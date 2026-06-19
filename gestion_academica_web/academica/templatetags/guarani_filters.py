from django import template

register = template.Library()


@register.filter
def guarani(value):
    """Formatea un número como moneda Guaraní: ₲ 1.500.000"""
    try:
        n = int(round(float(value)))
        formatted = f"{n:,}".replace(",", ".")
        return f"₲ {formatted}"
    except (ValueError, TypeError):
        return "₲ 0"


@register.filter
def guarani_short(value):
    """Versión corta sin símbolo: 1.500.000"""
    try:
        n = int(round(float(value)))
        return f"{n:,}".replace(",", ".")
    except (ValueError, TypeError):
        return "0"


@register.filter
def is_pdf(filefield):
    """True si el FileField (o string) termina en .pdf — para mostrar visor inline."""
    if not filefield:
        return False
    nombre = getattr(filefield, 'name', None) or str(filefield)
    return nombre.lower().endswith('.pdf')


@register.filter
def is_image(filefield):
    """True si el archivo es una imagen — para mostrar como <img> inline."""
    if not filefield:
        return False
    nombre = getattr(filefield, 'name', None) or str(filefield)
    n = nombre.lower()
    return any(n.endswith(ext) for ext in ('.jpg', '.jpeg', '.png', '.webp', '.gif'))
