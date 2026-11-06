from datetime import timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from gestion.models import (
    Proyecto, Etapa, Actividad, Subactividad, TipoRecurso, Recurso,
    AsignacionRecurso, Precedencia, Hito, SolicitudCambio, HistorialCambio
)
from gestion.services.kpi_service import KPIService
from gestion.services.precedencias_service import PrecedenciasService


class Command(BaseCommand):
    help = 'Carga el caso de prueba completo y verificado según la Rúbrica de Evaluación (Indicador H - 50%)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Iniciando carga de datos del caso de prueba para la Demo (50%)..."))

        # 1. Asegurar KPIs
        KPIService.asegurar_kpis_configurados()

        # 2. Tipos de Recursos (4 Tipos exigidos)
        t_humano, _ = TipoRecurso.objects.get_or_create(nombre='Recurso Humano', defaults={'unidad_medida': 'Horas'})
        t_material, _ = TipoRecurso.objects.get_or_create(nombre='Material', defaults={'unidad_medida': 'Unidades'})
        t_equipo, _ = TipoRecurso.objects.get_or_create(nombre='Equipamiento', defaults={'unidad_medida': 'Días/Renta'})
        t_licencia, _ = TipoRecurso.objects.get_or_create(nombre='Licencia de Software', defaults={'unidad_medida': 'Suscripción'})

        # 3. Profesionales / Recursos (5 Profesionales exigidos con tarifas)
        p1, _ = Recurso.objects.get_or_create(
            nombre='Ing. Carlos Mendoza',
            defaults={'tipo': t_humano, 'cargo_o_detalle': 'Líder Técnico & Arquitecto', 'tarifa_por_hora': Decimal('45.00'), 'jornada_diaria_horas': Decimal('8.0')}
        )
        p2, _ = Recurso.objects.get_or_create(
            nombre='Lic. Sofía Valenzuela',
            defaults={'tipo': t_humano, 'cargo_o_detalle': 'Especialista en Gestión del Cambio', 'tarifa_por_hora': Decimal('38.00'), 'jornada_diaria_horas': Decimal('8.0')}
        )
        p3, _ = Recurso.objects.get_or_create(
            nombre='Ing. Matías Herrera',
            defaults={'tipo': t_humano, 'cargo_o_detalle': 'Desarrollador Backend Senior', 'tarifa_por_hora': Decimal('35.00'), 'jornada_diaria_horas': Decimal('8.0')}
        )
        p4, _ = Recurso.objects.get_or_create(
            nombre='Diseñadora Elena Morales',
            defaults={'tipo': t_humano, 'cargo_o_detalle': 'Diseñadora UX/UI', 'tarifa_por_hora': Decimal('30.00'), 'jornada_diaria_horas': Decimal('8.0')}
        )
        p5, _ = Recurso.objects.get_or_create(
            nombre='Ing. Felipe Rojas',
            defaults={'tipo': t_humano, 'cargo_o_detalle': 'Especialista QA & Automatización', 'tarifa_por_hora': Decimal('32.00'), 'jornada_diaria_horas': Decimal('8.0')}
        )

        r_servidor, _ = Recurso.objects.get_or_create(
            nombre='Servidor Cloud AWS Staging',
            defaults={'tipo': t_equipo, 'cargo_o_detalle': 'Instancia EC2 r5.large', 'tarifa_por_hora': Decimal('15.00'), 'jornada_diaria_horas': Decimal('24.0')}
        )
        r_licencia, _ = Recurso.objects.get_or_create(
            nombre='Suscripción Okta Enterprise SSO',
            defaults={'tipo': t_licencia, 'cargo_o_detalle': 'Licencia Corporativa Identity Cloud', 'tarifa_por_hora': Decimal('5.00'), 'jornada_diaria_horas': Decimal('24.0')}
        )

        # 4. Proyecto Base
        hoy = timezone.now().date()
        fecha_ini = hoy - timedelta(days=20)
        fecha_fin = hoy + timedelta(days=70)

        proyecto, created = Proyecto.objects.get_or_create(
            codigo='PRJ-2026-001',
            defaults={
                'nombre': 'Modernización Integral del Sistema de Gestión y Autenticación Corporativa',
                'descripcion': 'Proyecto de modernización con arquitectura desacoplada, gestión EDT/WBS, integración Okta SSO, Carta Gantt con recálculo dinámico y módulo de gestión del cambio de 10 etapas.',
                'director_nombre': 'Director de Proyecto (Okta RBAC)',
                'fecha_inicio': fecha_ini,
                'fecha_fin_plan': fecha_fin,
                'presupuesto_inicial': Decimal('48000.00'),
                'presupuesto_actual': Decimal('48000.00'),
                'costo_acumulado': Decimal('19200.00'),
                'estado': 'EN_EJECUCION',
            }
        )

        if not created:
            self.stdout.write(self.style.WARNING("El proyecto PRJ-2026-001 ya existe. Se mantendrá el existente."))
            return

        # 5. Las 4 Etapas (Regla del 100%: 25% cada una)
        e1 = Etapa.objects.create(proyecto=proyecto, codigo='1.0', nombre='Iniciación y Diseño de Arquitectura', peso_porcentual=Decimal('25.00'), orden=1)
        e2 = Etapa.objects.create(proyecto=proyecto, codigo='2.0', nombre='Desarrollo del Núcleo y Autenticación Okta', peso_porcentual=Decimal('25.00'), orden=2)
        e3 = Etapa.objects.create(proyecto=proyecto, codigo='3.0', nombre='Gestión del Cambio y Despliegue de Motores', peso_porcentual=Decimal('25.00'), orden=3)
        e4 = Etapa.objects.create(proyecto=proyecto, codigo='4.0', nombre='Cierre, Auditoría y Transición Cultural', peso_porcentual=Decimal('25.00'), orden=4)

        # 6. Las 12 Actividades (3 por cada Etapa - Regla 100%: 33.33%, 33.33%, 33.34%)
        # Etapa 1.0
        a11 = Actividad.objects.create(etapa=e1, codigo='1.1', nombre='Levantamiento y Gobernanza', peso_porcentual=Decimal('33.33'), orden=1)
        a12 = Actividad.objects.create(etapa=e1, codigo='1.2', nombre='Arquitectura de Datos y Mockups', peso_porcentual=Decimal('33.33'), orden=2)
        a13 = Actividad.objects.create(etapa=e1, codigo='1.3', nombre='Aprobación del Plan Base', peso_porcentual=Decimal('33.34'), orden=3)

        # Etapa 2.0
        a21 = Actividad.objects.create(etapa=e2, codigo='2.1', nombre='Integración del SSO Okta', peso_porcentual=Decimal('33.33'), orden=1)
        a22 = Actividad.objects.create(etapa=e2, codigo='2.2', nombre='Motor de Precedencias y Carta Gantt', peso_porcentual=Decimal('33.33'), orden=2)
        a23 = Actividad.objects.create(etapa=e2, codigo='2.3', nombre='Módulo de Recursos y Costos', peso_porcentual=Decimal('33.34'), orden=3)

        # Etapa 3.0
        a31 = Actividad.objects.create(etapa=e3, codigo='3.1', nombre='Motor Configurable de KPIs', peso_porcentual=Decimal('33.33'), orden=1)
        a32 = Actividad.objects.create(etapa=e3, codigo='3.2', nombre='Flujo de Gestión del Cambio (10 Etapas)', peso_porcentual=Decimal('33.33'), orden=2)
        a33 = Actividad.objects.create(etapa=e3, codigo='3.3', nombre='Tableros de Control Duales', peso_porcentual=Decimal('33.34'), orden=3)

        # Etapa 4.0
        a41 = Actividad.objects.create(etapa=e4, codigo='4.1', nombre='Pruebas Integrales y Casos de Uso', peso_porcentual=Decimal('33.33'), orden=1)
        a42 = Actividad.objects.create(etapa=e4, codigo='4.2', nombre='Plan de Adopción Cultural', peso_porcentual=Decimal('33.33'), orden=2)
        a43 = Actividad.objects.create(etapa=e4, codigo='4.3', nombre='Entrega y Cierre Formal', peso_porcentual=Decimal('33.34'), orden=3)

        # 7. Las 20 Subactividades (distribuidas en las actividades respetando 100%)
        # Helper para crear subactividades
        def add_sub(act, cod, nom, peso, dur, d_offset, avance=0, hito=False, costo_fijo=0):
            inicio = fecha_ini + timedelta(days=d_offset)
            fin = inicio + timedelta(days=dur - 1)
            return Subactividad.objects.create(
                actividad=act,
                codigo=cod,
                nombre=nom,
                peso_porcentual=Decimal(str(peso)),
                duracion_dias=dur,
                fecha_inicio_plan=inicio,
                fecha_fin_plan=fin,
                porcentaje_avance=Decimal(str(avance)),
                costo_fijo=Decimal(str(costo_fijo)),
                es_hito=hito,
                estado='COMPLETADA' if avance == 100 else ('EN_PROGRESO' if avance > 0 else 'PENDIENTE'),
                orden=int(cod.split('.')[-1])
            )

        # Act 1.1 (2 subs: 50% + 50%)
        s111 = add_sub(a11, '1.1.1', 'Entrevistas de Requerimientos y Stakeholders', 50.00, 5, 0, 100, costo_fijo=400)
        s112 = add_sub(a11, '1.1.2', 'Formalización de la Matriz de Alcance', 50.00, 5, 5, 100, costo_fijo=300)

        # Act 1.2 (2 subs: 50% + 50%)
        s121 = add_sub(a12, '1.2.1', 'Diseño de Modelo Relacional y Diccionario', 50.00, 6, 8, 100, costo_fijo=500)
        s122 = add_sub(a12, '1.2.2', 'Prototipos de UI y Ajuste de Mockups', 50.00, 6, 12, 100, costo_fijo=600)

        # Act 1.3 (2 subs: 50% + 50%)
        s131 = add_sub(a13, '1.3.1', 'Consolidación de la Línea Base del Cronograma', 50.00, 4, 16, 100, costo_fijo=350)
        s132 = add_sub(a13, '1.3.2', 'Hito: Aprobación Formal del Proyecto', 50.00, 1, 20, 100, hito=True)

        # Act 2.1 (2 subs: 50% + 50%)
        s211 = add_sub(a21, '2.1.1', 'Configuración de App Okta y Claims de Rol', 50.00, 6, 21, 90, costo_fijo=800)
        s212 = add_sub(a21, '2.1.2', 'Middleware RBAC y Protección de Rutas', 50.00, 5, 27, 85, costo_fijo=650)

        # Act 2.2 (2 subs: 50% + 50%)
        s221 = add_sub(a22, '2.2.1', 'Motor de Precedencias y Algoritmo de Ciclos', 50.00, 7, 28, 80, costo_fijo=900)
        s222 = add_sub(a22, '2.2.2', 'Renderizado Interactivo de Carta Gantt', 50.00, 6, 35, 75, costo_fijo=750)

        # Act 2.3 (2 subs: 50% + 50%)
        s231 = add_sub(a23, '2.3.1', 'Gestión de Tarifas y Registro de Horas', 50.00, 5, 34, 60, costo_fijo=450)
        s232 = add_sub(a23, '2.3.2', 'Detector Automático de Sobreasignaciones', 50.00, 5, 39, 50, costo_fijo=500)

        # Act 3.1 (2 subs: 50% + 50%)
        s311 = add_sub(a31, '3.1.1', 'Parametrización de los 8 KPIs de Proyecto', 50.00, 5, 42, 40, costo_fijo=600)
        s312 = add_sub(a31, '3.1.2', 'Parametrización de los 12 KPIs de Cambio', 50.00, 5, 47, 30, costo_fijo=600)

        # Act 3.2 (2 subs: 50% + 50%)
        s321 = add_sub(a32, '3.2.1', 'Flujo de Aprobación de 10 Etapas', 50.00, 6, 45, 50, costo_fijo=700)
        s322 = add_sub(a32, '3.2.2', 'Servicio de Propagación Automática', 50.00, 5, 51, 40, costo_fijo=850)

        # Act 3.3 (2 subs: 50% + 50%)
        s331 = add_sub(a33, '3.3.1', 'Tablero 1: Operativo del Proyecto', 50.00, 5, 54, 25, costo_fijo=550)
        s332 = add_sub(a33, '3.3.2', 'Tablero 2: Estratégico de Gestión del Cambio', 50.00, 5, 58, 20, costo_fijo=550)

        # Act 4.1 (1 sub: 100%)
        s411 = add_sub(a41, '4.1.1', 'Batería de Pruebas de Integración y Carga', 100.00, 7, 62, 0, costo_fijo=900)

        # Act 4.2 (1 sub: 100%)
        s421 = add_sub(a42, '4.2.1', 'Talleres de Capacitación y Encuestas de Adopción', 100.00, 6, 68, 0, costo_fijo=1200)

        # Act 4.3 (1 sub: 100%)
        s431 = add_sub(a43, '4.3.1', 'Auditoría Final y Cierre Contractual', 100.00, 4, 74, 0, hito=True, costo_fijo=500)

        # 8. Las 4 Dependencias Estrictas (FS, SS, FF, SF con lags)
        # 1) FS: 1.1.1 -> 1.1.2 (Fin a Inicio, lag +1 día)
        Precedencia.objects.create(tarea_origen=s111, tarea_destino=s112, tipo='FS', lag_dias=1)
        # 2) SS: 2.1.1 -> 2.1.2 (Inicio a Inicio, lag +2 días)
        Precedencia.objects.create(tarea_origen=s211, tarea_destino=s212, tipo='SS', lag_dias=2)
        # 3) FF: 2.2.1 -> 2.2.2 (Fin a Fin, lag 0 días)
        Precedencia.objects.create(tarea_origen=s221, tarea_destino=s222, tipo='FF', lag_dias=0)
        # 4) SF: 3.2.1 -> 3.2.2 (Inicio a Fin, lag +3 días)
        Precedencia.objects.create(tarea_origen=s321, tarea_destino=s322, tipo='SF', lag_dias=3)

        # 9. Asignación de Recursos y Demostración de Sobreasignación
        # Asignamos horas estándar a varias tareas
        AsignacionRecurso.objects.create(subactividad=s111, recurso=p1, horas_asignadas=Decimal('30.0'), fecha_inicio=s111.fecha_inicio_plan, fecha_fin=s111.fecha_fin_plan)
        AsignacionRecurso.objects.create(subactividad=s122, recurso=p4, horas_asignadas=Decimal('35.0'), fecha_inicio=s122.fecha_inicio_plan, fecha_fin=s122.fecha_fin_plan)
        AsignacionRecurso.objects.create(subactividad=s211, recurso=p3, horas_asignadas=Decimal('40.0'), fecha_inicio=s211.fecha_inicio_plan, fecha_fin=s211.fecha_fin_plan)
        AsignacionRecurso.objects.create(subactividad=s321, recurso=p2, horas_asignadas=Decimal('40.0'), fecha_inicio=s321.fecha_inicio_plan, fecha_fin=s321.fecha_fin_plan)

        # CASO DE SOBREASIGNACIÓN INTENCIONAL (para demostrar alerta en vivo):
        # Asignamos a Ing. Matías Herrera a dos tareas en paralelo en los mismos días superando 8h/día
        AsignacionRecurso.objects.create(subactividad=s221, recurso=p3, horas_asignadas=Decimal('50.0'), fecha_inicio=s221.fecha_inicio_plan, fecha_fin=s221.fecha_fin_plan)
        AsignacionRecurso.objects.create(subactividad=s231, recurso=p3, horas_asignadas=Decimal('45.0'), fecha_inicio=s221.fecha_inicio_plan, fecha_fin=s221.fecha_fin_plan)

        # 10. Los 6 Hitos Exigidos
        Hito.objects.create(proyecto=proyecto, subactividad=s132, nombre='Hito 1: Aprobación Formal del Proyecto y WBS', fecha_programada=s132.fecha_fin_plan, fecha_cumplimiento=s132.fecha_fin_plan, cumplido=True)
        Hito.objects.create(proyecto=proyecto, subactividad=s212, nombre='Hito 2: Integración de Autenticación Okta Validada', fecha_programada=s212.fecha_fin_plan, fecha_cumplimiento=s212.fecha_fin_plan, cumplido=True)
        Hito.objects.create(proyecto=proyecto, subactividad=s222, nombre='Hito 3: Motor de Gantt y Precedencias Operativo', fecha_programada=s222.fecha_fin_plan, cumplido=False)
        Hito.objects.create(proyecto=proyecto, subactividad=s322, nombre='Hito 4: Módulo de Gestión del Cambio y Propagación Listo', fecha_programada=s322.fecha_fin_plan, cumplido=False)
        Hito.objects.create(proyecto=proyecto, subactividad=s332, nombre='Hito 5: Tableros Duales de Comando Operativos', fecha_programada=s332.fecha_fin_plan, cumplido=False)
        Hito.objects.create(proyecto=proyecto, subactividad=s431, nombre='Hito 6: Cierre del Proyecto y Adopción Cultural', fecha_programada=s431.fecha_fin_plan, cumplido=False)

        # 11. Las 5 Solicitudes de Cambio (en distintas etapas de las 10 exigidas)
        rfc1 = SolicitudCambio.objects.create(
            proyecto=proyecto,
            codigo='RFC-001',
            titulo='Ampliación de campos en Claims de Okta para perfiles directivos',
            descripcion='Se requiere incorporar claims avanzados en el ID Token para identificar divisiones regionales de los evaluadores.',
            justificacion='Requerimiento de auditoría de seguridad y gobernanza.',
            solicitante='Director de Ciberseguridad',
            responsable='Ing. Carlos Mendoza',
            prioridad='ALTA',
            etapa_actual=8,  # Ejecución y Propagación
            estado='EN_EJECUCION',
            impacto_plazo_dias=3,
            impacto_costo=Decimal('1500.00'),
            subactividad_afectada=s211,
            propagado=True,
            fecha_solicitud=hoy - timedelta(days=12),
            fecha_resolucion=hoy - timedelta(days=7),
        )
        HistorialCambio.objects.create(solicitud=rfc1, etapa=1, usuario='Director de Ciberseguridad', comentario='Solicitud registrada.')
        HistorialCambio.objects.create(solicitud=rfc1, etapa=6, usuario='Comité CCB', comentario='Aprobada por unanimidad.')
        HistorialCambio.objects.create(solicitud=rfc1, etapa=8, usuario='Sistema', comentario='PROPAGADA: +3 días a tarea 2.1.1 y +$1500 presupuesto.')

        rfc2 = SolicitudCambio.objects.create(
            proyecto=proyecto,
            codigo='RFC-002',
            titulo='Incorporación de exportación PDF en Tablero de Gestión del Cambio',
            descripcion='Generación de reporte ejecutivo en PDF para la reunión mensual de directorio.',
            justificacion='Facilitar la revisión gerencial sin necesidad de acceso a la consola web.',
            solicitante='Gerencia de Operaciones',
            responsable='Lic. Sofía Valenzuela',
            prioridad='MEDIA',
            etapa_actual=4,  # Evaluación Técnica y de Costos
            estado='EN_EVALUACION',
            impacto_plazo_dias=2,
            impacto_costo=Decimal('800.00'),
            subactividad_afectada=s332,
            propagado=False,
            fecha_solicitud=hoy - timedelta(days=4),
        )
        HistorialCambio.objects.create(solicitud=rfc2, etapa=1, usuario='Gerencia de Operaciones', comentario='Registro inicial.')
        HistorialCambio.objects.create(solicitud=rfc2, etapa=3, usuario='Lic. Sofía Valenzuela', comentario='Impacto evaluado como factible.')

        rfc3 = SolicitudCambio.objects.create(
            proyecto=proyecto,
            codigo='RFC-003',
            titulo='Soporte para dependencias tipo Start-to-Finish (SF) avanzadas con desfase negativo',
            descripcion='Ajuste en la matriz de cálculo para admitir desfases negativos (leads) en tareas críticas de cierre.',
            justificacion='Optimización del camino crítico.',
            solicitante='Líder Técnico',
            responsable='Ing. Matías Herrera',
            prioridad='ALTA',
            etapa_actual=5,  # Revisión por Comité CCB
            estado='EN_COMITE',
            impacto_plazo_dias=4,
            impacto_costo=Decimal('2200.00'),
            subactividad_afectada=s221,
            propagado=False,
            fecha_solicitud=hoy - timedelta(days=3),
        )

        rfc4 = SolicitudCambio.objects.create(
            proyecto=proyecto,
            codigo='RFC-004',
            titulo='Integración de encuesta de pulso semanal para Adopción Cultural',
            descripcion='Módulo interactivo corto de 3 preguntas al inicio de sesión para medir resistencia al cambio.',
            justificacion='Alimentar en tiempo real el KPI-CHG-09 y KPI-CHG-12.',
            solicitante='Especialista Gestión del Cambio',
            responsable='Lic. Sofía Valenzuela',
            prioridad='BAJA',
            etapa_actual=1,  # Identificación y Registro
            estado='REGISTRADA',
            impacto_plazo_dias=1,
            impacto_costo=Decimal('400.00'),
            subactividad_afectada=s421,
            propagado=False,
            fecha_solicitud=hoy - timedelta(days=1),
        )

        rfc5 = SolicitudCambio.objects.create(
            proyecto=proyecto,
            codigo='RFC-005',
            titulo='Actualización de políticas de vencimiento de sesiones en Okta',
            descripcion='Reducción del token timeout a 30 minutos por estándar ISO 27001.',
            justificacion='Cumplimiento de normativa de ciberseguridad bancaria.',
            solicitante='Oficial de Seguridad',
            responsable='Ing. Carlos Mendoza',
            prioridad='MEDIA',
            etapa_actual=9,  # Verificación y Cierre
            estado='EN_VERIFICACION',
            impacto_plazo_dias=1,
            impacto_costo=Decimal('600.00'),
            subactividad_afectada=s212,
            propagado=True,
            fecha_solicitud=hoy - timedelta(days=15),
            fecha_resolucion=hoy - timedelta(days=10),
        )

        self.stdout.write(self.style.SUCCESS(
            "¡Caso de prueba cargado exitosamente!\n"
            f"- Proyecto: {proyecto.codigo}\n"
            f"- 4 Etapas (Regla 100%: 25% c/u)\n"
            f"- 12 Actividades (Regla 100%)\n"
            f"- 20 Subactividades creadas\n"
            f"- 4 Precedencias estrictas (FS, SS, FF, SF con lags)\n"
            f"- 5 Profesionales + Recursos con tarifas horarias\n"
            f"- Caso de sobreasignación intencional configurado\n"
            f"- 6 Hitos registrados\n"
            f"- 20 KPIs listos para cálculo en tiempo real\n"
            f"- 5 Solicitudes de cambio en distintas etapas de las 10 del flujo\n"
        ))

