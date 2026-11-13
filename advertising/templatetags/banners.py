from django import template
from advertising.models import Banner, BannerImpressions
register = template.Library()
from django.template import Template, Context

class BannerNode(template.Node):
    def __init__(self, region_id, visitor_info):
        self.region_id = region_id
        self.visitor_info = visitor_info
    def render(self, context):
        banners_list = Banner.objects.filter(is_published=True, region=self.region_id).order_by('?')
        if banners_list.count():
            banner = banners_list[0]
            visitor_info = self.visitor_info.resolve(context)
            impression = BannerImpressions(banner=banner, visitor_info=visitor_info)
            impression.save()
            banner.impressions = BannerImpressions.objects.filter(banner=banner).count()
            banner.save()
            template = Template(banner.code)
            context = Context({'LINK': banner.get_click_url()})
            result = template.render(context)
            return result
        else:
            return ''


def show_banner(parser, token):
    tag_name, region_id, visitor_info = token.split_contents()
    region_id = region_id[1:-1]
    visitor_info = parser.compile_filter(visitor_info)
    return BannerNode(region_id, visitor_info)

register.tag('show_banner', show_banner)
