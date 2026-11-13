from django.utils import timezone
import pytz
from django.conf import settings

class TimezoneMiddleware(object):
    def process_request(self, request):
        timezone.activate(pytz.timezone(settings.TIME_ZONE))