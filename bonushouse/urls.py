from django.conf.urls import patterns, include, url
from bonushouse.views import CallMeView, ReferFriendView, ReferFriendSuccessView, ExtendedSearchFormView

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^$', 'bonushouse.views.home', name='home'),
    url(r'^share-link/$', 'bonushouse.views.share_link', name='share_link'),
    url(r'^call-me/success/$', CallMeView.as_view(), name='call_me_success'),
    url(r'^top/$', 'bonushouse.views.top', name='top'),
    url(r'^cron/$', 'bonushouse.views.cron', name='cron'),
    url(r'^accounts/edit-profile/$', 'bonushouse.views.edit_profile', name='edit_profile'),
    url(r'^accounts/cabinet/$', 'bonushouse.views.cabinet', name='cabinet'),
    url(r'^accounts/cabinet/coupons/print/(?P<coupon_id>[0-9]+)/$', 'bonushouse.views.cabinet_coupons_print', name='cabinet_coupons_print'),
    url(r'^accounts/cabinet/gift-coupons/print/(?P<coupon_id>[0-9]+)/$', 'bonushouse.views.cabinet_gift_coupons_print', name='cabinet_gift_coupons_print'),
    url(r'^accounts/cabinet/abonements/$', 'bonushouse.views.cabinet_abonements', name='cabinet_abonements'),
    url(r'^accounts/cabinet/abonements/print/(?P<abonement_id>[0-9]+)/$', 'bonushouse.views.cabinet_abonements_print', name='cabinet_abonements_print'),
    url(r'^accounts/cabinet/additional-services/print/(?P<abonement_id>[0-9]+)/$', 'bonushouse.views.cabinet_additional_services_print', name='cabinet_additional_services_print'),
    url(r'^accounts/cabinet/auctions/print/(?P<auction_id>[0-9]+)/$', 'bonushouse.views.cabinet_auctions_print', name='cabinet_auctions_print'),
    url(r'^accounts/cabinet/additional-services/$', 'bonushouse.views.cabinet_additional_services', name='cabinet_additional_services'),
    url(r'^accounts/cabinet/gifts/$', 'bonushouse.views.cabinet_gifts', name='cabinet_gifts'),
    url(r'^accounts/cabinet/auctions/$', 'bonushouse.views.cabinet_auctions', name='cabinet_auctions'),
    url(r'^accounts/cabinet/refer-friend/$', ReferFriendView.as_view(), name='refer_friend'),
    url(r'^accounts/cabinet/refer-friend/success/$', ReferFriendSuccessView.as_view(), name='refer_friend_success'),
    url(r'^accounts/deposit/$', 'bonushouse.views.deposit_account', name='deposit_account'),
    url(r'^accounts/buy_bonuses/$', 'bonushouse.views.buy_bonuses', name='buy_bonuses'),
    url(r'^accounts/deposit-log/$', 'bonushouse.views.deposit_account_log', name='users_deposit_account_log'),
    url(r'^accounts/cabinet/gift-code-form/$', 'bonushouse.views.cabinet_gift_code_form', name='cabinet_gift_code_form'),

    url(r'^suggest-idea/$', 'bonushouse.views.suggest_business_idea', name='suggest_idea'),
    url(r'^suggest-idea-success/$', 'bonushouse.views.suggest_business_idea_success', name='suggest_idea_success'),

    url(r'^news/', include('news.urls')),

    url(r'^contact/', include('contact.urls')),

    url(r'^advertising/', include('advertising.urls')),

    url(r'^partners/', include('partners.urls')),

    url(r'^offers/', include('offers.urls')),

    url(r'^cart/$', 'offers.views.cart', name='cart'),

    url(r'^auctions/', include('auctions.urls')),

    url(r'^payments/', include('payment_gateways.urls')),

    url(r'^categories/$', 'common.views.categories_index', name='categories_index'),

    url(r'^plupload/$', 'common.views.plupload_handler', name='plupload_handler'),

    url(r'^accounts/login/$', 'bonushouse.views.login_view', name='registration_login'),
    url(r'^accounts/register/$', 'bonushouse.views.login_view'),
    url(r'^accounts/logout/$', 'bonushouse.views.logout_view', name='logout', kwargs={'template_name':'registration/logout.html'}),
    url(r'^accounts/', include('django.contrib.auth.urls')),
    url(r'^accounts/', include('registration.urls')),

    url(r'', include('social_auth.urls')),


    url(r'^ckeditor/', include('ckeditor.urls')),

    (r'^search/', include('haystack.urls')),
    url(r'^extended-search/$', ExtendedSearchFormView.as_view(), name='extended_search'),

    url(r'^administration/', include('administration.urls')),
    # Uncomment the admin/doc line below to enable admin documentation:
    #url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)
from django.conf import settings
if settings.DEBUG:
    urlpatterns += patterns('',
        url(r'^media/(?P<path>.*)$', 'django.views.static.serve',
                {'document_root': settings.MEDIA_ROOT}),
        url(r'^static/(?P<path>.*)$', 'django.views.static.serve',
                {'document_root': settings.STATIC_ROOT}),
    )