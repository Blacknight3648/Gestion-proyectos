from django.urls import path, include
from . import views

urlpatterns = [
    # Rutas exclusivas de Autenticación OIDC con Okta / Auth0
    path("login/", views.login_page, name="login"),
    path("login/sso/", views.login, name="login_sso"),
    path("logout/", views.logout, name="logout"),
    path("callback", views.callback, name="callback"),
    path("callback/", views.callback, name="callback_slash"),

    # Sistema de Gestión de Proyectos
    path("", include("gestion.urls")),
]
