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
    must_change_password = models.IntegerField(default=0)

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


class Institucion(models.Model):
    nombre = models.TextField()
    email = models.TextField(null=True, blank=True)
    telefono = models.TextField(null=True, blank=True)
    direccion = models.TextField(null=True, blank=True)
    ciudad = models.TextField(null=True, blank=True)
    imagen = models.FileField(upload_to='instituciones/', null=True, blank=True)
    activo = models.IntegerField(default=1)
    modalidades = models.ManyToManyField(
        Modalidad,
        through='InstitucionModalidad',
        related_name='instituciones',
    )

    class Meta:
        managed = False
        db_table = 'instituciones'

    def __str__(self):
        return self.nombre


class InstitucionModalidad(models.Model):
    institucion = models.ForeignKey(Institucion, on_delete=models.CASCADE, db_column='institucion_id')
    modalidad = models.ForeignKey(Modalidad, on_delete=models.CASCADE, db_column='modalidad_id')

    class Meta:
        managed = False
        db_table = 'institucion_modalidades'
        unique_together = [('institucion', 'modalidad')]


class CondicionInscripcion(models.Model):
    nombre = models.TextField()
    descripcion = models.TextField(null=True, blank=True)
    texto = models.TextField(null=True, blank=True)  # columna legacy, no usar en UI nueva
    activo = models.IntegerField(default=1)

    class Meta:
        managed = False
        db_table = 'condiciones_inscripcion'

    def __str__(self):
        return self.nombre or self.texto or ''


class Curso(models.Model):
    codigo = models.TextField(null=True, blank=True, unique=True)
    nombre = models.TextField()
    descripcion = models.TextField(null=True, blank=True)
    modalidad = models.ForeignKey(Modalidad, on_delete=models.PROTECT, db_column='modalidad_id')
    institucion = models.ForeignKey(
        Institucion, on_delete=models.SET_NULL,
        db_column='institucion_id', null=True, blank=True,
        related_name='cursos',
    )
    horas_totales = models.IntegerField(default=0)
    tarifa_estudiante = models.FloatField(default=0.0)
    activo = models.IntegerField(default=1)
    condiciones_ingreso = models.TextField(null=True, blank=True)
    condiciones = models.ManyToManyField(
        CondicionInscripcion,
        through='CursoCondicion',
        related_name='cursos',
        blank=True,
    )

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
    dias_clase = models.TextField(null=True, blank=True)
    carga_horaria_diaria = models.FloatField(default=0)
    docente = models.ForeignKey(
        'Docente', on_delete=models.SET_NULL,
        db_column='docente_id', null=True, blank=True,
        related_name='cohortes_a_cargo',
    )

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
        return max(0, self.cupo_maximo - self.inscriptos_activos)

    @property
    def ocupacion_pct(self):
        if self.cupo_maximo == 0:
            return 0
        return round(self.inscriptos_activos / self.cupo_maximo * 100, 1)

    @property
    def dias_lista(self):
        if not self.dias_clase:
            return []
        return [d.strip() for d in self.dias_clase.split(',')]

    @property
    def dias_abreviados(self):
        abrev = {'Lunes':'Lun','Martes':'Mar','Miércoles':'Mié',
                 'Jueves':'Jue','Viernes':'Vie','Sábado':'Sáb','Domingo':'Dom'}
        return ' · '.join(abrev.get(d, d) for d in self.dias_lista)


class Docente(models.Model):
    usuario = models.OneToOneField(
        Usuario, on_delete=models.CASCADE,
        db_column='usuario_id', related_name='docente'
    )
    especialidad = models.TextField(null=True, blank=True)
    tarifa_hora = models.FloatField(default=0.0)
    telefono = models.TextField(null=True, blank=True)
    cedula = models.TextField(null=True, blank=True)
    ruc = models.TextField(null=True, blank=True)
    foto = models.FileField(upload_to='docentes/', null=True, blank=True)
    biografia = models.TextField(null=True, blank=True)
    areas_experiencia = models.TextField(null=True, blank=True)
    trayectoria_academica = models.TextField(null=True, blank=True)
    linkedin_url = models.TextField(null=True, blank=True)
    otras_redes = models.TextField(null=True, blank=True)
    nivel_educativo = models.ForeignKey(
        'NivelEducativo', on_delete=models.SET_NULL,
        db_column='nivel_educativo_id', null=True, blank=True,
        related_name='docentes',
    )
    legajo_interno = models.TextField(null=True, blank=True)
    tipo_contratacion = models.ForeignKey(
        'TipoContratacion', on_delete=models.SET_NULL,
        db_column='tipo_contratacion_id', null=True, blank=True,
        related_name='docentes',
    )

    class Meta:
        managed = False
        db_table = 'docentes'

    @property
    def areas_experiencia_lista(self):
        if not self.areas_experiencia:
            return []
        return [a.strip() for a in self.areas_experiencia.split(',') if a.strip()]

    @property
    def otras_redes_lista(self):
        """Devuelve lista de dicts {label, url} parseando líneas 'label|url' o solo 'url'."""
        if not self.otras_redes:
            return []
        out = []
        for raw in self.otras_redes.splitlines():
            raw = raw.strip()
            if not raw:
                continue
            if '|' in raw:
                label, url = raw.split('|', 1)
                out.append({'label': label.strip(), 'url': url.strip()})
            else:
                out.append({'label': raw, 'url': raw})
        return out

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
    fecha_nacimiento = models.TextField(null=True, blank=True)
    direccion_residencia = models.TextField(null=True, blank=True)

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
    ESTADO_PLANIFICADA = 'planificada'
    ESTADO_EN_CURSO = 'en_curso'
    ESTADO_FINALIZADA = 'finalizada'
    ESTADO_CANCELADA = 'cancelada'

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
    hora_inicio_real = models.TextField(null=True, blank=True)
    hora_fin_real = models.TextField(null=True, blank=True)
    estado = models.TextField(default='planificada')

    class Meta:
        managed = False
        db_table = 'sesiones'

    def __str__(self):
        return f'{self.fecha} — {self.cohorte}'

    @property
    def es_hoy(self):
        from datetime import date
        try:
            return self.fecha[:10] == date.today().isoformat()
        except Exception:
            return False

    @property
    def horas_dictadas(self):
        """Horas reales dictadas según marcas inicio/fin. 0 si no finalizada."""
        if not (self.hora_inicio_real and self.hora_fin_real):
            return 0
        try:
            from datetime import datetime
            fmt = '%H:%M'
            t1 = datetime.strptime(self.hora_inicio_real[:5], fmt)
            t2 = datetime.strptime(self.hora_fin_real[:5], fmt)
            delta = (t2 - t1).total_seconds() / 3600
            return round(delta, 2) if delta > 0 else 0
        except Exception:
            return 0

    @property
    def verificada(self):
        return self.estado == 'finalizada' and self.hora_inicio_real and self.hora_fin_real


class PagoEstudiante(models.Model):
    ESTADO_PENDIENTE   = 'pendiente'
    ESTADO_EN_REVISION = 'en_revision'
    ESTADO_APROBADO    = 'aprobado'
    ESTADO_RECHAZADO   = 'rechazado'
    ESTADO_ANULADO     = 'anulado'

    inscripcion = models.ForeignKey(
        Inscripcion, on_delete=models.CASCADE,
        db_column='inscripcion_id', related_name='pagos'
    )
    monto = models.FloatField()
    fecha_pago = models.TextField(null=True, blank=True)
    fecha_vencimiento = models.TextField(null=True, blank=True)
    metodo_pago = models.TextField(default='efectivo')
    estado = models.TextField(default='pendiente')
    observacion = models.TextField(null=True, blank=True)
    numero_recibo = models.TextField(null=True, blank=True)
    referencia = models.TextField(null=True, blank=True)
    revisado_por = models.ForeignKey(
        'Usuario', on_delete=models.SET_NULL,
        null=True, blank=True, db_column='revisado_por',
        related_name='pagos_revisados',
    )
    fecha_revision = models.TextField(null=True, blank=True)
    motivo_rechazo = models.TextField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'pagos_estudiantes'

    @property
    def esta_vencido(self):
        if not self.fecha_vencimiento or self.estado == 'pagado':
            return False
        from datetime import date
        try:
            venc = date.fromisoformat(self.fecha_vencimiento[:10])
            return date.today() > venc
        except ValueError:
            return False

    @property
    def vence_pronto(self):
        """True si vence en los próximos 5 días y no está pagado."""
        if not self.fecha_vencimiento or self.estado == 'pagado':
            return False
        from datetime import date, timedelta
        try:
            venc = date.fromisoformat(self.fecha_vencimiento[:10])
            return date.today() <= venc <= date.today() + timedelta(days=5)
        except ValueError:
            return False

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
    hora_marca = models.TextField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'asistencias'
        unique_together = [('sesion', 'estudiante')]


class Material(models.Model):
    cohorte = models.ForeignKey(
        Cohorte, on_delete=models.CASCADE,
        db_column='cohorte_id', related_name='materiales'
    )
    docente = models.ForeignKey(
        Docente, on_delete=models.SET_NULL,
        db_column='docente_id', null=True, blank=True,
        related_name='materiales',
    )
    titulo = models.TextField()
    descripcion = models.TextField(null=True, blank=True)
    archivo = models.FileField(upload_to='materiales/', null=True, blank=True)
    url_externa = models.TextField(null=True, blank=True)
    fecha_publicacion = models.TextField(null=True, blank=True)
    activo = models.IntegerField(default=1)

    class Meta:
        managed = False
        db_table = 'materiales'

    def __str__(self):
        return self.titulo


class Tarea(models.Model):
    cohorte = models.ForeignKey(
        Cohorte, on_delete=models.CASCADE,
        db_column='cohorte_id', related_name='tareas'
    )
    docente = models.ForeignKey(
        Docente, on_delete=models.SET_NULL,
        db_column='docente_id', null=True, blank=True,
        related_name='tareas',
    )
    titulo = models.TextField()
    descripcion = models.TextField(null=True, blank=True)
    archivo_consigna = models.FileField(upload_to='tareas/consignas/', null=True, blank=True)
    fecha_entrega = models.TextField(null=True, blank=True)
    puntos_maximos = models.IntegerField(default=100)
    fecha_creacion = models.TextField(null=True, blank=True)
    activo = models.IntegerField(default=1)

    class Meta:
        managed = False
        db_table = 'tareas'

    def __str__(self):
        return self.titulo

    @property
    def esta_vencida(self):
        if not self.fecha_entrega:
            return False
        from datetime import date
        try:
            return date.today() > date.fromisoformat(self.fecha_entrega[:10])
        except Exception:
            return False


class EntregaTarea(models.Model):
    tarea = models.ForeignKey(
        Tarea, on_delete=models.CASCADE,
        db_column='tarea_id', related_name='entregas'
    )
    estudiante = models.ForeignKey(
        Estudiante, on_delete=models.CASCADE,
        db_column='estudiante_id', related_name='entregas_tareas'
    )
    archivo = models.FileField(upload_to='tareas/entregas/', null=True, blank=True)
    comentario = models.TextField(null=True, blank=True)
    fecha_entrega = models.TextField(null=True, blank=True)
    nota = models.FloatField(null=True, blank=True)
    feedback = models.TextField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'entregas_tareas'
        unique_together = [('tarea', 'estudiante')]


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


class CursoCondicion(models.Model):
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, db_column='curso_id')
    condicion = models.ForeignKey(CondicionInscripcion, on_delete=models.CASCADE, db_column='condicion_id')

    class Meta:
        managed = False
        db_table = 'curso_condiciones'
        unique_together = [('curso', 'condicion')]


class NivelEducativo(models.Model):
    nombre = models.TextField(unique=True)
    descripcion = models.TextField(null=True, blank=True)
    activo = models.IntegerField(default=1)

    class Meta:
        managed = False
        db_table = 'niveles_educativos'

    def __str__(self):
        return self.nombre


class TipoContratacion(models.Model):
    nombre = models.TextField(unique=True)
    descripcion = models.TextField(null=True, blank=True)
    activo = models.IntegerField(default=1)

    class Meta:
        managed = False
        db_table = 'tipos_contratacion'

    def __str__(self):
        return self.nombre


class DocenteInstitucion(models.Model):
    docente = models.ForeignKey(
        'Docente', on_delete=models.CASCADE,
        db_column='docente_id', related_name='instituciones_rel'
    )
    institucion = models.ForeignKey(
        Institucion, on_delete=models.CASCADE,
        db_column='institucion_id', related_name='docentes_rel'
    )
    email_institucional = models.TextField(null=True, blank=True)
    nivel_educativo = models.ForeignKey(
        NivelEducativo, on_delete=models.SET_NULL,
        db_column='nivel_educativo_id', null=True, blank=True,
        related_name='docente_instituciones',
    )

    class Meta:
        managed = False
        db_table = 'docente_instituciones'
        unique_together = [('docente', 'institucion')]


class Permiso(models.Model):
    clave = models.TextField(unique=True)
    nombre = models.TextField()
    modulo = models.TextField()

    class Meta:
        managed = False
        db_table = 'permisos'

    def __str__(self):
        return self.nombre


class RolPermiso(models.Model):
    rol = models.ForeignKey(Rol, on_delete=models.CASCADE, db_column='rol_id', related_name='permisos')
    permiso = models.ForeignKey(Permiso, on_delete=models.CASCADE, db_column='permiso_id')

    class Meta:
        managed = False
        db_table = 'rol_permisos'
        unique_together = [('rol', 'permiso')]


class PasswordResetToken(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, db_column='usuario_id')
    token = models.TextField(unique=True)
    expira = models.TextField()
    usado = models.IntegerField(default=0)

    class Meta:
        managed = False
        db_table = 'password_reset_tokens'


class Notificacion(models.Model):
    TIPO_INFO    = 'info'
    TIPO_SUCCESS = 'success'
    TIPO_WARNING = 'warning'
    TIPO_DANGER  = 'danger'

    usuario = models.ForeignKey(
        Usuario, on_delete=models.CASCADE,
        db_column='usuario_id', related_name='notificaciones',
    )
    titulo = models.TextField()
    mensaje = models.TextField(null=True, blank=True)
    tipo = models.TextField(default='info')
    url = models.TextField(null=True, blank=True)
    leida = models.IntegerField(default=0)
    fecha = models.TextField()

    class Meta:
        managed = False
        db_table = 'notificaciones'
        ordering = ['-fecha', '-id']

    def __str__(self):
        return f'{self.titulo} → {self.usuario_id}'

    @classmethod
    def notificar(cls, usuario_id, titulo, mensaje=None, tipo='info', url=None):
        """Helper para crear notificaciones desde cualquier vista."""
        from datetime import datetime
        if not usuario_id:
            return None
        return cls.objects.create(
            usuario_id=usuario_id,
            titulo=titulo,
            mensaje=mensaje,
            tipo=tipo,
            url=url,
            leida=0,
            fecha=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        )
