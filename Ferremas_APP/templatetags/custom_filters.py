from django import template
from babel.numbers import format_currency
register = template.Library()


@register.filter(name='formato_moneda') # Decorador para registrar el filtro
def formato_moneda(value, currency='CLP'): # Función que recibe el valor y la moneda
    if value is None:  # Si el valor es nulo
        return ''  # Retornar un string vacío
    return format_currency(value, currency, locale='es_CL') # Formatear el valor a moneda con el formato chileno

@register.filter(name='add_class') # Decorador para registrar el filtro
def add_class(value, arg): # Función que recibe el valor y la clase
    return value.as_widget(attrs={'class': arg}) # Agregar la clase al widget del valor