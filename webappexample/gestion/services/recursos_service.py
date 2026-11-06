from collections import defaultdict
from datetime import timedelta
from decimal import Decimal
from gestion.models import Recurso, AsignacionRecurso


class RecursosService:
    @staticmethod
    def detectar_sobreasignaciones(proyecto=None):
        """
        Analiza día a día la carga de trabajo asignada a cada recurso profesional.
        Si la suma de horas asignadas en un día supera su 'jornada_diaria_horas' (típicamente 8h),
        se genera una alerta de sobreasignación.
        """
        asignaciones = AsignacionRecurso.objects.select_related('recurso', 'subactividad__actividad__etapa__proyecto')
        if proyecto:
            asignaciones = asignaciones.filter(subactividad__actividad__etapa__proyecto=proyecto)

        # Mapa: recurso_id -> fecha -> total_horas_dia
        horas_por_dia = defaultdict(lambda: defaultdict(Decimal))
        detalles_asignacion = defaultdict(lambda: defaultdict(list))

        for asig in asignaciones:
            recurso = asig.recurso
            # Solo evaluamos recursos con jornada definida (recursos humanos)
            if not recurso.jornada_diaria_horas or recurso.jornada_diaria_horas <= 0:
                continue

            delta_dias = (asig.fecha_fin - asig.fecha_inicio).days + 1
            if delta_dias <= 0:
                delta_dias = 1
            horas_diarias_asig = Decimal(str(asig.horas_asignadas)) / Decimal(str(delta_dias))

            curr = asig.fecha_inicio
            while curr <= asig.fecha_fin:
                horas_por_dia[recurso.id][curr] += horas_diarias_asig
                detalles_asignacion[recurso.id][curr].append({
                    'subactividad': asig.subactividad.codigo,
                    'nombre_tarea': asig.subactividad.nombre,
                    'horas': round(float(horas_diarias_asig), 1)
                })
                curr += timedelta(days=1)

        alertas = []
        for recurso_id, dias in horas_por_dia.items():
            recurso = Recurso.objects.get(id=recurso_id)
            limite = recurso.jornada_diaria_horas
            for fecha, horas_totales in dias.items():
                if horas_totales > limite:
                    exceso = horas_totales - limite
                    alertas.append({
                        'recurso_id': recurso.id,
                        'recurso_nombre': recurso.nombre,
                        'cargo': recurso.cargo_o_detalle,
                        'fecha': fecha.strftime('%Y-%m-%d'),
                        'horas_asignadas': round(float(horas_totales), 1),
                        'jornada_maxima': float(limite),
                        'exceso_horas': round(float(exceso), 1),
                        'tareas_involucradas': detalles_asignacion[recurso_id][fecha]
                    })

        # Ordenar por fecha y luego por gravedad
        alertas.sort(key=lambda x: (x['fecha'], -x['exceso_horas']))
        return alertas

    @staticmethod
    def resumen_costos_recursos(proyecto=None):
        """
        Retorna el desglose de costos por recurso para el proyecto.
        """
        asignaciones = AsignacionRecurso.objects.select_related('recurso')
        if proyecto:
            asignaciones = asignaciones.filter(subactividad__actividad__etapa__proyecto=proyecto)

        resumen = defaultdict(lambda: {'recurso': None, 'horas_totales': Decimal('0'), 'costo_total': Decimal('0')})

        for asig in asignaciones:
            r = asig.recurso
            resumen[r.id]['recurso'] = r
            resumen[r.id]['horas_totales'] += Decimal(str(asig.horas_asignadas))
            resumen[r.id]['costo_total'] += asig.costo_asignacion

        lista = []
        for rid, item in resumen.items():
            lista.append({
                'nombre': item['recurso'].nombre,
                'tipo': item['recurso'].tipo.nombre,
                'tarifa': float(item['recurso'].tarifa_por_hora),
                'horas': float(item['horas_totales']),
                'costo': float(item['costo_total']),
            })
        return lista

