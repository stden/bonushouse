import re
from visitor_tracking.models import VisitorInfo

IP_RE = re.compile('\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}')

def get_ip(request):
    ip_address = request.META.get('HTTP_X_FORWARDED_FOR',
        request.META.get('REMOTE_ADDR', '127.0.0.1'))
    if ip_address:
        # make sure we have one and only one IP
        try:
            ip_address = IP_RE.match(ip_address)
            if ip_address:
                ip_address = ip_address.group(0)
            else:
                # no IP, probably from some dirty proxy or other device
                # throw in some bogus IP
                ip_address = '10.0.0.1'
        except IndexError:
            pass
    return ip_address

class VisitorTrackingMiddleware:
    def process_request(self, request):
        if request.is_ajax(): return
        visitor_info = request.session.get('visitor_info')
        if not visitor_info:
            ip_address = get_ip(request)
            referer = request.META.get('HTTP_REFERER', 'unknown')
            if referer.startswith('http://109.254.82.29') or referer.startswith('http://bonus-house.ru'):
                referer = 'unknown'
            visitor_info = VisitorInfo(ip=ip_address, referer=referer)
            visitor_info.save()
            request.session['visitor_info'] = visitor_info
