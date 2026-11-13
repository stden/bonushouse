from django.conf.urls import patterns, url
urlpatterns = patterns('',
    url(r'^banners/click/(?P<banner_id>\d+)$', 'advertising.views.banner_click', name='advertising_banners_click'),
)