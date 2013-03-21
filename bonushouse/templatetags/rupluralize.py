# -*- coding: utf-8 -*-

from django.template import Library, TemplateSyntaxError
from django.template.defaultfilters import stringfilter
register = Library()

@register.filter(is_safe=False)
@stringfilter
def rupluralize(value, endings):
    try:
        value = int(value)
        endings = endings.split(',')
        if value % 100 in (11, 12, 13, 14):
            return endings[2]
        if value % 10 == 1:
            return endings[0]
        if value % 10 in (2, 3, 4):
            return endings[1]
        else:
            return endings[2]
    except:
        raise TemplateSyntaxError