from django.urls import path
from gestion import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('cambiar-proyecto/<int:proyecto_id>/', views.cambiar_proyecto_activo, name='cambiar_proyecto_activo'),
    path('cargar-caso-demo/', views.cargar_caso_demo, name='cargar_caso_demo'),
    path('crear-proyecto/', views.crear_proyecto, name='crear_proyecto'),

    # WBS / EDT
    path('proyecto/<int:proyecto_id>/wbs/', views.wbs_view, name='wbs_view'),
    path('proyecto/<int:proyecto_id>/etapa/agregar/', views.agregar_etapa, name='agregar_etapa'),
    path('etapa/<int:etapa_id>/actividad/agregar/', views.agregar_actividad, name='agregar_actividad'),
    path('actividad/<int:actividad_id>/subactividad/agregar/', views.agregar_subactividad, name='agregar_subactividad'),

    # Recursos
    path('proyecto/<int:proyecto_id>/recursos/', views.recursos_view, name='recursos_view'),

    # Gantt
    path('proyecto/<int:proyecto_id>/gantt/', views.gantt_view, name='gantt_view'),
    path('subactividad/<int:subactividad_id>/actualizar-duracion/', views.actualizar_duracion_tarea, name='actualizar_duracion_tarea'),

    # Tableros Duales
    path('proyecto/<int:proyecto_id>/tablero-operativo/', views.dashboard_proyecto_view, name='dashboard_proyecto'),
    path('proyecto/<int:proyecto_id>/tablero-cambio/', views.dashboard_cambio_view, name='dashboard_cambio'),

    # Gestión del Cambio
    path('proyecto/<int:proyecto_id>/cambios/', views.cambios_list_view, name='cambios_list'),
    path('proyecto/<int:proyecto_id>/cambio/registrar/', views.registrar_solicitud_cambio, name='registrar_solicitud_cambio'),
    path('cambio/<int:solicitud_id>/avanzar/', views.avanzar_etapa_cambio, name='avanzar_etapa_cambio'),
    path('cambio/<int:solicitud_id>/propagar/', views.propagar_cambio_directo, name='propagar_cambio_directo'),
]

