from django.conf import settings
from django.shortcuts import redirect
from gestion.services.auth_service import AuthService


class OktaAuthRequiredMiddleware:
    """
    Middleware de seguridad que:
    1. En desarrollo local, normaliza 127.0.0.1 -> localhost para garantizar
       coincidencia exacta con las URIs autorizadas de Okta/Auth0 y la cookie OAuth state.
    2. Exige una sesión OIDC real emitida por Okta/Auth0 en toda ruta protegida,
       purgando cualquier sesión residual o simulada.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1. Normalizar 127.0.0.1 -> localhost en entorno local para evitar mismatch en Auth0
        if getattr(settings, 'DEBUG', False) and request.method in ('GET', 'HEAD'):
            host = request.get_host()
            if host.startswith('127.0.0.1'):
                port_part = host.split(':', 1)[1] if ':' in host else ''
                target_host = f"localhost:{port_part}" if port_part else "localhost"
                scheme = 'https' if request.is_secure() else 'http'
                return redirect(f"{scheme}://{target_host}{request.get_full_path()}")

        # 2. Rutas públicas del flujo OIDC y archivos estáticos
        path = request.path
        rutas_publicas = (
            '/login/',
            '/login/sso/',
            '/logout/',
            '/callback',
            '/static/',
        )
        if any(path == r or path.startswith(r) for r in rutas_publicas):
            return self.get_response(request)

        # 3. Validar sesión OIDC real emitida por Okta/Auth0
        session_user = request.session.get('user')
        if not AuthService.is_valid_oidc_session(session_user):
            if session_user is not None or 'dev_role' in request.session:
                request.session.flush()
            return redirect('login')

        return self.get_response(request)
