# -*- coding: utf-8 -*-
from django.conf.urls import patterns, url
from administration.views import IndexView, UsersFormView, UsersListView, PartnerAddressListView, PartnerAddressCreateView, PartnerAddressUpdateView, PartnerAddressDeleteView, PartnersPageListView, PartnersPageCreateView, PartnersPageUpdateView, ClubCardNumbersListView, ClubCardNumbersCreateView, ClubCardNumbersUpdateView
from administration.views import CallMeSubjectCreateView, CallMeSubjectUpdateView, ModelChangelogListView
from django.contrib.auth.models import User
from offers.forms import OffersForm
from flatpages.forms import FlatPageForm
from auctions.forms import AuctionForm
from administration.forms import OffersFormPreview, PagesFormPreview, AuctionFormPreview

urlpatterns = patterns('',
    url(r'^$', IndexView.as_view(), name='administration_index'),

    url(r'^log/$', ModelChangelogListView.as_view(), name='administration_model_changelog'),

    url(r'^offers/$', 'administration.views.offers_index', name='administration_offers_index'),
    url(r'^offers/auto-bonus-count/$', 'administration.views.get_bonus_count', name='get_auto_bonus_count'),
    url(r'^offers/add/$', 'administration.views.offers_add', name='administration_offers_add'),
    url(r'^offers/add_prolongation/$', 'administration.views.offers_add_prolongation', name='administration_offers_add_prolongation'),
    url(r'^offers/preview/$', OffersFormPreview(OffersForm), name='administration_offers_preview'),
    url(r'^offers/edit/(?P<offer_id>\d+)/$', 'administration.views.offers_edit', name='administration_offers_edit'),
    url(r'^offers/delete/(?P<offer_id>\d+)/$', 'administration.views.offers_delete', name='administration_offers_delete'),
    url(r'^offers/validate/$', 'administration.views.offers_ajax_validate', name='administration_offers_ajax_validate'),

    url(r'^categories/$', 'administration.views.categories_index', name='administration_categories_index'),
    url(r'^categories/add/$', 'administration.views.categories_add', name='administration_categories_add'),
    url(r'^categories/edit/(?P<category_id>\d+)/$', 'administration.views.categories_edit', name='administration_categories_edit'),
    url(r'^categories/delete/(?P<category_id>\d+)/$', 'administration.views.categories_delete', name='administration_categories_delete'),

    url(r'^partners/$', 'administration.views.partners_index', name='administration_partners_index'),
    url(r'^partners/add/$', 'administration.views.partners_add', name='administration_partners_add'),
    url(r'^partners/address/(?P<partner_id>\d+)/$', PartnerAddressListView.as_view(), name='administration_partners_address_index'),
    url(r'^partners/address/ajax/(?P<partner_id>\d+)/$', PartnerAddressListView.as_view(template_name='administration/partners/ajax_load.html', paginate_by=1000), name='administration_partners_ajax_load_address'),
    url(r'^partners/address/add/(?P<partner_id>\d+)/$', PartnerAddressCreateView.as_view(), name='administration_partners_address_add'),
    url(r'^partners/address/edit/(?P<address_id>\d+)/$', PartnerAddressUpdateView.as_view(), name='administration_partners_address_edit'),
    url(r'^partners/address/delete/(?P<address_id>\d+)/$', PartnerAddressDeleteView.as_view(), name='administration_partners_address_delete'),
    url(r'^partners/edit/(?P<partner_id>\d+)/$', 'administration.views.partners_edit', name='administration_partners_edit'),
    url(r'^partners/delete/(?P<partner_id>\d+)/$', 'administration.views.partners_delete', name='administration_partners_delete'),

    url(r'^partners-page/$', PartnersPageListView.as_view(), name='administration_partners_page'),
    url(r'^partners-page/add/$', PartnersPageCreateView.as_view(), name='administration_partners_page_add'),
    url(r'^partners-page/edit/(?P<partner_id>\d+)/$', PartnersPageUpdateView.as_view(), name='administration_partners_page_edit'),

    url(r'^pages/$', 'administration.views.pages_index', name='administration_pages_index'),
    url(r'^pages/preview/$', PagesFormPreview(FlatPageForm), name='administration_pages_preview'),
    url(r'^pages/add/$', 'administration.views.pages_add', name='administration_pages_add'),
    url(r'^pages/edit/(?P<page_id>\d+)/$', 'administration.views.pages_edit', name='administration_pages_edit'),
    url(r'^pages/delete/(?P<page_id>\d+)/$', 'administration.views.pages_delete', name='administration_pages_delete'),

    url(r'^news/$', 'administration.views.news_index', name='administration_news_index'),
    url(r'^news/add/$', 'administration.views.news_add', name='administration_news_add'),
    url(r'^news/edit/(?P<post_id>\d+)/$', 'administration.views.news_edit', name='administration_news_edit'),
    url(r'^news/delete/(?P<post_id>\d+)/$', 'administration.views.news_delete', name='administration_news_delete'),

    url(r'^auctions/$', 'administration.views.auctions_index', name='administration_auctions_index'),
    url(r'^auctions/preview/$', AuctionFormPreview(AuctionForm), name='administration_auctions_preview'),
    url(r'^auctions/add/$', 'administration.views.auctions_add', name='administration_auctions_add'),
    url(r'^auctions/edit/(?P<auction_id>\d+)/$', 'administration.views.auctions_edit', name='administration_auctions_edit'),
    url(r'^auctions/delete/(?P<auction_id>\d+)/$', 'administration.views.auctions_delete', name='administration_auctions_delete'),

    url(r'^advertising/$', 'administration.views.advertising_index', name='administration_advertising_index'),
    url(r'^advertising/add-banner/$', 'administration.views.advertising_add_banner', name='administration_advertising_add_banner'),
    url(r'^advertising/edit-banner/(?P<banner_id>\d+)/$', 'administration.views.advertising_banner_edit', name='administration_banner_edit'),
    url(r'^advertising/delete-banner/(?P<banner_id>\d+)/$', 'administration.views.advertising_banner_delete', name='administration_banner_delete'),

    url(r'^reports/$', 'administration.views.reports_index', name='administration_reports_index'),
    url(r'^reports/view/(?P<report_type>[\w-]+)/$', 'administration.views.reports_view', name='administration_reports_view'),
    url(r'^reports/order-details/(?P<metaorder_id>\d+)/$', 'administration.views.reports_metaorder_details', name='administration_reports_order_details'),

    url(r'^emails/$', 'administration.views.emails_index', name='administration_emails_index'),
    url(r'^emails/add-campaign/$', 'administration.views.emails_campaigns_add', name='administration_emails_campaigns_add'),
    url(r'^emails/edit-campaign/(?P<campaign_id>\d+)/$', 'administration.views.emails_campaigns_edit', name='administration_emails_campaigns_edit'),
    url(r'^emails/delete-campaign/(?P<campaign_id>\d+)/$', 'administration.views.emails_campaigns_delete', name='administration_emails_campaigns_delete'),
    url(r'^emails/add-email/$', 'administration.views.emails_add', name='administration_emails_add'),
    url(r'^emails/add-sms/$', 'administration.views.sms_add', name='administration_sms_add'),
    url(r'^emails/edit-email/(?P<email_id>\d+)/$', 'administration.views.emails_edit', name='administration_emails_edit'),
    url(r'^emails/edit-sms/(?P<sms_id>\d+)/$', 'administration.views.sms_edit', name='administration_sms_edit'),
    url(r'^emails/delete-email/(?P<email_id>\d+)/$', 'administration.views.emails_delete', name='administration_emails_delete'),
    url(r'^emails/delete-sms/(?P<sms_id>\d+)/$', 'administration.views.sms_delete', name='administration_sms_delete'),

    url(r'^settings/$', 'administration.views.settings', name='administration_settings'),

    url(r'^ideas/$', 'administration.views.ideas', name='administration_ideas'),
    url(r'^ideas/edit/(?P<idea_id>\d+)/$', 'administration.views.ideas_edit', name='administration_ideas_edit'),
    url(r'^ideas/delete/(?P<idea_id>\d+)/$', 'administration.views.ideas_delete', name='administration_ideas_delete'),

    url(r'^moderator/$', 'administration.views.moderator', name='administration_moderator'),

    url(r'^uploaded-photo/$', 'administration.views.uploaded_photo', name='administration_uploaded_photo'),

    url(r'^call-me/subjects/add/$', CallMeSubjectCreateView.as_view(), name='administration_callme_subjects_add'),
    url(r'^call-me/subjects/edit/(?P<department_id>\d+)/$', CallMeSubjectUpdateView.as_view(), name='administration_callme_subjects_edit'),
    url(r'^call-me/subjects/delete/(?P<department_id>\d+)/$', 'administration.views.call_me_subject_delete', name='administration_callme_subjects_delete'),

    url(r'^users/edit/(?P<user_id>\d+)/$', UsersFormView.as_view(), name='administration_users_edit'),

    url(r'^users/$', UsersListView.as_view(ADMIN_MENU_ACTIVE='Пользователи'), name='administration_users'),
    url(r'^users/administrators/$', UsersListView.as_view(ADMIN_MENU_ACTIVE='Администраторы', queryset=User.objects.filter(is_staff=True)), kwargs={'admins_view':True}, name='administration_users_administrators'),
    url(r'^users/add/$', UsersFormView.as_view(), name='administration_users_add'),
    url(r'^users/edit/(?P<user_id>\d+)/$', UsersFormView.as_view(), name='administration_users_edit'),

    url(r'^club-cards/$', ClubCardNumbersListView.as_view(), name='administration_club_card_numbers_index'),
    url(r'^club-cards/add/$', ClubCardNumbersCreateView.as_view(), name='administration_club_card_numbers_add'),
    url(r'^club-cards/edit/(?P<number_id>\d+)/$', ClubCardNumbersUpdateView.as_view(), name='administration_club_card_numbers_edit'),

    url(r'^metaorders/resend-notification/(?P<metaorder_id>\d+)/$', 'administration.views.metaorders_resend_notification', name='administration_metaorder_resend_notification'),
)