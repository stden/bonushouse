from django.conf.urls import patterns, url
from news.models import News
from django.views.generic import ListView, DetailView

urlpatterns = patterns('',
    url(r'^$', ListView.as_view(model=News, paginate_by=10), name='news_index'),
    url(r'^(?P<post_id>[0-9]+)$', 'news.views.view_post', name='news_single'),
)