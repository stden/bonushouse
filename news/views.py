# -*- coding: utf-8 -*-
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from news.models import News
# Create your views here.
def index(request):
    context = RequestContext(request)
    context['posts'] = News.objects.order_by('-add_date')
    return render_to_response('news/index.html', context)

def view_post(request, post_id):
    post_id = int(post_id)
    post = get_object_or_404(News, pk=post_id)
    context = RequestContext(request)
    context['object'] = post
    return render_to_response('news/news_detail.html', context)