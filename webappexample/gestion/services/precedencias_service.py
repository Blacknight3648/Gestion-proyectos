from datetime import timedelta
from collections import defaultdict, deque
from django.core.exceptions import ValidationError
from gestion.models import Subactividad, Precedencia


class PrecedenciasService:
    @staticmethod
    def validar_dependencia_circular(origen_id, destino_id):
        """
        Verifica si agregar una relación origen -> destino crearía un ciclo en el grafo de precedencias.
        Usa recorrido DFS para buscar si existe un camino desde destino hasta origen.
        """
        if origen_id == destino_id:
            return True

        # Grafo de adyacencia existente
        grafo = defaultdict(list)
        for prec in Precedencia.objects.all():
            grafo[prec.tarea_origen_id].append(prec.tarea_destino_id)

        # Si ya existe un camino desde destino hasta origen, conectar origen -> destino creará un ciclo
        visitados = set()
        cola = deque([destino_id])

        while cola:
            actual = cola.popleft()
            if actual == origen_id:
                return True
            if actual not in visitados:
                visitados.add(actual)
                for vecino in grafo[actual]:
                    if vecino not in visitados:
                        cola.append(vecino)

        return False

    @staticmethod
    def calcular_nueva_fecha_inicio(origen, tipo, lag_dias, duracion_destino):
        """
        Calcula la fecha de inicio resultante para la tarea destino según el tipo de precedencia:
        - FS: Fin a Inicio -> inicio_destino = fin_origen + lag + 1 día
        - SS: Inicio a Inicio -> inicio_destino = inicio_origen + lag
        - FF: Fin a Fin -> fin_destino = fin_origen + lag -> inicio_destino = fin_destino - duracion
        - SF: Inicio a Fin -> fin_destino = inicio_origen + lag -> inicio_destino = fin_destino - duracion
        """
        lag = timedelta(days=lag_dias)

        if tipo == 'FS':
            fecha_inicio = origen.fecha_fin_plan + timedelta(days=1) + lag
        elif tipo == 'SS':
            fecha_inicio = origen.fecha_inicio_plan + lag
        elif tipo == 'FF':
            fecha_fin = origen.fecha_fin_plan + lag
            fecha_inicio = fecha_fin - timedelta(days=max(0, duracion_destino - 1))
        elif tipo == 'SF':
            fecha_fin = origen.fecha_inicio_plan + lag
            fecha_inicio = fecha_fin - timedelta(days=max(0, duracion_destino - 1))
        else:
            fecha_inicio = origen.fecha_fin_plan + timedelta(days=1) + lag

        return fecha_inicio

    @classmethod
    def recalcular_en_cascada(cls, subactividad):
        """
        Recorre en cascada todas las tareas dependientes (salientes) y actualiza sus fechas
        en función de los tipos de enlace (FS, SS, FF, SF) y desfases.
        """
        cola = deque([subactividad])
        actualizadas = set()

        while cola:
            tarea_actual = cola.popleft()
            precedencias_salientes = tarea_actual.precedencias_salientes.select_related('tarea_destino').all()

            for prec in precedencias_salientes:
                hija = prec.tarea_destino
                nueva_fecha_inicio = cls.calcular_nueva_fecha_inicio(
                    tarea_actual, prec.tipo, prec.lag_dias, hija.duracion_dias
                )

                # Si la nueva fecha de inicio es posterior a la actual, ajustamos
                if nueva_fecha_inicio > hija.fecha_inicio_plan:
                    dias_duracion = max(1, hija.duracion_dias)
                    hija.fecha_inicio_plan = nueva_fecha_inicio
                    hija.fecha_fin_plan = nueva_fecha_inicio + timedelta(days=dias_duracion - 1)
                    hija.save(update_fields=['fecha_inicio_plan', 'fecha_fin_plan'])
                    actualizadas.add(hija.id)
                    cola.append(hija)

        return len(actualizadas)

