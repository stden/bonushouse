from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
        url(r'unsubscribe/(?P<user_hash>\w+)/$', 'newsletter.views.unsubscribe', name='newsletter_unsubscribe'),
    )