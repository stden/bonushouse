from django.conf.urls import patterns, url

urlpatterns = patterns('',
    url(r'^view/(?P<offer_id>[0-9]+)/$', 'offers.views.view', name='offers_view'),
    url(r'^cart/add/(?P<offer_id>[0-9]+)/$', 'offers.views.cart_add', name='offers_add_to_cart'),
    url(r'^cart/buy/(?P<item_id>[0-9]+)/$', 'offers.views.cart_buy', name='offers_cart_buy'),
    url(r'^cart/remove/(?P<item_id>[0-9]+)/$', 'offers.views.cart_remove', name='cart_remove'),
    url(r'^cart/clear/$', 'offers.views.cart_clear', name='cart_clear'),
    url(r'^buy/(?P<offer_id>[0-9]+)/$', 'offers.views.buy', name='offers_buy'),
    url(r'^like/(?P<offer_id>[0-9]+)/$', 'offers.views.like', name='offers_like'),
    url(r'^ajax-additional-info-club-card-validate/(?P<offer_id>[0-9]+)/$', 'offers.views.ajax_additional_info_club_card_validate', name='ajax_additional_info_club_card_validate'),
    url(r'^ajax-additional-info-club-card-load-clubs/(?P<offer_id>[0-9]+)/$', 'offers.views.ajax_additional_info_club_card_load_clubs', name='ajax_additional_info_club_card_load_clubs'),
    url(r'^ajax-additional-info-abonements-validate/(?P<offer_id>[0-9]+)/$', 'offers.views.ajax_additional_info_abonements_validate', name='ajax_additional_info_abonements_validate'),
)