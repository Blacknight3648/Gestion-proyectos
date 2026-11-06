from django.shortcuts import redirect


class OktaAuthRequiredMiddleware:
    """
    Middleware que garantiza que ningún usuario acceda al sistema sin autenticarse.
    Si no existe sesión activa, redirige automáticamente a la pantalla de Login.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        rutas_libres = [
            '/login/',
            '/login/sso/',
            '/login/manual/',
            '/callback/',
            '/static/',
        ]

        # Permitir rutas públicas de autenticación y estáticos
        if any(request.path.startswith(r) for r in rutas_libres):
            return self.get_response(request)

        # Si no hay sesión de usuario activa en request.session, forzar inicio de sesión
        if not request.session.get('user'):
            return redirect('login')

        return self.get_response(request)

