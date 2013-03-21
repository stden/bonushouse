# -*- coding: utf-8 -*-
from django.conf.urls import patterns, url
urlpatterns = patterns('',
    url(r'^complete/(?P<backend>[^/]+)/$', 'payment_gateways.views.complete_payment', name='payment_gateway_complete'),
    url(r'^check-order/(?P<backend>[^/]+)/$', 'payment_gateways.views.check_order_id', name='payment_gateway_check_order'),
    url(r'^success/$', 'payment_gateways.views.success_payment', name='payment_gateway_success'),
    url(r'^failure/$', 'payment_gateways.views.failed_payment', name='payment_gateway_failure'),
)