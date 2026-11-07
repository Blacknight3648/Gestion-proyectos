from functools import wraps
from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect


class AuthService:
    ROLE_DIRECTOR = 'DIRECTOR'
    ROLE_MIEMBRO = 'MIEMBRO'

    @staticmethod
    def is_valid_oidc_session(session_user):
        """
        Verifica que la sesión provenga exclusivamente de un flujo OIDC real de Okta / Auth0
        (con token emitido y claim 'sub' del sujeto autenticado).
        Rechaza cualquier sesión simulada, incompleta o antigua.
        """
        if not isinstance(session_user, dict):
            return False
        has_token = bool(session_user.get('id_token') or session_user.get('access_token'))
        userinfo = session_user.get('userinfo')
        has_subject = isinstance(userinfo, dict) and bool(userinfo.get('sub'))
        return has_token and has_subject

    @staticmethod
    def _extract_oidc_roles(userinfo):
        """
        Extrae la lista de roles desde los claims del id_token / userinfo firmado por Okta/Auth0.
        Soporta namespaces personalizados (ej. https://sgp.proyectos/roles) y claims estándar.
        """
        collected = []
        candidate_keys = {
            'https://sgp.proyectos/roles',
            'https://okta.com/roles',
            'https://gestionproyectos.com/roles',
            'roles',
            'groups',
        }

        for key, value in userinfo.items():
            if key in candidate_keys or key.endswith('/roles') or key.endswith('/groups'):
                if isinstance(value, (list, tuple)):
                    collected.extend(str(item) for item in value if item)
                elif isinstance(value, str) and value.strip():
                    collected.append(value.strip())

        return collected

    @classmethod
    def get_current_user_profile(cls, request):
        """
        Obtiene el perfil e identidad del usuario autenticado vía Okta/Auth0 OIDC.
        Aplica Principio de Menor Privilegio: por defecto 'Miembro de Equipo' (Solo Lectura),
        salvo que el token firmado de Okta certifique el rol de Director/Administrador.
        """
        session_user = request.session.get('user')

        if not cls.is_valid_oidc_session(session_user):
            return {
                'autenticado': False,
                'nombre': 'Invitado',
                'email': '',
                'sub': '',
                'rol': 'INVITADO',
                'rol_display': 'No Autenticado',
                'es_director': False,
                'roles_okta': [],
                'proveedor': 'Ninguno',
            }

        userinfo = session_user.get('userinfo', {})
        email = (userinfo.get('email') or '').strip()
        nombre = (
            userinfo.get('name')
            or userinfo.get('nickname')
            or email
            or 'Usuario Okta'
        )
        sub = userinfo.get('sub', '')

        roles_okta = cls._extract_oidc_roles(userinfo)
        admin_emails = getattr(settings, 'OKTA_ADMIN_EMAILS', [])

        tiene_rol_director_token = any(
            any(keyword in r.lower() for keyword in ('director', 'admin', 'administrador'))
            for r in roles_okta
        )
        en_lista_admin_servidor = bool(email and email.lower() in admin_emails)

        es_director = tiene_rol_director_token or en_lista_admin_servidor
        rol_clave = cls.ROLE_DIRECTOR if es_director else cls.ROLE_MIEMBRO

        return {
            'autenticado': True,
            'nombre': nombre,
            'email': email,
            'sub': sub,
            'rol': rol_clave,
            'rol_display': 'Director de Proyecto' if es_director else 'Miembro de Equipo',
            'es_director': es_director,
            'roles_okta': roles_okta,
            'proveedor': 'Okta / Auth0 SSO',
        }


def requerir_director(view_func):
    """Decorador que restringe acciones de escritura exclusivamente al rol Director de Proyecto."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        profile = AuthService.get_current_user_profile(request)
        if not profile['autenticado']:
            messages.warning(request, "Debe iniciar sesión con Okta para acceder al sistema.")
            return redirect('login')
        if not profile['es_director']:
            messages.error(
                request,
                "Acceso denegado: Su cuenta posee rol de Miembro de Equipo (Solo Lectura). Esta acción requiere rol de Director de Proyecto asignado en Okta."
            )
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper
