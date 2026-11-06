from django.urls import path, include
from . import views

urlpatterns = [
    # Rutas de Autenticación
    path("login/", views.login_page, name="login"),
    path("login/sso/", views.login, name="login_sso"),
    path("login/manual/", views.login_manual, name="login_manual"),
    path("logout/", views.logout, name="logout"),
    path("callback/", views.callback, name="callback"),

    # Sistema de Gestión de Proyectos
    path("", include("gestion.urls")),
]
