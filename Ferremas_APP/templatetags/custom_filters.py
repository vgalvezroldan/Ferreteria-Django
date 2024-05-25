from django import template

register = template.Library()



@register.filter(name='replace_comma')
def replace_comma(value):
    return value.replace(",", ".")

@register.filter(name='add_class')
def add_class(value, arg):
    return value.as_widget(attrs={'class': arg})