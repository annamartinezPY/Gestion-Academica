from django.shortcuts import render
from django.db.models import Count, Sum, Q
from ..decorators import rol_required, get_usuario_sesion
from ..models import Curso, Cohorte, Docente, Inscripcion, PagoEstudiante, PagoDocente, Sesion


@rol_required('admin')
def index(request):
    # Tarjetas resumen
    total_ingresos = PagoEstudiante.objects.filter(
        ~Q(estado='anulado')
    ).aggregate(t=Sum('monto'))['t'] or 0

    total_egresos = PagoDocente.objects.filter(
        ~Q(estado='anulado')
    ).aggregate(t=Sum('monto'))['t'] or 0

    pendientes_doc = PagoDocente.objects.filter(
        estado='pendiente'
    ).aggregate(t=Sum('monto'))['t'] or 0

    # Top 5 cursos por inscriptos
    top_cursos = Curso.objects.annotate(
        total_inscriptos=Count(
            'cohortes__inscripciones',
            filter=Q(cohortes__inscripciones__estado='activa')
        )
    ).filter(activo=1).order_by('-total_inscriptos')[:5]

    # Cohortes activas con ocupación
    cohortes = Cohorte.objects.filter(activo=1).select_related('curso').annotate(
        inscriptos=Count('inscripciones', filter=Q(inscripciones__estado='activa'))
    ).order_by('-fecha_inicio')[:8]

    # Docentes con más sesiones
    top_docentes = Docente.objects.select_related('usuario').annotate(
        total_sesiones=Count('sesiones'),
        total_cobrado=Sum('pagos__monto', filter=~Q(pagos__estado='anulado'))
    ).order_by('-total_sesiones')[:5]

    # Inscripciones por mes (últimos 6 meses)
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT strftime('%Y-%m', fecha_inscripcion) as mes, COUNT(*) as total
            FROM inscripciones
            WHERE fecha_inscripcion >= date('now', '-6 months')
            GROUP BY mes ORDER BY mes
        """)
        inscripciones_mes = cursor.fetchall()

    return render(request, 'reportes/index.html', {
        'total_ingresos': total_ingresos,
        'total_egresos': total_egresos,
        'balance': total_ingresos - total_egresos,
        'pendientes_doc': pendientes_doc,
        'top_cursos': top_cursos,
        'cohortes': cohortes,
        'top_docentes': top_docentes,
        'inscripciones_mes': inscripciones_mes,
        'usuario': get_usuario_sesion(request),
    })