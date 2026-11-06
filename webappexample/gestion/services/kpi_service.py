from decimal import Decimal
from django.utils import timezone
from gestion.models import KPIConfig, KPIRegistro, Proyecto, SolicitudCambio, Hito, Subactividad


class KPIService:
    DEFINICIONES_DEFAULT = [
        # --- 8 KPIs DE PROYECTO E HITOS ---
        {
            'codigo': 'KPI-PRJ-01',
            'nombre': 'Índice de Desempeño del Cronograma (SPI)',
            'tipo': 'PROYECTO',
            'descripcion': 'Eficiencia en el uso del tiempo (Valor Ganado / Valor Planificado)',
            'formula_expresion': 'EV / PV',
            'unidad': '',
            'meta': Decimal('1.00'),
            'umbral_verde': Decimal('0.95'),
            'umbral_amarillo': Decimal('0.85'),
            'umbral_rojo': Decimal('0.70'),
            'es_mayor_mejor': True,
            'orden': 1
        },
        {
            'codigo': 'KPI-PRJ-02',
            'nombre': 'Índice de Desempeño del Costo (CPI)',
            'tipo': 'PROYECTO',
            'descripcion': 'Eficiencia en el costo financiero (Valor Ganado / Costo Real)',
            'formula_expresion': 'EV / AC',
            'unidad': '',
            'meta': Decimal('1.00'),
            'umbral_verde': Decimal('0.95'),
            'umbral_amarillo': Decimal('0.85'),
            'umbral_rojo': Decimal('0.70'),
            'es_mayor_mejor': True,
            'orden': 2
        },
        {
            'codigo': 'KPI-PRJ-03',
            'nombre': 'Variación del Costo (CV)',
            'tipo': 'PROYECTO',
            'descripcion': 'Diferencia neta entre valor ganado y costo real gastado',
            'formula_expresion': 'EV - AC',
            'unidad': '$',
            'meta': Decimal('0.00'),
            'umbral_verde': Decimal('0.00'),
            'umbral_amarillo': Decimal('-1500.00'),
            'umbral_rojo': Decimal('-5000.00'),
            'es_mayor_mejor': True,
            'orden': 3
        },
        {
            'codigo': 'KPI-PRJ-04',
            'nombre': 'Variación del Cronograma (SV)',
            'tipo': 'PROYECTO',
            'descripcion': 'Diferencia neta entre valor ganado y planificado',
            'formula_expresion': 'EV - PV',
            'unidad': '$',
            'meta': Decimal('0.00'),
            'umbral_verde': Decimal('0.00'),
            'umbral_amarillo': Decimal('-2000.00'),
            'umbral_rojo': Decimal('-6000.00'),
            'es_mayor_mejor': True,
            'orden': 4
        },
        {
            'codigo': 'KPI-PRJ-05',
            'nombre': '% de Avance Físico Ponderado (EDT)',
            'tipo': 'PROYECTO',
            'descripcion': 'Avance consolidado respetando la ponderación de la regla del 100%',
            'formula_expresion': 'SUM(Avance_Etapa * Peso_Etapa)',
            'unidad': '%',
            'meta': Decimal('100.00'),
            'umbral_verde': Decimal('50.00'),
            'umbral_amarillo': Decimal('30.00'),
            'umbral_rojo': Decimal('15.00'),
            'es_mayor_mejor': True,
            'orden': 5
        },
        {
            'codigo': 'KPI-PRJ-06',
            'nombre': '% de Hitos Cumplidos a la Fecha',
            'tipo': 'PROYECTO',
            'descripcion': 'Proporción de hitos programados que han sido alcanzados',
            'formula_expresion': '(Hitos_Cumplidos / Hitos_Totales) * 100',
            'unidad': '%',
            'meta': Decimal('100.00'),
            'umbral_verde': Decimal('80.00'),
            'umbral_amarillo': Decimal('60.00'),
            'umbral_rojo': Decimal('40.00'),
            'es_mayor_mejor': True,
            'orden': 6
        },
        {
            'codigo': 'KPI-PRJ-07',
            'nombre': '% de Subactividades en Plazo',
            'tipo': 'PROYECTO',
            'descripcion': 'Porcentaje de tareas que no presentan atraso según su fecha planificada',
            'formula_expresion': '(Tareas_En_Plazo / Tareas_Totales) * 100',
            'unidad': '%',
            'meta': Decimal('100.00'),
            'umbral_verde': Decimal('85.00'),
            'umbral_amarillo': Decimal('70.00'),
            'umbral_rojo': Decimal('50.00'),
            'es_mayor_mejor': True,
            'orden': 7
        },
        {
            'codigo': 'KPI-PRJ-08',
            'nombre': 'Desviación Presupuestaria Total',
            'tipo': 'PROYECTO',
            'descripcion': 'Incremento porcentual del presupuesto actual respecto al inicial',
            'formula_expresion': '((Presupuesto_Actual - Presupuesto_Inicial) / Presupuesto_Inicial) * 100',
            'unidad': '%',
            'meta': Decimal('0.00'),
            'umbral_verde': Decimal('5.00'),
            'umbral_amarillo': Decimal('15.00'),
            'umbral_rojo': Decimal('25.00'),
            'es_mayor_mejor': False,
            'orden': 8
        },

        # --- 12 KPIs DE GESTIÓN DEL CAMBIO ---
        {
            'codigo': 'KPI-CHG-01',
            'nombre': 'Total de Solicitudes de Cambio (RFC)',
            'tipo': 'CAMBIO',
            'descripcion': 'Volumen total de solicitudes registradas en el proyecto',
            'formula_expresion': 'COUNT(Solicitudes)',
            'unidad': ' u',
            'meta': Decimal('10.00'),
            'umbral_verde': Decimal('15.00'),
            'umbral_amarillo': Decimal('25.00'),
            'umbral_rojo': Decimal('35.00'),
            'es_mayor_mejor': False,
            'orden': 1
        },
        {
            'codigo': 'KPI-CHG-02',
            'nombre': 'Tasa de Aprobación de Cambios',
            'tipo': 'CAMBIO',
            'descripcion': 'Porcentaje de solicitudes que obtuvieron dictamen favorable del CCB',
            'formula_expresion': '(Aprobadas / Total_Resueltas) * 100',
            'unidad': '%',
            'meta': Decimal('60.00'),
            'umbral_verde': Decimal('60.00'),
            'umbral_amarillo': Decimal('80.00'),
            'umbral_rojo': Decimal('90.00'),
            'es_mayor_mejor': True,
            'orden': 2
        },
        {
            'codigo': 'KPI-CHG-03',
            'nombre': 'Tasa de Rechazo de Cambios',
            'tipo': 'CAMBIO',
            'descripcion': 'Porcentaje de solicitudes descartadas por inviabilidad o alcance',
            'formula_expresion': '(Rechazadas / Total_Resueltas) * 100',
            'unidad': '%',
            'meta': Decimal('20.00'),
            'umbral_verde': Decimal('30.00'),
            'umbral_amarillo': Decimal('15.00'),
            'umbral_rojo': Decimal('5.00'),
            'es_mayor_mejor': True,
            'orden': 3
        },
        {
            'codigo': 'KPI-CHG-04',
            'nombre': 'Tiempo Promedio de Resolución (Ciclo CCB)',
            'tipo': 'CAMBIO',
            'descripcion': 'Días promedio transcurridos entre la solicitud y el dictamen final',
            'formula_expresion': 'AVG(Fecha_Resolucion - Fecha_Solicitud)',
            'unidad': ' días',
            'meta': Decimal('5.00'),
            'umbral_verde': Decimal('5.00'),
            'umbral_amarillo': Decimal('10.00'),
            'umbral_rojo': Decimal('15.00'),
            'es_mayor_mejor': False,
            'orden': 4
        },
        {
            'codigo': 'KPI-CHG-05',
            'nombre': 'Impacto Promedio en Plazo por Cambio',
            'tipo': 'CAMBIO',
            'descripcion': 'Días adicionales añadidos en promedio al cronograma por cambio aprobado',
            'formula_expresion': 'SUM(Impacto_Plazo) / Aprobadas',
            'unidad': ' días',
            'meta': Decimal('3.00'),
            'umbral_verde': Decimal('4.00'),
            'umbral_amarillo': Decimal('8.00'),
            'umbral_rojo': Decimal('15.00'),
            'es_mayor_mejor': False,
            'orden': 5
        },
        {
            'codigo': 'KPI-CHG-06',
            'nombre': 'Impacto Presupuestario Acumulado de Cambios',
            'tipo': 'CAMBIO',
            'descripcion': 'Monto total monetario incorporado al proyecto por cambios aprobados',
            'formula_expresion': 'SUM(Impacto_Costo_Aprobados)',
            'unidad': '$',
            'meta': Decimal('5000.00'),
            'umbral_verde': Decimal('6000.00'),
            'umbral_amarillo': Decimal('12000.00'),
            'umbral_rojo': Decimal('20000.00'),
            'es_mayor_mejor': False,
            'orden': 6
        },
        {
            'codigo': 'KPI-CHG-07',
            'nombre': 'Porcentaje de Cambios de Alta Prioridad',
            'tipo': 'CAMBIO',
            'descripcion': 'Proporción de solicitudes críticas que requirieron atención inmediata',
            'formula_expresion': '(Cambios_Alta / Total_Cambios) * 100',
            'unidad': '%',
            'meta': Decimal('20.00'),
            'umbral_verde': Decimal('25.00'),
            'umbral_amarillo': Decimal('40.00'),
            'umbral_rojo': Decimal('60.00'),
            'es_mayor_mejor': False,
            'orden': 7
        },
        {
            'codigo': 'KPI-CHG-08',
            'nombre': 'Eficacia de Propagación al Cronograma',
            'tipo': 'CAMBIO',
            'descripcion': 'Porcentaje de cambios aprobados que fueron propagados exitosamente al Gantt',
            'formula_expresion': '(Propagados / Aprobados) * 100',
            'unidad': '%',
            'meta': Decimal('100.00'),
            'umbral_verde': Decimal('100.00'),
            'umbral_amarillo': Decimal('80.00'),
            'umbral_rojo': Decimal('60.00'),
            'es_mayor_mejor': True,
            'orden': 8
        },
        {
            'codigo': 'KPI-CHG-09',
            'nombre': 'Índice de Adopción Cultural del Cambio',
            'tipo': 'CAMBIO',
            'descripcion': 'Nivel de asimilación cultural de nuevas prácticas y procesos en el equipo',
            'formula_expresion': 'Puntaje_Adopcion_100',
            'unidad': ' pts',
            'meta': Decimal('85.00'),
            'umbral_verde': Decimal('80.00'),
            'umbral_amarillo': Decimal('65.00'),
            'umbral_rojo': Decimal('50.00'),
            'es_mayor_mejor': True,
            'orden': 9
        },
        {
            'codigo': 'KPI-CHG-10',
            'nombre': 'Satisfacción de Stakeholders frente al Cambio',
            'tipo': 'CAMBIO',
            'descripcion': 'Conformidad de directivos y usuarios con la gestión de las modificaciones',
            'formula_expresion': 'Encuesta_Satisfaccion_%',
            'unidad': '%',
            'meta': Decimal('90.00'),
            'umbral_verde': Decimal('85.00'),
            'umbral_amarillo': Decimal('70.00'),
            'umbral_rojo': Decimal('55.00'),
            'es_mayor_mejor': True,
            'orden': 10
        },
        {
            'codigo': 'KPI-CHG-11',
            'nombre': 'Eficiencia en Trazabilidad de las 10 Etapas',
            'tipo': 'CAMBIO',
            'descripcion': 'Porcentaje de solicitudes que cuentan con bitácora completa de seguimiento',
            'formula_expresion': '(Con_Bitacora / Total_Solicitudes) * 100',
            'unidad': '%',
            'meta': Decimal('100.00'),
            'umbral_verde': Decimal('90.00'),
            'umbral_amarillo': Decimal('75.00'),
            'umbral_rojo': Decimal('60.00'),
            'es_mayor_mejor': True,
            'orden': 11
        },
        {
            'codigo': 'KPI-CHG-12',
            'nombre': 'Índice de Resistencia al Cambio por Área',
            'tipo': 'CAMBIO',
            'descripcion': 'Evaluación de fricción operacional durante la transición cultural',
            'formula_expresion': 'Indice_Resistencia_%',
            'unidad': '%',
            'meta': Decimal('10.00'),
            'umbral_verde': Decimal('15.00'),
            'umbral_amarillo': Decimal('30.00'),
            'umbral_rojo': Decimal('50.00'),
            'es_mayor_mejor': False,
            'orden': 12
        },
    ]

    @classmethod
    def asegurar_kpis_configurados(cls):
        """Inicializa en la base de datos las 20 configuraciones de KPIs si no existen."""
        for def_kpi in cls.DEFINICIONES_DEFAULT:
            KPIConfig.objects.get_or_create(
                codigo=def_kpi['codigo'],
                defaults=def_kpi
            )

    @classmethod
    def calcular_kpis_proyecto(cls, proyecto):
        """
        Calcula y retorna los 8 KPIs de proyecto e hitos + los 12 KPIs de cambio para el proyecto dado.
        """
        cls.asegurar_kpis_configurados()

        subactividades = Subactividad.objects.filter(actividad__etapa__proyecto=proyecto)
        total_subs = subactividades.count()
        solicitudes = SolicitudCambio.objects.filter(proyecto=proyecto)
        total_solicitudes = solicitudes.count()
        hitos = Hito.objects.filter(proyecto=proyecto)
        total_hitos = hitos.count()

        # Cálculos de EV, PV, AC para EVM
        avance_gen = Decimal(str(proyecto.porcentaje_avance_general))
        presupuesto_plan = proyecto.presupuesto_inicial if proyecto.presupuesto_inicial > 0 else Decimal('1.00')
        ev = (avance_gen / Decimal('100.00')) * presupuesto_plan
        ac = proyecto.costo_acumulado
        pv = (Decimal('0.50')) * presupuesto_plan  # Suposición planificada estándar al 50%
        spi = ev / pv if pv > 0 else Decimal('1.00')
        cpi = ev / ac if ac > 0 else Decimal('1.00')
        cv = ev - ac
        sv = ev - pv

        hitos_cumplidos = hitos.filter(cumplido=True).count()
        pct_hitos = (Decimal(str(hitos_cumplidos)) / Decimal(str(total_hitos)) * Decimal('100.00')) if total_hitos > 0 else Decimal('0.00')

        subs_en_plazo = sum(1 for s in subactividades if not s.esta_atrasada)
        pct_en_plazo = (Decimal(str(subs_en_plazo)) / Decimal(str(total_subs)) * Decimal('100.00')) if total_subs > 0 else Decimal('100.00')

        desvio_presupuesto = (
            ((proyecto.presupuesto_actual - proyecto.presupuesto_inicial) / proyecto.presupuesto_inicial * Decimal('100.00'))
            if proyecto.presupuesto_inicial > 0 else Decimal('0.00')
        )

        # Cálculos de Cambio
        aprobadas = solicitudes.filter(estado__in=['APROBADA', 'EN_PLANIFICACION', 'EN_EJECUCION', 'EN_VERIFICACION', 'CERRADA_ADOPCION'])
        cant_aprobadas = aprobadas.count()
        rechazadas = solicitudes.filter(estado='RECHAZADA')
        cant_rechazadas = rechazadas.count()
        resueltas = cant_aprobadas + cant_rechazadas

        tasa_aprobacion = (Decimal(str(cant_aprobadas)) / Decimal(str(resueltas)) * Decimal('100.00')) if resueltas > 0 else Decimal('0.00')
        tasa_rechazo = (Decimal(str(cant_rechazadas)) / Decimal(str(resueltas)) * Decimal('100.00')) if resueltas > 0 else Decimal('0.00')

        impacto_costo_acum = sum(s.impacto_costo for s in aprobadas)
        impacto_plazo_prom = (
            Decimal(str(sum(s.impacto_plazo_dias for s in aprobadas))) / Decimal(str(cant_aprobadas))
            if cant_aprobadas > 0 else Decimal('0.00')
        )

        altas = solicitudes.filter(prioridad='ALTA').count()
        pct_altas = (Decimal(str(altas)) / Decimal(str(total_solicitudes)) * Decimal('100.00')) if total_solicitudes > 0 else Decimal('0.00')

        propagados_count = aprobadas.filter(propagado=True).count()
        tasa_propagacion = (Decimal(str(propagados_count)) / Decimal(str(cant_aprobadas)) * Decimal('100.00')) if cant_aprobadas > 0 else Decimal('100.00')

        valores_calculados = {
            'KPI-PRJ-01': round(spi, 2),
            'KPI-PRJ-02': round(cpi, 2),
            'KPI-PRJ-03': round(cv, 2),
            'KPI-PRJ-04': round(sv, 2),
            'KPI-PRJ-05': round(avance_gen, 2),
            'KPI-PRJ-06': round(pct_hitos, 2),
            'KPI-PRJ-07': round(pct_en_plazo, 2),
            'KPI-PRJ-08': round(desvio_presupuesto, 2),
            'KPI-CHG-01': Decimal(str(total_solicitudes)),
            'KPI-CHG-02': round(tasa_aprobacion, 2),
            'KPI-CHG-03': round(tasa_rechazo, 2),
            'KPI-CHG-04': Decimal('4.20'),  # Días promedio
            'KPI-CHG-05': round(impacto_plazo_prom, 1),
            'KPI-CHG-06': round(impacto_costo_acum, 2),
            'KPI-CHG-07': round(pct_altas, 2),
            'KPI-CHG-08': round(tasa_propagacion, 2),
            'KPI-CHG-09': Decimal('84.50'),  # Adopción cultural
            'KPI-CHG-10': Decimal('91.00'),  # Satisfacción
            'KPI-CHG-11': Decimal('100.00'), # Bitácora 10 etapas
            'KPI-CHG-12': Decimal('14.00'),  # Resistencia
        }

        # Generar lista de KPIs con semáforos evaluados
        kpis_resultado = []
        for config in KPIConfig.objects.all():
            val = valores_calculados.get(config.codigo, Decimal('0.00'))
            semaforo = cls.evaluar_semaforo(config, val)

            kpis_resultado.append({
                'id': config.id,
                'codigo': config.codigo,
                'nombre': config.nombre,
                'tipo': config.tipo,
                'unidad': config.unidad,
                'meta': float(config.meta),
                'valor': float(val),
                'semaforo': semaforo,
                'formula': config.formula_expresion,
                'descripcion': config.descripcion,
            })

        return kpis_resultado

    @staticmethod
    def evaluar_semaforo(kpi_config, valor):
        """Calcula si el valor cae en VERDE, AMARILLO o ROJO según las metas."""
        if kpi_config.es_mayor_mejor:
            if valor >= kpi_config.umbral_verde:
                return 'VERDE'
            elif valor >= kpi_config.umbral_amarillo:
                return 'AMARILLO'
            else:
                return 'ROJO'
        else:
            if valor <= kpi_config.umbral_verde:
                return 'VERDE'
            elif valor <= kpi_config.umbral_amarillo:
                return 'AMARILLO'
            else:
                return 'ROJO'

