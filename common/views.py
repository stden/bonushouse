# Create your views here.
from common.models import Categories, UploadedFile
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse

def categories_index(request):
    context = RequestContext(request)
    categories_list = Categories.objects.all()
    context['categories_list'] = categories_list
    return render_to_response('common/categories_index.html', context)

def view_category(request, category_id):
    category_id = int(category_id)
    category = get_object_or_404(Categories.all_objects, pk=category_id)
    context = RequestContext(request)
    context['category'] = category
    return render_to_response('common/view_category.html', context)

@csrf_exempt
def plupload_handler(request):
    if request.method == 'POST':
        f = request.FILES['file']
        file = UploadedFile(file=f)
        file.save()
        return HttpResponse(file.pk)
    return HttpResponse('Not OK')