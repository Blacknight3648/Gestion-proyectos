from django.conf import settings
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


class AuthService:
    ROLE_DIRECTOR = 'DIRECTOR'
    ROLE_MIEMBRO = 'MIEMBRO'

    @classmethod
    def get_current_user_profile(cls, request):
        """
        Obtiene los datos del usuario autenticado (desde Okta o sesión local).
        Retorna diccionario con: {autenticado, nombre, email, rol, rol_display, es_director, proveedor}.
        """
        session_user = request.session.get('user')

        if not session_user:
            return {
                'autenticado': False,
                'nombre': 'Invitado',
                'email': '',
                'rol': 'INVITADO',
                'rol_display': 'Invitado',
                'es_director': False,
                'proveedor': 'Ninguno'
            }

        userinfo = session_user.get('userinfo', {})
        nombre = userinfo.get('name') or session_user.get('name', 'Usuario')
        email = userinfo.get('email') or session_user.get('email', '')

        # Si el usuario cambió de rol en vivo con el botón del navbar:
        dev_role = request.session.get('dev_role')

        if dev_role:
            rol_clave = dev_role
            es_director = (rol_clave == cls.ROLE_DIRECTOR)
        else:
            # Extracción de roles desde tokens de Okta / Auth0 o sesión
            roles = (
                userinfo.get('https://okta.com/roles') or
                userinfo.get('https://gestionproyectos.com/roles') or
                userinfo.get('roles') or
                userinfo.get('groups') or
                session_user.get('roles') or
                []
            )
            if isinstance(roles, str):
                roles = [roles]

            direct_role = session_user.get('role')
            if direct_role:
                roles.append(direct_role)

            es_director = any('director' in str(r).lower() or 'admin' in str(r).lower() for r in roles)
            rol_clave = cls.ROLE_DIRECTOR if es_director else cls.ROLE_MIEMBRO

        return {
            'autenticado': True,
            'nombre': nombre,
            'email': email,
            'rol': rol_clave,
            'rol_display': 'Director de Proyecto' if rol_clave == cls.ROLE_DIRECTOR else 'Miembro de Equipo',
            'es_director': es_director,
            'proveedor': session_user.get('provider', 'Okta SSO')
        }


def requerir_director(view_func):
    """Decorador para proteger vistas que requieren privilegios de Director/Admin."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        profile = AuthService.get_current_user_profile(request)
        if not profile['autenticado']:
            messages.warning(request, "Debe iniciar sesión para acceder.")
            return redirect('login')
        if not profile['es_director']:
            messages.error(request, "Acceso denegado: Esta acción requiere el rol de Director de Proyecto.")
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper
