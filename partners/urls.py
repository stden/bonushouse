# -*- coding: utf-8 -*-
from django.conf.urls import patterns, url
from partners.views import MenuIndexView, PartnersPageListView

urlpatterns = patterns('',
    url(r'^$', PartnersPageListView.as_view(), name='partners_page'),
    url(r'^menu/$', MenuIndexView.as_view(), name='partner_menu'),
    url(r'^menu/offers/$', 'partners.views.menu_offers_index', name='partner_menu_offers_index'),
    url(r'^menu/offers/add/$', 'partners.views.menu_offers_add', name='partner_menu_offers_add'),
    url(r'^menu/offers/edit/(?P<offer_id>\d+)/$', 'partners.views.menu_offers_edit', name='partner_menu_offers_edit'),
    url(r'^menu/moderation/$', 'partners.views.menu_moderator', name='partner_menu_moderator'),
    url(r'^menu/pin-codes/$', 'partners.views.pin_codes', name='partner_menu_pin_codes'),
    url(r'^menu/reports/$', 'partners.views.reports', name='partner_menu_reports'),
)