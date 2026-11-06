from datetime import timedelta
from decimal import Decimal
from django.utils import timezone
from gestion.models import SolicitudCambio, HistorialCambio
from gestion.services.precedencias_service import PrecedenciasService


class PropagacionService:
    @classmethod
    def avanzar_etapa(cls, solicitud, nueva_etapa, usuario="Director", comentario=""):
        """
        Avanza o retrocede la solicitud a lo largo del flujo de 10 etapas:
        1. Identificación y Registro
        2. Clasificación y Asignación
        3. Análisis de Impacto Inicial
        4. Evaluación Técnica y de Costos
        5. Revisión por Comité de Cambios (CCB)
        6. Decisión (Aprobación / Rechazo)
        7. Planificación e Integración
        8. Ejecución y Propagación
        9. Verificación y Cierre
        10. Adopción Cultural y Medición
        """
        solicitud.etapa_actual = nueva_etapa

        # Mapeo de estado según etapa
        if nueva_etapa in [1, 2]:
            solicitud.estado = 'REGISTRADA'
        elif nueva_etapa in [3, 4]:
            solicitud.estado = 'EN_EVALUACION'
        elif nueva_etapa == 5:
            solicitud.estado = 'EN_COMITE'
        elif nueva_etapa == 6:
            solicitud.estado = 'APROBADA'
            solicitud.fecha_resolucion = timezone.now().date()
        elif nueva_etapa == 7:
            solicitud.estado = 'EN_PLANIFICACION'
        elif nueva_etapa == 8:
            solicitud.estado = 'EN_EJECUCION'
            # Disparar la propagación automática
            cls.propagar_impacto(solicitud, usuario)
        elif nueva_etapa == 9:
            solicitud.estado = 'EN_VERIFICACION'
        elif nueva_etapa == 10:
            solicitud.estado = 'CERRADA_ADOPCION'

        solicitud.save()

        # Guardar en bitácora de historial
        HistorialCambio.objects.create(
            solicitud=solicitud,
            etapa=nueva_etapa,
            usuario=usuario,
            comentario=comentario or f"Transición a la etapa {solicitud.get_etapa_actual_display()}"
        )

        return solicitud

    @classmethod
    def propagar_impacto(cls, solicitud, usuario="Director"):
        """
        Aplica automáticamente el impacto al proyecto:
        1. Si hay días de impacto y subactividad afectada:
           - Incrementa la duración y retrasa la fecha de fin de la subactividad.
           - Recalcula en cascada todas las tareas dependientes en la Carta Gantt.
        2. Si hay impacto en costo:
           - Actualiza el presupuesto y costo acumulado del proyecto.
        3. Marca la solicitud como propagada.
        """
        if solicitud.propagado:
            return False, "La solicitud ya había sido propagada."

        proyecto = solicitud.proyecto
        cambios_realizados = []

        # 1. Propagación a fechas y Gantt
        if solicitud.subactividad_afectada and solicitud.impacto_plazo_dias > 0:
            sub = solicitud.subactividad_afectada
            dias_extra = solicitud.impacto_plazo_dias
            sub.duracion_dias += dias_extra
            sub.fecha_fin_plan = sub.fecha_fin_plan + timedelta(days=dias_extra)
            sub.save(update_fields=['duracion_dias', 'fecha_fin_plan'])

            # Recálculo en cascada para todas las tareas dependientes
            afectadas = PrecedenciasService.recalcular_en_cascada(sub)
            cambios_realizados.append(
                f"Gantt: Se añadieron {dias_extra} días a {sub.codigo}. Se recalcularon {afectadas} tareas dependientes."
            )

        # 2. Propagación a costos y presupuesto
        if solicitud.impacto_costo > Decimal('0.00'):
            proyecto.presupuesto_actual += solicitud.impacto_costo
            proyecto.costo_acumulado += solicitud.impacto_costo
            proyecto.save(update_fields=['presupuesto_actual', 'costo_acumulado'])
            cambios_realizados.append(
                f"Costos: Se incrementó el presupuesto actual en ${solicitud.impacto_costo}."
            )

        solicitud.propagado = True
        solicitud.save(update_fields=['propagado'])

        HistorialCambio.objects.create(
            solicitud=solicitud,
            etapa=solicitud.etapa_actual,
            usuario=usuario,
            comentario=f"PROPAGACIÓN AUTOMÁTICA EJECUTADA: {'; '.join(cambios_realizados)}"
        )

        return True, cambios_realizados

