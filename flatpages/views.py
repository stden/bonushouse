from flatpages.models import FlatPage
from django.template import loader, RequestContext
from django.shortcuts import get_object_or_404, render_to_response
from django.http import Http404, HttpResponse, HttpResponsePermanentRedirect
from django.conf import settings
from django.core.xheaders import populate_xheaders
from django.utils.safestring import mark_safe
from django.views.decorators.csrf import csrf_protect

DEFAULT_TEMPLATE = 'flatpages/default.html'

# This view is called from FlatpageFallbackMiddleware.process_response
# when a 404 is raised, which often means CsrfViewMiddleware.process_view
# has not been called even if CsrfViewMiddleware is installed. So we need
# to use @csrf_protect, in case the template needs {% csrf_token %}.
# However, we can't just wrap this view; if no matching flatpage exists,
# or a redirect is required for authentication, the 404 needs to be returned
# without any CSRF checks. Therefore, we only
# CSRF protect the internal implementation.

def render_flatpage(request, page_id):
    page_id = int(page_id)
    page = get_object_or_404(FlatPage, pk=page_id)
    context = RequestContext(request)
    context['flatpage'] = page
    template_name = page.template_name if page.template_name else DEFAULT_TEMPLATE
    return render_to_response(template_name, context)