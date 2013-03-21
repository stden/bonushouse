from django.shortcuts import get_object_or_404, redirect
from advertising.models import Banner, BannerClicks
# Create your views here.

def banner_click(request, banner_id):
    banner_id = int(banner_id)
    banner = get_object_or_404(Banner, pk=banner_id)
    banner_click = BannerClicks(banner=banner, visitor_info=request.session['visitor_info'])
    banner_click.save()
    banner.clicks = BannerClicks.objects.filter(banner=banner).count()
    banner.save()
    return redirect(banner.url)