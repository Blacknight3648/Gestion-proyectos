from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal


class Proyecto(models.Model):
    ESTADOS = [
        ('PLANIFICACION', 'Planificación'),
        ('EN_EJECUCION', 'En Ejecución'),
        ('PAUSADO', 'En Pausa'),
        ('CERRADO', 'Cerrado'),
    ]

    nombre = models.CharField(max_length=200)
    codigo = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField(blank=True, default='')
    director_nombre = models.CharField(max_length=150, default='Director de Proyecto')
    fecha_inicio = models.DateField(default=timezone.now)
    fecha_fin_plan = models.DateField()
    fecha_fin_real = models.DateField(null=True, blank=True)
    presupuesto_inicial = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    presupuesto_actual = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    costo_acumulado = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PLANIFICACION')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"

    @property
    def porcentaje_avance_general(self):
        etapas = self.etapas.all()
        if not etapas.exists():
            return 0.0
        total_avance = 0.0
        for etapa in etapas:
            # Ponderación según la regla del 100% de la etapa
            peso = float(etapa.peso_porcentual) / 100.0
            total_avance += float(etapa.porcentaje_avance) * peso
        return round(total_avance, 2)

    @property
    def duracion_dias_plan(self):
        if self.fecha_inicio and self.fecha_fin_plan:
            return (self.fecha_fin_plan - self.fecha_inicio).days
        return 0


class Etapa(models.Model):
    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, related_name='etapas')
    codigo = models.CharField(max_length=20)  # Ej. 1.0, 2.0, 3.0, 4.0
    nombre = models.CharField(max_length=150)
    peso_porcentual = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('25.00'))  # Regla 100%
    orden = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['orden', 'codigo']
        unique_together = ('proyecto', 'codigo')

    def __str__(self):
        return f"{self.codigo} {self.nombre}"

    @property
    def porcentaje_avance(self):
        actividades = self.actividades.all()
        if not actividades.exists():
            return 0.0
        total = 0.0
        for act in actividades:
            peso = float(act.peso_porcentual) / 100.0
            total += float(act.porcentaje_avance) * peso
        return round(total, 2)

    @property
    def costo_total(self):
        return sum(act.costo_total for act in self.actividades.all())


class Actividad(models.Model):
    etapa = models.ForeignKey(Etapa, on_delete=models.CASCADE, related_name='actividades')
    codigo = models.CharField(max_length=20)  # Ej. 1.1, 1.2, 1.3
    nombre = models.CharField(max_length=150)
    peso_porcentual = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('33.33'))  # Regla 100%
    orden = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['orden', 'codigo']
        unique_together = ('etapa', 'codigo')

    def __str__(self):
        return f"{self.codigo} {self.nombre}"

    @property
    def porcentaje_avance(self):
        subacts = self.subactividades.all()
        if not subacts.exists():
            return 0.0
        total = 0.0
        for sub in subacts:
            peso = float(sub.peso_porcentual) / 100.0
            total += float(sub.porcentaje_avance) * peso
        return round(total, 2)

    @property
    def fecha_inicio(self):
        subacts = self.subactividades.all()
        if subacts.exists():
            return min(sub.fecha_inicio_plan for sub in subacts)
        return None

    @property
    def fecha_fin(self):
        subacts = self.subactividades.all()
        if subacts.exists():
            return max(sub.fecha_fin_plan for sub in subacts)
        return None

    @property
    def costo_total(self):
        return sum(sub.costo_total for sub in self.subactividades.all())


class TipoRecurso(models.Model):
    nombre = models.CharField(max_length=50, unique=True)  # Humano, Material, Equipamiento, Licencia
    unidad_medida = models.CharField(max_length=30, default='Horas')

    def __str__(self):
        return self.nombre


class Recurso(models.Model):
    tipo = models.ForeignKey(TipoRecurso, on_delete=models.PROTECT, related_name='recursos')
    nombre = models.CharField(max_length=120)
    cargo_o_detalle = models.CharField(max_length=120, blank=True, default='')
    tarifa_por_hora = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('25.00'))
    jornada_diaria_horas = models.DecimalField(max_digits=4, decimal_places=1, default=Decimal('8.0'))
    disponible = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombre} ({self.tipo.nombre} - ${self.tarifa_por_hora}/h)"


class Subactividad(models.Model):
    ESTADOS = [
        ('PENDIENTE', 'Pendiente'),
        ('EN_PROGRESO', 'En Progreso'),
        ('COMPLETADA', 'Completada'),
        ('ATRASADA', 'Atrasada'),
    ]

    actividad = models.ForeignKey(Actividad, on_delete=models.CASCADE, related_name='subactividades')
    codigo = models.CharField(max_length=20)  # Ej. 1.1.1, 1.1.2
    nombre = models.CharField(max_length=150)
    peso_porcentual = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('50.00'))  # Regla 100%
    duracion_dias = models.PositiveIntegerField(default=5)
    
    # Línea base (Planificada)
    fecha_inicio_plan = models.DateField()
    fecha_fin_plan = models.DateField()
    
    # Avance Real
    fecha_inicio_real = models.DateField(null=True, blank=True)
    fecha_fin_real = models.DateField(null=True, blank=True)
    porcentaje_avance = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    
    costo_fijo = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    es_hito = models.BooleanField(default=False)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')
    orden = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['orden', 'codigo']
        unique_together = ('actividad', 'codigo')

    def __str__(self):
        return f"{self.codigo} {self.nombre}"

    @property
    def costo_recursos(self):
        costo = Decimal('0.00')
        for asignacion in self.asignaciones.all():
            costo += asignacion.costo_asignacion
        return costo

    @property
    def costo_total(self):
        return self.costo_fijo + self.costo_recursos

    @property
    def esta_atrasada(self):
        hoy = timezone.now().date()
        if self.porcentaje_avance < 100 and self.fecha_fin_plan < hoy:
            return True
        return False


class AsignacionRecurso(models.Model):
    subactividad = models.ForeignKey(Subactividad, on_delete=models.CASCADE, related_name='asignaciones')
    recurso = models.ForeignKey(Recurso, on_delete=models.CASCADE, related_name='asignaciones')
    horas_asignadas = models.DecimalField(max_digits=6, decimal_places=1, default=Decimal('40.0'))
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()

    class Meta:
        unique_together = ('subactividad', 'recurso')

    def __str__(self):
        return f"{self.recurso.nombre} -> {self.subactividad.codigo} ({self.horas_asignadas} hrs)"

    @property
    def costo_asignacion(self):
        return Decimal(str(self.horas_asignadas)) * self.recurso.tarifa_por_hora


class Precedencia(models.Model):
    TIPOS = [
        ('FS', 'Fin a Inicio (FS)'),
        ('SS', 'Inicio a Inicio (SS)'),
        ('FF', 'Fin a Fin (FF)'),
        ('SF', 'Inicio a Fin (SF)'),
    ]

    tarea_origen = models.ForeignKey(
        Subactividad, on_delete=models.CASCADE, related_name='precedencias_salientes'
    )
    tarea_destino = models.ForeignKey(
        Subactividad, on_delete=models.CASCADE, related_name='precedencias_entrantes'
    )
    tipo = models.CharField(max_length=2, choices=TIPOS, default='FS')
    lag_dias = models.IntegerField(default=0, help_text="Desfase en días (positivo=lag, negativo=lead)")

    class Meta:
        unique_together = ('tarea_origen', 'tarea_destino')

    def clean(self):
        if self.tarea_origen_id == self.tarea_destino_id:
            raise ValidationError("Una tarea no puede depender de sí misma.")

    def __str__(self):
        return f"{self.tarea_origen.codigo} -> {self.tarea_destino.codigo} [{self.tipo} {self.lag_dias}d]"


class Hito(models.Model):
    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, related_name='hitos')
    subactividad = models.ForeignKey(
        Subactividad, on_delete=models.SET_NULL, null=True, blank=True, related_name='hitos_asociados'
    )
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True, default='')
    fecha_programada = models.DateField()
    fecha_cumplimiento = models.DateField(null=True, blank=True)
    cumplido = models.BooleanField(default=False)

    class Meta:
        ordering = ['fecha_programada']

    def __str__(self):
        estado = "✓ Cumplido" if self.cumplido else "⏳ Pendiente"
        return f"Hito: {self.nombre} ({self.fecha_programada}) [{estado}]"


# ==========================================
# MOTOR CONFIGURABLE DE KPIS (Indicador E)
# ==========================================
class KPIConfig(models.Model):
    TIPOS = [
        ('PROYECTO', 'KPI de Proyecto e Hitos'),
        ('CAMBIO', 'KPI de Gestión del Cambio'),
    ]
    SEMAFOROS = [
        ('VERDE', 'Verde (En Meta)'),
        ('AMARILLO', 'Amarillo (Alerta)'),
        ('ROJO', 'Rojo (Crítico)'),
    ]

    codigo = models.CharField(max_length=30, unique=True)
    nombre = models.CharField(max_length=120)
    tipo = models.CharField(max_length=10, choices=TIPOS)
    descripcion = models.TextField(blank=True, default='')
    formula_expresion = models.CharField(max_length=200, help_text="Expresión o fórmula paramétrica")
    unidad = models.CharField(max_length=20, default='%')
    meta = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('100.00'))
    umbral_verde = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('90.00'))
    umbral_amarillo = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('75.00'))
    umbral_rojo = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('50.00'))
    es_mayor_mejor = models.BooleanField(default=True, help_text="True si un valor más alto es positivo (ej. avance)")
    orden = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['tipo', 'orden', 'codigo']

    def __str__(self):
        return f"[{self.tipo}] {self.codigo} - {self.nombre}"


class KPIRegistro(models.Model):
    kpi = models.ForeignKey(KPIConfig, on_delete=models.CASCADE, related_name='registros')
    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, related_name='kpi_registros')
    valor_actual = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    fecha_registro = models.DateTimeField(default=timezone.now)
    semaforo = models.CharField(max_length=10, choices=KPIConfig.SEMAFOROS, default='VERDE')
    observaciones = models.CharField(max_length=250, blank=True, default='')

    class Meta:
        ordering = ['-fecha_registro']

    def __str__(self):
        return f"{self.kpi.codigo}: {self.valor_actual}{self.kpi.unidad} ({self.semaforo})"


# ==========================================
# GESTIÓN DEL CAMBIO (Indicador F - 10 Etapas)
# ==========================================
class SolicitudCambio(models.Model):
    PRIORIDADES = [
        ('ALTA', 'Alta'),
        ('MEDIA', 'Media'),
        ('BAJA', 'Baja'),
    ]
    ESTADOS = [
        ('REGISTRADA', '1. Registrada'),
        ('EN_EVALUACION', '2. En Evaluación'),
        ('EN_COMITE', '3. En Comité CCB'),
        ('APROBADA', '4. Aprobada'),
        ('EN_PLANIFICACION', '5. En Planificación'),
        ('EN_EJECUCION', '6. En Ejecución'),
        ('EN_VERIFICACION', '7. En Verificación'),
        ('CERRADA_ADOPCION', '8. Cerrada / Adopción'),
        ('RECHAZADA', 'Rechazada'),
    ]
    ETAPAS_10 = [
        (1, '1. Identificación y Registro'),
        (2, '2. Clasificación y Asignación'),
        (3, '3. Análisis de Impacto Inicial'),
        (4, '4. Evaluación Técnica y de Costos'),
        (5, '5. Revisión por Comité de Cambios (CCB)'),
        (6, '6. Decisión (Aprobación / Rechazo)'),
        (7, '7. Planificación e Integración'),
        (8, '8. Ejecución y Propagación'),
        (9, '9. Verificación y Cierre'),
        (10, '10. Adopción Cultural y Medición'),
    ]

    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, related_name='solicitudes_cambio')
    codigo = models.CharField(max_length=30, unique=True)  # Ej. RFC-001
    titulo = models.CharField(max_length=180)
    descripcion = models.TextField()
    justificacion = models.TextField()
    solicitante = models.CharField(max_length=120)
    responsable = models.CharField(max_length=120, default='Comité de Cambios')
    prioridad = models.CharField(max_length=10, choices=PRIORIDADES, default='MEDIA')
    etapa_actual = models.PositiveSmallIntegerField(choices=ETAPAS_10, default=1)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='REGISTRADA')
    
    # Impacto para la propagación automática
    impacto_plazo_dias = models.IntegerField(default=0, help_text="Días que añade al cronograma")
    impacto_costo = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), help_text="Costo monetario adicional")
    subactividad_afectada = models.ForeignKey(
        Subactividad, on_delete=models.SET_NULL, null=True, blank=True, related_name='cambios_asociados'
    )
    propagado = models.BooleanField(default=False, help_text="Indica si el impacto ya fue aplicado al Gantt y Costos")

    fecha_solicitud = models.DateField(default=timezone.now)
    fecha_resolucion = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['-fecha_solicitud', 'codigo']

    def __str__(self):
        return f"{self.codigo} - {self.titulo} [{self.get_estado_display()}]"


class HistorialCambio(models.Model):
    solicitud = models.ForeignKey(SolicitudCambio, on_delete=models.CASCADE, related_name='historial')
    etapa = models.PositiveSmallIntegerField(choices=SolicitudCambio.ETAPAS_10)
    usuario = models.CharField(max_length=120, default='Sistema / Okta User')
    comentario = models.TextField()
    fecha_evento = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['fecha_evento']

    def __str__(self):
        return f"{self.solicitud.codigo} - Etapa {self.etapa} ({self.fecha_evento.strftime('%d/%m/%Y')})"
