import logging
from urllib.parse import quote_plus, urlencode

from authlib.integrations.django_client import OAuth
from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse

from gestion.services.auth_service import AuthService

logger = logging.getLogger(__name__)


def _is_okta_configured():
    domain = getattr(settings, 'AUTH0_DOMAIN', '') or ''
    client_id = getattr(settings, 'AUTH0_CLIENT_ID', '') or ''
    client_secret = getattr(settings, 'AUTH0_CLIENT_SECRET', '') or ''
    if not domain or not client_id or not client_secret:
        return False
    if any('{' in val for val in (domain, client_id, client_secret)):
        return False
    return True


oauth = OAuth()
if _is_okta_configured():
    oauth.register(
        "auth0",
        client_id=settings.AUTH0_CLIENT_ID,
        client_secret=settings.AUTH0_CLIENT_SECRET,
        client_kwargs={
            "scope": "openid profile email",
        },
        server_metadata_url=f"https://{settings.AUTH0_DOMAIN}/.well-known/openid-configuration",
    )


def login_page(request):
    """Pantalla de Inicio de Sesión exclusiva vía Okta / Auth0 SSO."""
    session_user = request.session.get('user')
    if AuthService.is_valid_oidc_session(session_user):
        return redirect('home')

    # Limpiar cualquier sesión residual o inválida si existiera
    if session_user is not None or 'dev_role' in request.session:
        request.session.flush()

    return render(request, "gestion/login.html", {
        "okta_configurado": _is_okta_configured(),
        "auth0_domain": getattr(settings, 'AUTH0_DOMAIN', ''),
    })


def login(request):
    """Redirige al usuario al Universal Login de Okta / Auth0 (OIDC)."""
    if not _is_okta_configured():
        messages.error(
            request,
            "Configuración incompleta: Verifique AUTH0_DOMAIN, AUTH0_CLIENT_ID y AUTH0_CLIENT_SECRET en el archivo .env."
        )
        return redirect('login')

    try:
        callback_uri = request.build_absolute_uri(reverse("callback"))
        return oauth.auth0.authorize_redirect(request, callback_uri)
    except Exception as e:
        logger.exception("Fallo al iniciar redirección OIDC hacia Okta/Auth0")
        messages.error(
            request,
            f"No fue posible conectar con el proveedor de identidad Okta ({settings.AUTH0_DOMAIN}): {str(e)}"
        )
        return redirect('login')


def callback(request):
    """Procesa el retorno desde Okta / Auth0, verifica el id_token y extrae el rol."""
    if request.GET.get("error"):
        err_code = request.GET.get("error")
        err_desc = request.GET.get("error_description", "Autenticación rechazada por el proveedor.")
        messages.error(request, f"Okta rechazó el inicio de sesión ({err_code}): {err_desc}")
        return redirect('login')

    try:
        token = oauth.auth0.authorize_access_token(request)
        if isinstance(token, dict) and not token.get("userinfo"):
            token["userinfo"] = oauth.auth0.userinfo(token=token)

        if not AuthService.is_valid_oidc_session(token):
            messages.error(request, "El token retornado por Okta no contiene información de identidad OIDC válida.")
            return redirect('login')

        request.session["user"] = token
        profile = AuthService.get_current_user_profile(request)
        messages.success(
            request,
            f"Sesión iniciada vía Okta SSO: {profile['nombre']} ({profile['rol_display']})."
        )
        return redirect('home')
    except Exception as e:
        logger.exception("Error validando callback OIDC de Okta/Auth0")
        messages.error(request, f"Error al validar el token con Okta: {str(e)}")
        return redirect('login')


def logout(request):
    """Destruye la sesión local en Django y cierra la sesión SSO en Okta / Auth0."""
    request.session.flush()

    if _is_okta_configured():
        # Usa la raíz canónica (ej. http://localhost:3000) compatible con Allowed Logout URLs de Auth0;
        # al regresar a '/', el middleware redirige limpiamente a '/login/'.
        return_to = request.build_absolute_uri("/").rstrip("/")
        return redirect(
            f"https://{settings.AUTH0_DOMAIN}/v2/logout?"
            + urlencode(
                {
                    "returnTo": return_to,
                    "client_id": settings.AUTH0_CLIENT_ID,
                },
                quote_via=quote_plus,
            )
        )

    messages.info(request, "Sesión cerrada correctamente.")
    return redirect('login')
