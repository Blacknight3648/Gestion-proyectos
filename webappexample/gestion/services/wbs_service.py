from decimal import Decimal
from django.core.exceptions import ValidationError


class WBSService:
    @staticmethod
    def validar_regla_100_etapas(proyecto):
        """
        Valida que la suma de pesos de las etapas del proyecto sea 100%.
        Retorna (es_valido, suma_actual, diferencia).
        """
        etapas = proyecto.etapas.all()
        if not etapas.exists():
            return True, Decimal('0.00'), Decimal('0.00')
        suma = sum(e.peso_porcentual for e in etapas)
        diferencia = Decimal('100.00') - suma
        es_valido = abs(diferencia) < Decimal('0.05')
        return es_valido, suma, diferencia

    @staticmethod
    def validar_regla_100_actividades(etapa):
        """
        Valida que la suma de pesos de las actividades de una etapa sea 100%.
        """
        actividades = etapa.actividades.all()
        if not actividades.exists():
            return True, Decimal('0.00'), Decimal('0.00')
        suma = sum(a.peso_porcentual for a in actividades)
        diferencia = Decimal('100.00') - suma
        es_valido = abs(diferencia) < Decimal('0.05')
        return es_valido, suma, diferencia

    @staticmethod
    def validar_regla_100_subactividades(actividad):
        """
        Valida que la suma de pesos de las subactividades de una actividad sea 100%.
        """
        subactividades = actividad.subactividades.all()
        if not subactividades.exists():
            return True, Decimal('0.00'), Decimal('0.00')
        suma = sum(s.peso_porcentual for s in subactividades)
        diferencia = Decimal('100.00') - suma
        es_valido = abs(diferencia) < Decimal('0.05')
        return es_valido, suma, diferencia

    @staticmethod
    def calcular_avance_arbol(proyecto):
        """
        Recorre y retorna la estructura jerárquica con avances y cumplimiento de la regla del 100%.
        """
        arbol = []
        valido_global, suma_etapas, _ = WBSService.validar_regla_100_etapas(proyecto)

        for etapa in proyecto.etapas.all():
            valido_etapa, suma_acts, _ = WBSService.validar_regla_100_actividades(etapa)
            nodo_etapa = {
                'id': etapa.id,
                'codigo': etapa.codigo,
                'nombre': etapa.nombre,
                'peso': float(etapa.peso_porcentual),
                'avance': etapa.porcentaje_avance,
                'costo': float(etapa.costo_total),
                'regla_100_valida': valido_etapa,
                'suma_hijos': float(suma_acts),
                'actividades': []
            }
            for act in etapa.actividades.all():
                valido_act, suma_subs, _ = WBSService.validar_regla_100_subactividades(act)
                nodo_act = {
                    'id': act.id,
                    'codigo': act.codigo,
                    'nombre': act.nombre,
                    'peso': float(act.peso_porcentual),
                    'avance': act.porcentaje_avance,
                    'costo': float(act.costo_total),
                    'fecha_inicio': act.fecha_inicio.strftime('%Y-%m-%d') if act.fecha_inicio else None,
                    'fecha_fin': act.fecha_fin.strftime('%Y-%m-%d') if act.fecha_fin else None,
                    'regla_100_valida': valido_act,
                    'suma_hijos': float(suma_subs),
                    'subactividades': []
                }
                for sub in act.subactividades.all():
                    nodo_act['subactividades'].append({
                        'id': sub.id,
                        'codigo': sub.codigo,
                        'nombre': sub.nombre,
                        'peso': float(sub.peso_porcentual),
                        'avance': float(sub.porcentaje_avance),
                        'duracion': sub.duracion_dias,
                        'fecha_inicio_plan': sub.fecha_inicio_plan.strftime('%Y-%m-%d'),
                        'fecha_fin_plan': sub.fecha_fin_plan.strftime('%Y-%m-%d'),
                        'costo': float(sub.costo_total),
                        'es_hito': sub.es_hito,
                        'atrasada': sub.esta_atrasada,
                        'estado': sub.estado
                    })
                nodo_etapa['actividades'].append(nodo_act)
            arbol.append(nodo_etapa)

        return {
            'regla_100_global': valido_global,
            'suma_etapas': float(suma_etapas),
            'avance_general': proyecto.porcentaje_avance_general,
            'etapas': arbol
        }

