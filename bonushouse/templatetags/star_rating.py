from django import template
import re
from django.utils.encoding import smart_str

register = template.Library()
kw_pat = re.compile(r'^(?P<key>[\w]+)=(?P<value>.+)$')

class StarRatingNode(template.Node):
    error_msg = 'Syntax error.'
    def __init__(self, parser, token):
        self.options = {
            'class':'star-rating',
            'name': 'star-rating',
            'count':5,
            'read_only':True,
            'initial': 3
        }
        bits = token.split_contents()
        for bit in bits[1:]:
            m = kw_pat.match(bit)
            if not m:
                raise template.TemplateSyntaxError(self.error_msg)
            key = smart_str(m.group('key'))
            expr = parser.compile_filter(m.group('value'))
            self.options[key] = expr
    def render(self, context):
        if not self.options.get('name'):
            raise template.TemplateSyntaxError('Name is not set')
        options = self.options.copy()
        for key in options.keys():
            if isinstance(options[key], template.base.FilterExpression):
                options[key] = options[key].resolve(context)
        result = ''
        for i in range(1, options['count']+1):
            result += '<input type="radio" name="%s" class="%s" value="%s" %s %s />' % (
                options['name'],
                options['class'],
                i,
                ('disabled="disabled"' if options['read_only'] else ''),
                ('checked="checked"' if i == options['initial'] else '')
            )
        return result


@register.tag
def star_rating(parser, token):
    return StarRatingNode(parser, token)