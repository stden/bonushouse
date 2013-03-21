import logging, sys
from django import template
from common.models import Categories
register = template.Library()
from django.template import Library, Node, NodeList, TemplateSyntaxError

logger = logging.getLogger('common')

class CategoryNodeBase(Node):
    """
    A Node that renders safely
    """
    nodelist_empty = NodeList()

    def render(self, context):
        try:
            return self._render(context)
        except Exception:
            logger.error('Category tag failed:', exc_info=sys.exc_info())
            return self.nodelist_empty.render(context)

    def _render(self, context):
        raise NotImplemented()

class CategoryNode(CategoryNodeBase):
    child_nodelists = ('nodelist_file', 'nodelist_empty')
    error_msg = ('Syntax error. Expected: ``getcategory category_id '
                 'as var``')

    def __init__(self, parser, token):
        bits = token.split_contents()
        if len(bits) < 3 or bits[-2] != 'as':
            raise TemplateSyntaxError(self.error_msg)
        self.category_id = parser.compile_filter(bits[1])
        self.as_var = bits[-1]
        self.nodelist_file = parser.parse(('empty', 'endgetcategory',))
        if parser.next_token().contents == 'empty':
            self.nodelist_empty = parser.parse(('endgetcategory',))
            parser.delete_first_token()

    def _render(self, context):
        try:
            category = Categories.objects.get(pk=self.category_id.resolve(context))
        except Categories.DoesNotExist:
            return self.nodelist_empty.render(context)
        context.push()
        context[self.as_var] = category
        output = self.nodelist_file.render(context)
        context.pop()
        return output

    def __repr__(self):
        return "<CategoryNode>"

    def __iter__(self):
        for node in self.nodelist_file:
            yield node
        for node in self.nodelist_empty:
            yield node


@register.tag
def getcategory(parser, token):
    return CategoryNode(parser, token)
