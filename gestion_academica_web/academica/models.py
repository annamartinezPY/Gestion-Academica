"""
Modelos Django que mapean la base de datos existente (managed=False).
Django no crea ni modifica estas tablas; ya existen desde el CLI.
"""
from django.db import models


class Rol(models.Model):
    nombre = models.TextField(unique=True)
    descripcion = models.TextField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'roles'

    def __str__(self):
        return self.nombre


class Usuario(models.Model):
    nombre = models.TextField()
    apellido = models.TextField()
    email = models.TextField(unique=True)
    password = models.TextField()
    rol = models.ForeignKey(Rol, on_delete=models.PROTECT, db_column='rol_id')
    activo = models.IntegerField(default=1)
    fecha_creacion = models.TextField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'usuarios'

    def __str__(self):
        return f'{self.nombre} {self.apellido}'

    @property
    def nombre_completo(self):
        return f'{self.nombre} {self.apellido}'

    @property
    def esta_activo(self):
        return bool(self.activo)


class Modalidad(models.Model):
    nombre = models.TextField(unique=True)
    descripcion = models.TextField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'modalidades'

    def __str__(self):
        return self.nombre


class Curso(models.Model):
    nombre = models.TextField()
    descripcion = models.TextField(null=True, blank=True)
    modalidad = models.ForeignKey(Modalidad, on_delete=models.PROTECT, db_column='modalidad_id')
    horas_totales = models.IntegerField(default=0)
    tarifa_estudiante = models.FloatField(default=0.0)
    activo = models.IntegerField(default=1)
    condiciones_ingreso = models.TextField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'cursos'

    def __str__(self):
        return self.nombre


class Cohorte(models.Model):
    nombre = models.TextField()
    curso = models.ForeignKey(Curso, on_delete=models.PROTECT, db_column='curso_id', related_name='cohortes')
    fecha_inicio = models.TextField()
    fecha_fin = models.TextField()
    cupo_maximo = models.IntegerField(default=30)
    activo = models.IntegerField(default=1)

    class Meta:
        managed = False
        db_table = 'cohortes'

    def __str__(self):
        return f'{self.nombre} — {self.curso}'

    @property
    def inscriptos_activos(self):
        return self.inscripciones.filter(estado='activa').count()

    @property
    def cupo_disponible(self):
        return self.inscriptos_activos < self.cupo_maximo

    @property
    def ocupacion_pct(self):
        if self.cupo_maximo == 0:
            return 0
        return round(self.inscriptos_activos / self.cupo_maximo * 100, 1)


class Docente(models.Model):
    usuario = models.OneToOneField(
        Usuario, on_delete=models.CASCADE,
        db_column='usuario_id', related_name='docente'
    )
    especialidad = models.TextField(null=True, blank=True)
    tarifa_hora = models.FloatField(default=0.0)

    class Meta:
        managed = False
        db_table = 'docentes'

    def __str__(self):
        return str(self.usuario)

    @property
    def nombre_completo(self):
        return self.usuario.nombre_completo


class Estudiante(models.Model):
    usuario = models.OneToOneField(
        Usuario, on_delete=models.CASCADE,
        db_column='usuario_id', related_name='estudiante'
    )
    documento = models.TextField(unique=True, null=True, blank=True)
    telefono = models.TextField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'estudiantes'

    def __str__(self):
        return str(self.usuario)

    @property
    def nombre_completo(self):
        return self.usuario.nombre_completo


class Inscripcion(models.Model):
    estudiante = models.ForeignKey(
        Estudiante, on_delete=models.CASCADE,
        db_column='estudiante_id', related_name='inscripciones'
    )
    cohorte = models.ForeignKey(
        Cohorte, on_delete=models.CASCADE,
        db_column='cohorte_id', related_name='inscripciones'
    )
    fecha_inscripcion = models.TextField(null=True, blank=True)
    estado = models.TextField(default='activa')

    class Meta:
        managed = False
        db_table = 'inscripciones'
        unique_together = [('estudiante', 'cohorte')]

    def __str__(self):
        return f'{self.estudiante} → {self.cohorte}'


class Sesion(models.Model):
    cohorte = models.ForeignKey(
        Cohorte, on_delete=models.CASCADE,
        db_column='cohorte_id', related_name='sesiones'
    )
    docente = models.ForeignKey(
        Docente, on_delete=models.CASCADE,
        db_column='docente_id', related_name='sesiones'
    )
    fecha = models.TextField()
    hora_inicio = models.TextField()
    hora_fin = models.TextField()
    tema = models.TextField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'sesiones'

    def __str__(self):
        return f'{self.fecha} — {self.cohorte}'


class PagoEstudiante(models.Model):
    inscripcion = models.ForeignKey(
        Inscripcion, on_delete=models.CASCADE,
        db_column='inscripcion_id', related_name='pagos'
    )
    monto = models.FloatField()
    fecha_pago = models.TextField(null=True, blank=True)
    metodo_pago = models.TextField(default='efectivo')
    estado = models.TextField(default='pagado')
    observacion = models.TextField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'pagos_estudiantes'

    def __str__(self):
        return f'${self.monto} — {self.inscripcion}'


class PagoDocente(models.Model):
    docente = models.ForeignKey(
        Docente, on_delete=models.CASCADE,
        db_column='docente_id', related_name='pagos'
    )
    cohorte = models.ForeignKey(
        Cohorte, on_delete=models.CASCADE,
        db_column='cohorte_id', related_name='pagos_docentes'
    )
    horas_dictadas = models.FloatField(default=0)
    monto = models.FloatField()
    fecha_pago = models.TextField(null=True, blank=True)
    estado = models.TextField(default='pendiente')
    observacion = models.TextField(null=True, blank=True)
    tipo_pago = models.TextField(default='horas')
    concepto = models.TextField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'pagos_docentes'

    def __str__(self):
        return f'${self.monto} → {self.docente}'


class Asistencia(models.Model):
    sesion = models.ForeignKey(
        Sesion, on_delete=models.CASCADE,
        db_column='sesion_id', related_name='asistencias'
    )
    estudiante = models.ForeignKey(
        Estudiante, on_delete=models.CASCADE,
        db_column='estudiante_id', related_name='asistencias'
    )
    presente = models.IntegerField(default=1)
    observacion = models.TextField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'asistencias'
        unique_together = [('sesion', 'estudiante')]


class Configuracion(models.Model):
    clave = models.TextField(primary_key=True)
    valor = models.TextField()
    descripcion = models.TextField(null=True, blank=True)
    tipo = models.TextField(default='texto')

    class Meta:
        managed = False
        db_table = 'configuracion'

    def __str__(self):
        return f'{self.clave} = {self.valor}'
