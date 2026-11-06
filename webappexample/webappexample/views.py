import json
import logging
from urllib.parse import quote_plus, urlencode

from authlib.integrations.django_client import OAuth
from django.conf import settings
from django.shortcuts import redirect, render
from django.urls import reverse
from django.contrib import messages
from django.views.decorators.http import require_POST

logger = logging.getLogger(__name__)

oauth = OAuth()
okta_valido = bool(getattr(settings, 'AUTH0_DOMAIN', None) and '{' not in settings.AUTH0_DOMAIN)

if okta_valido:
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
    """Pantalla de Login oficial ajustada al Mockup."""
    # Si ya tiene sesión iniciada, redirigir a inicio
    if request.session.get('user'):
        return redirect('home')

    return render(request, "gestion/login.html", {
        "okta_configurado": okta_valido,
        "auth0_domain": getattr(settings, 'AUTH0_DOMAIN', ''),
    })


def login(request):
    """Inicia el flujo SSO de Okta / Auth0."""
    if not okta_valido:
        messages.error(
            request,
            "Okta no está conectado: Por favor ingresa tu AUTH0_DOMAIN, AUTH0_CLIENT_ID y AUTH0_CLIENT_SECRET reales en el archivo .env. Mientras tanto, puedes iniciar sesión con tu usuario en el formulario inferior."
        )
        return redirect('login')

    try:
        return oauth.auth0.authorize_redirect(
            request, request.build_absolute_uri(reverse("callback"))
        )
    except Exception as e:
        messages.error(request, f"Error al conectar con Okta SSO: {str(e)}")
        return redirect('login')


@require_POST
def login_manual(request):
    """Permite al usuario ingresar con sus credenciales y seleccionar su rol."""
    email = request.POST.get('email', '').strip()
    nombre = request.POST.get('nombre', '').strip() or email.split('@')[0]
    password = request.POST.get('password', '')
    role = request.POST.get('role', 'DIRECTOR')

    if not email or not password:
        messages.error(request, "Debes ingresar tu usuario/email y contraseña.")
        return redirect('login')

    # Almacenar sesión de usuario
    request.session['user'] = {
        'name': nombre,
        'email': email,
        'role': role,
        'provider': 'Autenticación Local (RBAC Simulado)'
    }
    request.session['dev_role'] = role

    rol_nombre = 'Director de Proyecto' if role == 'DIRECTOR' else 'Miembro de Equipo'
    messages.success(request, f"¡Bienvenido, {nombre}! Has iniciado sesión como: {rol_nombre}.")
    return redirect('home')


def callback(request):
    try:
        token = oauth.auth0.authorize_access_token(request)
        request.session["user"] = token
        messages.success(request, "¡Sesión iniciada exitosamente vía Okta SSO!")
    except Exception as e:
        messages.error(request, f"Error durante la autenticación con Okta: {str(e)}")
    return redirect('home')


def logout(request):
    request.session.flush()
    messages.info(request, "Sesión cerrada correctamente.")

    if okta_valido:
        try:
            return redirect(
                f"https://{settings.AUTH0_DOMAIN}/v2/logout?"
                + urlencode(
                    {
                        "returnTo": request.build_absolute_uri(reverse("login")),
                        "client_id": settings.AUTH0_CLIENT_ID,
                    },
                    quote_via=quote_plus,
                ),
            )
        except Exception:
            pass

    return redirect('login')
