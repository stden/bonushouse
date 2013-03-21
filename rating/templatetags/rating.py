from django import template
from django.utils.html import mark_safe
from django.conf import settings

register = template.Library()

@register.filter()
def rating_stars(value):
    if isinstance(value, int):
        value = int(value)
    else:
        value = 0
    i = 0
    result = '<span class="rating-container">'
    while i<5:
        if value > i:
            result += '<img src="%simages/star_full.png" alt="" />' % (settings.STATIC_URL, )
        else:
            result += '<img src="%simages/star_empty.png" alt="" />' % (settings.STATIC_URL, )
        i += 1
    result += '</span>'
    return mark_safe(result)