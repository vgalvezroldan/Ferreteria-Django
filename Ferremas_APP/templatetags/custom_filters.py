from django import template
from babel.numbers import format_currency
register = template.Library()


@register.filter(name='formato_moneda')
def formato_moneda(value, currency='CLP'):
    if value is None:
        return ''
    return format_currency(value, currency, locale='es_CL')

@register.filter(name='replace_comma')
def replace_comma(value):
    return value.replace(",", ".")

@register.filter(name='add_class')
def add_class(value, arg):
    return value.as_widget(attrs={'class': arg})