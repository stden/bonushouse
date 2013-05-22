from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
        url(r'unsubscribe/(?P<user_hash>[a-zA-Z0-9]+)/^$', 'newsletter.views.unsubscribe', name='newsletter_unsubscribe'),
    )