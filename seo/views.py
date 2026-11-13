from django.views.decorators.csrf import csrf_protect
# Create your views here.


@csrf_protect
def seo_model_view(request, view, object_id):
    return view(request, object_id)