import json
from decimal import Decimal
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.core.management import call_command
from django.views.decorators.http import require_POST
from django.utils import timezone

from gestion.models import (
    Proyecto, Etapa, Actividad, Subactividad, Recurso, TipoRecurso,
    AsignacionRecurso, Precedencia, Hito, SolicitudCambio, HistorialCambio, KPIConfig
)
from gestion.services.wbs_service import WBSService
from gestion.services.precedencias_service import PrecedenciasService
from gestion.services.recursos_service import RecursosService
from gestion.services.propagacion_service import PropagacionService
from gestion.services.kpi_service import KPIService
from gestion.services.auth_service import AuthService, requerir_director


def get_common_context(request, proyecto=None):
    """Contexto base común con perfil, proyectos disponibles y rol activo."""
    profile = AuthService.get_current_user_profile(request)
    todos_proyectos = Proyecto.objects.all()

    if not proyecto and todos_proyectos.exists():
        # Tomar el proyecto guardado en sesión o el primero
        pid = request.session.get('proyecto_activo_id')
        if pid:
            proyecto = todos_proyectos.filter(id=pid).first()
        if not proyecto:
            proyecto = todos_proyectos.first()

    return {
        'profile': profile,
        'proyecto_actual': proyecto,
        'todos_proyectos': todos_proyectos,
        'tiene_proyectos': todos_proyectos.exists(),
    }


def home_view(request):
    """Vista principal: muestra el Estado Vacío si no hay proyectos, o el resumen si hay."""
    context = get_common_context(request)
    if not context['tiene_proyectos']:
        return render(request, 'gestion/empty_state.html', context)
    return redirect('dashboard_proyecto', proyecto_id=context['proyecto_actual'].id)


def cambiar_proyecto_activo(request, proyecto_id):
    """Permite seleccionar qué proyecto visualizar en la barra superior."""
    get_object_or_404(Proyecto, id=proyecto_id)
    request.session['proyecto_activo_id'] = proyecto_id
    messages.info(request, "Proyecto activo actualizado.")
    next_url = request.META.get('HTTP_REFERER', '/')
    return redirect(next_url)


def toggle_dev_role(request):
    """Permite al evaluador conmutar entre Director y Miembro para probar el RBAC."""
    actual = request.session.get('dev_role', AuthService.ROLE_DIRECTOR)
    nuevo = AuthService.ROLE_MIEMBRO if actual == AuthService.ROLE_DIRECTOR else AuthService.ROLE_DIRECTOR
    request.session['dev_role'] = nuevo
    nombre_rol = 'Director de Proyecto' if nuevo == AuthService.ROLE_DIRECTOR else 'Miembro de Equipo'
    messages.success(request, f"Rol cambiado para la prueba a: {nombre_rol}")
    return redirect(request.META.get('HTTP_REFERER', '/'))


@require_POST
def cargar_caso_demo(request):
    """Carga el caso de prueba completo exigido para el 50% de la evaluación."""
    profile = AuthService.get_current_user_profile(request)
    if not profile['es_director']:
        messages.error(request, "Solo un Director de Proyecto puede inicializar el caso de prueba.")
        return redirect('home')

    try:
        call_command('seed_demo_data')
        proyecto = Proyecto.objects.filter(codigo='PRJ-2026-001').first()
        if proyecto:
            request.session['proyecto_activo_id'] = proyecto.id
        messages.success(request, "¡Caso de prueba cargado con éxito! Se poblaron 4 etapas, 12 actividades, 20 subactividades, dependencias, recursos y cambios.")
    except Exception as e:
        messages.error(request, f"Error al cargar caso demo: {str(e)}")

    return redirect('home')


@require_POST
@requerir_director
def crear_proyecto(request):
    """Crea un nuevo proyecto desde el estado vacío o la interfaz."""
    nombre = request.POST.get('nombre')
    codigo = request.POST.get('codigo')
    descripcion = request.POST.get('descripcion', '')
    fecha_inicio = request.POST.get('fecha_inicio')
    fecha_fin_plan = request.POST.get('fecha_fin_plan')
    presupuesto = request.POST.get('presupuesto_inicial', '0')

    try:
        nuevo = Proyecto.objects.create(
            nombre=nombre,
            codigo=codigo,
            descripcion=descripcion,
            fecha_inicio=fecha_inicio,
            fecha_fin_plan=fecha_fin_plan,
            presupuesto_inicial=Decimal(presupuesto),
            presupuesto_actual=Decimal(presupuesto),
            costo_acumulado=Decimal('0.00'),
            director_nombre=request.POST.get('director_nombre', 'Director de Proyecto')
        )
        request.session['proyecto_activo_id'] = nuevo.id
        messages.success(request, f"Proyecto {nuevo.codigo} creado exitosamente.")
        return redirect('wbs_view', proyecto_id=nuevo.id)
    except Exception as e:
        messages.error(request, f"Error al crear proyecto: {str(e)}")
        return redirect('home')


# ==========================================
# INDICADOR B: VISTA EDT / WBS
# ==========================================
def wbs_view(request, proyecto_id):
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)
    context = get_common_context(request, proyecto)
    context['wbs_data'] = WBSService.calcular_avance_arbol(proyecto)
    context['recursos'] = Recurso.objects.filter(disponible=True)
    context['todas_subactividades'] = Subactividad.objects.filter(actividad__etapa__proyecto=proyecto)
    return render(request, 'gestion/wbs.html', context)


@require_POST
@requerir_director
def agregar_etapa(request, proyecto_id):
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)
    codigo = request.POST.get('codigo')
    nombre = request.POST.get('nombre')
    peso = request.POST.get('peso_porcentual', '25.00')

    try:
        Etapa.objects.create(
            proyecto=proyecto,
            codigo=codigo,
            nombre=nombre,
            peso_porcentual=Decimal(peso)
        )
        messages.success(request, f"Etapa {codigo} agregada.")
    except Exception as e:
        messages.error(request, f"Error al agregar etapa: {str(e)}")
    return redirect('wbs_view', proyecto_id=proyecto.id)


@require_POST
@requerir_director
def agregar_actividad(request, etapa_id):
    etapa = get_object_or_404(Etapa, id=etapa_id)
    codigo = request.POST.get('codigo')
    nombre = request.POST.get('nombre')
    peso = request.POST.get('peso_porcentual', '33.33')

    try:
        Actividad.objects.create(
            etapa=etapa,
            codigo=codigo,
            nombre=nombre,
            peso_porcentual=Decimal(peso)
        )
        messages.success(request, f"Actividad {codigo} agregada.")
    except Exception as e:
        messages.error(request, f"Error al agregar actividad: {str(e)}")
    return redirect('wbs_view', proyecto_id=etapa.proyecto_id)


@require_POST
@requerir_director
def agregar_subactividad(request, actividad_id):
    actividad = get_object_or_404(Actividad, id=actividad_id)
    codigo = request.POST.get('codigo')
    nombre = request.POST.get('nombre')
    peso = request.POST.get('peso_porcentual', '50.00')
    duracion = int(request.POST.get('duracion_dias', 5))
    fecha_inicio = request.POST.get('fecha_inicio_plan')
    fecha_fin = request.POST.get('fecha_fin_plan')
    costo_fijo = request.POST.get('costo_fijo', '0.00')
    es_hito = request.POST.get('es_hito') == 'on'

    try:
        sub = Subactividad.objects.create(
            actividad=actividad,
            codigo=codigo,
            nombre=nombre,
            peso_porcentual=Decimal(peso),
            duracion_dias=duracion,
            fecha_inicio_plan=fecha_inicio,
            fecha_fin_plan=fecha_fin,
            costo_fijo=Decimal(costo_fijo),
            es_hito=es_hito
        )

        # Precedencia opcional directa desde el modal
        predecesora_id = request.POST.get('predecesora_id')
        if predecesora_id:
            tipo_enlace = request.POST.get('tipo_enlace', 'FS')
            lag = int(request.POST.get('lag_dias', 0))
            if not PrecedenciasService.validar_dependencia_circular(int(predecesora_id), sub.id):
                Precedencia.objects.create(
                    tarea_origen_id=predecesora_id,
                    tarea_destino=sub,
                    tipo=tipo_enlace,
                    lag_dias=lag
                )
            else:
                messages.warning(request, "Se omitió la dependencia por riesgo de ciclo circular.")

        # Asignación de recurso opcional
        recurso_id = request.POST.get('recurso_id')
        if recurso_id:
            horas = request.POST.get('horas_asignadas', '40.0')
            AsignacionRecurso.objects.create(
                subactividad=sub,
                recurso_id=recurso_id,
                horas_asignadas=Decimal(horas),
                fecha_inicio=sub.fecha_inicio_plan,
                fecha_fin=sub.fecha_fin_plan
            )

        messages.success(request, f"Subactividad {codigo} creada exitosamente.")
    except Exception as e:
        messages.error(request, f"Error al crear subactividad: {str(e)}")

    return redirect('wbs_view', proyecto_id=actividad.etapa.proyecto_id)


# ==========================================
# INDICADOR C: RECURSOS Y SOBREASIGNACIÓN
# ==========================================
def recursos_view(request, proyecto_id):
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)
    context = get_common_context(request, proyecto)
    context['alertas_sobreasignacion'] = RecursosService.detectar_sobreasignaciones(proyecto)
    context['resumen_recursos'] = RecursosService.resumen_costos_recursos(proyecto)
    context['todos_recursos'] = Recurso.objects.select_related('tipo').all()
    context['asignaciones'] = AsignacionRecurso.objects.filter(subactividad__actividad__etapa__proyecto=proyecto).select_related('recurso', 'subactividad')
    return render(request, 'gestion/recursos.html', context)


# ==========================================
# INDICADOR D: CARTA GANTT Y PRECEDENCIAS
# ==========================================
def gantt_view(request, proyecto_id):
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)
    context = get_common_context(request, proyecto)

    subactividades = Subactividad.objects.filter(
        actividad__etapa__proyecto=proyecto
    ).select_related('actividad__etapa')

    precedencias = Precedencia.objects.filter(
        tarea_origen__actividad__etapa__proyecto=proyecto
    ).select_related('tarea_origen', 'tarea_destino')

    # Preparar datos JSON para Frappe Gantt
    tasks_json = []
    for sub in subactividades:
        deps = [p.tarea_origen.codigo for p in sub.precedencias_entrantes.all()]
        tasks_json.append({
            'id': sub.codigo,
            'name': f"{sub.codigo} {sub.nombre}",
            'start': sub.fecha_inicio_plan.strftime('%Y-%m-%d'),
            'end': sub.fecha_fin_plan.strftime('%Y-%m-%d'),
            'progress': float(sub.porcentaje_avance),
            'dependencies': ", ".join(deps),
            'custom_class': 'bar-milestone' if sub.es_hito else ('bar-late' if sub.esta_atrasada else 'bar-normal')
        })

    context['tasks_json'] = json.dumps(tasks_json)
    context['subactividades'] = subactividades
    context['precedencias'] = precedencias
    context['hitos'] = Hito.objects.filter(proyecto=proyecto)
    return render(request, 'gestion/gantt.html', context)


@require_POST
@requerir_director
def actualizar_duracion_tarea(request, subactividad_id):
    """
    Simulación en vivo para la Demo (50%):
    Al modificar la duración de una tarea, se recalculan en cascada las fechas de las dependencias.
    """
    sub = get_object_or_404(Subactividad, id=subactividad_id)
    dias = int(request.POST.get('duracion_dias', sub.duracion_dias))
    sub.duracion_dias = dias
    sub.fecha_fin_plan = sub.fecha_inicio_plan + timezone.timedelta(days=max(0, dias - 1))
    sub.save(update_fields=['duracion_dias', 'fecha_fin_plan'])

    afectadas = PrecedenciasService.recalcular_en_cascada(sub)
    messages.success(request, f"Duración de {sub.codigo} actualizada a {dias} días. Se recalcularon {afectadas} tareas dependientes en cascada.")
    return redirect('gantt_view', proyecto_id=sub.actividad.etapa.proyecto_id)


# ==========================================
# INDICADOR E & G: TABLERO 1 (OPERATIVO PROYECTO)
# ==========================================
def dashboard_proyecto_view(request, proyecto_id):
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)
    context = get_common_context(request, proyecto)

    kpis_todos = KPIService.calcular_kpis_proyecto(proyecto)
    context['kpis_proyecto'] = [k for k in kpis_todos if k['tipo'] == 'PROYECTO']
    context['hitos'] = Hito.objects.filter(proyecto=proyecto)
    context['alertas_sobreasignacion'] = RecursosService.detectar_sobreasignaciones(proyecto)
    context['total_tareas'] = Subactividad.objects.filter(actividad__etapa__proyecto=proyecto).count()
    context['total_atrasadas'] = sum(1 for s in Subactividad.objects.filter(actividad__etapa__proyecto=proyecto) if s.esta_atrasada)
    return render(request, 'gestion/dashboard_proyecto.html', context)


# ==========================================
# INDICADOR F & G: TABLERO 2 (GESTIÓN DEL CAMBIO)
# ==========================================
def dashboard_cambio_view(request, proyecto_id):
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)
    context = get_common_context(request, proyecto)

    kpis_todos = KPIService.calcular_kpis_proyecto(proyecto)
    context['kpis_cambio'] = [k for k in kpis_todos if k['tipo'] == 'CAMBIO']
    context['solicitudes'] = SolicitudCambio.objects.filter(proyecto=proyecto).select_related('subactividad_afectada')
    context['etapas_10'] = SolicitudCambio.ETAPAS_10

    solicitudes = context['solicitudes']
    context['total_solicitudes'] = solicitudes.count()
    context['total_aprobadas'] = solicitudes.filter(estado__in=['APROBADA', 'EN_PLANIFICACION', 'EN_EJECUCION', 'EN_VERIFICACION', 'CERRADA_ADOPCION']).count()
    context['total_en_evaluacion'] = solicitudes.filter(estado__in=['REGISTRADA', 'EN_EVALUACION', 'EN_COMITE']).count()
    context['total_rechazadas'] = solicitudes.filter(estado='RECHAZADA').count()

    return render(request, 'gestion/dashboard_cambio.html', context)


# ==========================================
# INDICADOR F: GESTIÓN DEL CAMBIO (10 ETAPAS Y PROPAGACIÓN)
# ==========================================
def cambios_list_view(request, proyecto_id):
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)
    context = get_common_context(request, proyecto)
    context['solicitudes'] = SolicitudCambio.objects.filter(proyecto=proyecto).select_related('subactividad_afectada')
    context['subactividades'] = Subactividad.objects.filter(actividad__etapa__proyecto=proyecto)
    return render(request, 'gestion/cambios_list.html', context)


@require_POST
def registrar_solicitud_cambio(request, proyecto_id):
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)
    profile = AuthService.get_current_user_profile(request)

    codigo = request.POST.get('codigo')
    titulo = request.POST.get('titulo')
    descripcion = request.POST.get('descripcion')
    justificacion = request.POST.get('justificacion')
    solicitante = request.POST.get('solicitante', profile['nombre'])
    prioridad = request.POST.get('prioridad', 'MEDIA')
    impacto_dias = int(request.POST.get('impacto_plazo_dias', 0))
    impacto_costo = Decimal(request.POST.get('impacto_costo', '0.00'))
    sub_id = request.POST.get('subactividad_afectada_id')

    try:
        sol = SolicitudCambio.objects.create(
            proyecto=proyecto,
            codigo=codigo,
            titulo=titulo,
            descripcion=descripcion,
            justificacion=justificacion,
            solicitante=solicitante,
            prioridad=prioridad,
            impacto_plazo_dias=impacto_dias,
            impacto_costo=impacto_costo,
            subactividad_afectada_id=sub_id if sub_id else None,
            etapa_actual=1,
            estado='REGISTRADA'
        )
        HistorialCambio.objects.create(
            solicitud=sol,
            etapa=1,
            usuario=profile['nombre'],
            comentario="Registro formal de la Solicitud de Cambio (RFC)."
        )
        messages.success(request, f"Solicitud {codigo} ingresada en Etapa 1.")
    except Exception as e:
        messages.error(request, f"Error al registrar solicitud: {str(e)}")

    return redirect('cambios_list', proyecto_id=proyecto.id)


@require_POST
@requerir_director
def avanzar_etapa_cambio(request, solicitud_id):
    """
    Avanza la solicitud en el flujo de 10 etapas.
    Si se aprueba o llega a etapa 8, se propaga el impacto a la Carta Gantt y presupuesto.
    """
    solicitud = get_object_or_404(SolicitudCambio, id=solicitud_id)
    profile = AuthService.get_current_user_profile(request)
    nueva_etapa = int(request.POST.get('nueva_etapa', solicitud.etapa_actual + 1))
    comentario = request.POST.get('comentario', '')

    if nueva_etapa > 10:
        nueva_etapa = 10

    solicitud = PropagacionService.avanzar_etapa(
        solicitud, nueva_etapa, usuario=profile['nombre'], comentario=comentario
    )

    if solicitud.etapa_actual == 8 and not solicitud.propagado:
        exito, msgs = PropagacionService.propagar_impacto(solicitud, usuario=profile['nombre'])
        if exito:
            messages.success(request, f"¡Propagación automática ejecutada! Impacto aplicado al Gantt y Presupuesto: {'; '.join(msgs)}")
        else:
            messages.info(request, msgs)
    else:
        messages.success(request, f"Solicitud {solicitud.codigo} avanzada a etapa: {solicitud.get_etapa_actual_display()}.")

    return redirect('cambios_list', proyecto_id=solicitud.proyecto_id)


@require_POST
@requerir_director
def propagar_cambio_directo(request, solicitud_id):
    """Permite disparar manualmente la propagación en vivo para demostración."""
    solicitud = get_object_or_404(SolicitudCambio, id=solicitud_id)
    profile = AuthService.get_current_user_profile(request)
    exito, msgs = PropagacionService.propagar_impacto(solicitud, usuario=profile['nombre'])
    if exito:
        messages.success(request, f"Propagación exitosa en vivo: {'; '.join(msgs)}")
    else:
        messages.warning(request, f"Resultado: {msgs}")
    return redirect('cambios_list', proyecto_id=solicitud.proyecto_id)
