from django.http import Http404
from django.conf import settings
from seo.models import ModelFriendlyUrl
from seo.views import seo_model_view

class  FriendlyUrlFallbackMiddleware(object):
    def process_response(self, request, response):
        if response.status_code != 404:
            return response # No need to check for a flatpage for non-404 responses.
        try:
            path_info = request.path_info
            url = ModelFriendlyUrl.objects.get(friendly_url=path_info)
            view = url.content_object.get_view_for_model()
            return seo_model_view(request, view, url.object_id)
        # Return the original response if any errors happened. Because this
        # is a middleware, we can't assume the errors will be caught elsewhere.
        except ModelFriendlyUrl.DoesNotExist:
            return response
        except:
            if settings.DEBUG:
                raise
            return response
