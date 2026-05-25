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
