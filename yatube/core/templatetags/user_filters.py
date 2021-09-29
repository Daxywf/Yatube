from django import template

register = template.Library()


@register.filter
def addclass(field, css):
    return field.as_widget(attrs={"class": css})


@register.filter
def cutter30(line):
    return line[0:30]
