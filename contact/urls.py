# -*- coding: utf-8 -*-
from django.conf.urls import patterns, url
urlpatterns = patterns('',
    url(r'^$', 'contact.views.index', name='contact_form'),
    url(r'^success/$', 'contact.views.contact_form_success', name='contact_form_success'),
)