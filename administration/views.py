# -*- coding: utf-8 -*-
import datetime
import csv

from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.db import models
from django.template import RequestContext
from django.shortcuts import render_to_response, redirect, get_object_or_404
from common.forms import CategoriesForm, PhotoForm
from common.models import Categories
from seo.forms import SeoModelMetaForm, SeoModelUrlForm
from offers.forms import OffersForm, ProlongationOffersAdminForm
from offers.models import Offers, ProlongationOffers, Order, AbonementOrder, AdditionalServicesOrder, MetaOrder, GiftOrder
from partners.models import Partner, PartnerAddress, PartnersPage, ClubCardNumbers
from partners.forms import PartnerForm, PartnerAddressForm, PartnersPageForm, ClubCardNumbersForm
from flatpages.models import FlatPage
from flatpages.forms import FlatPageForm
from news.models import News
from news.forms import NewsForm
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from administration.forms import BulkOffersForm, BulkCategoriesForm, BulkPartnersForm, BulkPagesForm, BulkBannersForm, \
    BulkAuctionsForm, DateRangeForm, IdeaRewardForm, BulkFeedbacksForm, UserForm, BulkUsersForm, BulkPartnersPageForm, \
    BulkClubCardNumbersForm, CallMeSubjectForm, BulkProlongationOffersForm
from django.http import Http404, HttpResponse
from common.models import UploadedFile
from django.utils import simplejson
from django.views.decorators.csrf import csrf_exempt
from dbsettings.forms import SettingsForm
from advertising.forms import BannerForm
from advertising.models import Banner
from auctions.forms import AuctionForm
from auctions.models import Auction
from bonushouse.models import BonusTransactions, BusinessIdea, UserFeedbacks
from django.utils import timezone
from django.utils.timezone import make_aware, get_current_timezone, now, localtime
from newsletter.forms import NewsletterCampaignForm, NewsletterEmailForm, NewsletterSmsForm
from newsletter.models import NewsletterCampaign, NewsletterEmail, NewsletterSms
from administration.menu import load_menu_context
from django.views.generic import FormView, ListView, TemplateView, CreateView, UpdateView, DeleteView
from django.views.generic.edit import FormMixin
from django.utils.decorators import method_decorator
from django.core.urlresolvers import reverse_lazy

from bonushouse.utils import get_auto_bonus_count
from newsletter.sms_gate import Gate
from django.conf import settings as django_settings
from administration.models import CallMeSubjects
from model_changelog.models import LogMessage
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.template import Template, Context



class BaseAdminView(object):
    @method_decorator(user_passes_test(lambda u: u.is_staff))
    def dispatch(self, request, *args, **kwargs):
        return super(BaseAdminView, self).dispatch(request, *args, **kwargs)
    def get_context_data(self, **kwargs):
        context = super(BaseAdminView, self).get_context_data(**kwargs)
        context = load_menu_context(context, self.request, show_secondary_menu=False)
        return context

class SuperUserRequiredView(BaseAdminView):
    @method_decorator(user_passes_test(lambda u: u.is_staff and u.is_superuser))
    def dispatch(self, request, *args, **kwargs):
        return super(SuperUserRequiredView, self).dispatch(request, *args, **kwargs)

# Create your views here.
class IndexView(BaseAdminView, TemplateView):
    template_name = 'administration/index.html'


@user_passes_test(lambda u: u.is_staff)
def offers_index(request):
    if request.method == 'POST':
        form = BulkOffersForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['action'] == 'delete':
                for offer in form.cleaned_data['selected_items']:
                    offer.delete()
            elif form.cleaned_data['action'] == 'publish':
                for offer in form.cleaned_data['selected_items']:
                    offer.is_published = True
                    offer.save()
            elif form.cleaned_data['action'] == 'hide':
                for offer in form.cleaned_data['selected_items']:
                    offer.is_published = False
                    offer.save()
        return redirect('administration.views.offers_index')
    per_page = 20
    page = request.GET.get('page', 1)
    context = RequestContext(request)
    context = load_menu_context(context, request, show_secondary_menu=False)
    context['ADMIN_MENU_ACTIVE'] = 'OFFERS'
    offers_list = Offers.all_objects.all()
    context['offers_list'] = offers_list
    # paginator = Paginator(offers_list, per_page)
    # try:
    #     context['offers_list'] = paginator.page(page)
    # except PageNotAnInteger:
    #     context['offers_list'] = paginator.page(1)
    # except EmptyPage:
    #     context['offers_list'] = paginator.page(paginator.num_pages)
    return render_to_response('administration/offers/index.html', context)


@user_passes_test(lambda u: u.is_staff)
def offers_prolongation_index(request):
    if request.method == 'POST':
        form = BulkProlongationOffersForm(request.POST)
        if form.is_valid():
            BulkProlongationOffersForm(request.POST)
            if form.cleaned_data['action'] == 'delete':
                for offer in form.cleaned_data['selected_items']:
                    print offer
                    offer.delete()
            elif form.cleaned_data['action'] == 'publish':
                for offer in form.cleaned_data['selected_items']:
                    offer.is_published = True
                    offer.save()
            elif form.cleaned_data['action'] == 'hide':
                for offer in form.cleaned_data['selected_items']:
                    offer.is_published = False
                    offer.save()
        return redirect('administration.views.offers_prolongation_index')
    per_page = 20
    page = request.GET.get('page', 1)
    context = RequestContext(request)
    context = load_menu_context(context, request, show_secondary_menu=False)
    context['ADMIN_MENU_ACTIVE'] = 'OFFERS_PROLONGATION'
    offers_list = ProlongationOffers.all_objects.all()
    context['offers_list'] = offers_list
    return render_to_response('administration/offers_prolongation/index.html', context)


def get_bonus_count(request):
    price = request.GET.get('price')
    result = {'success':True, 'bonuses_count':0}
    if price:
        result['bonuses_count'] = get_auto_bonus_count(price)
    return HttpResponse(simplejson.dumps(result))


@user_passes_test(lambda u: u.is_staff)
def offers_add(request):
    context = RequestContext(request)
    context = load_menu_context(context, request, show_secondary_menu=False)
    context['ADMIN_MENU_ACTIVE'] = 'OFFERS'
    if request.method == 'POST':
        offers_form = OffersForm(request.POST)
        seo_meta_form = SeoModelMetaForm(request.POST)
        seo_url_form = SeoModelUrlForm(request.POST)
        if offers_form.is_valid() and seo_meta_form.is_valid() and seo_url_form.is_valid():
            offers_form.save()
            seo_meta_form.instance.content_object = offers_form.instance
            seo_meta_form.save()
            seo_url_form.instance.content_object = offers_form.instance
            seo_url_form.save()
            return redirect('administration.views.offers_index')
    else:
        offers_form = OffersForm()
        seo_meta_form = SeoModelMetaForm()
        seo_url_form = SeoModelUrlForm()
    context['offers_form'] = offers_form
    context['seo_meta_form'] = seo_meta_form
    context['seo_url_form'] = seo_url_form
    context['page_title'] = 'Добавить акцию'
    return render_to_response('administration/offers/form.html', context)

@user_passes_test(lambda u: u.is_staff)
def offers_prolongation_add(request):
    context = RequestContext(request)
    context = load_menu_context(context, request, show_secondary_menu=False)
    context['ADMIN_MENU_ACTIVE'] = 'OFFERS'
    if request.method == 'POST':
        offers_form = ProlongationOffersAdminForm(request.POST)
        seo_meta_form = SeoModelMetaForm(request.POST)
        seo_url_form = SeoModelUrlForm(request.POST)
        if offers_form.is_valid() and seo_meta_form.is_valid() and seo_url_form.is_valid():
            offers_form.save()
            seo_meta_form.instance.content_object = offers_form.instance
            seo_meta_form.save()
            seo_url_form.instance.content_object = offers_form.instance
            seo_url_form.save()
            return redirect('administration.views.offers_prolongation_index')
    else:
        offers_form = ProlongationOffersAdminForm()
        seo_meta_form = SeoModelMetaForm()
        seo_url_form = SeoModelUrlForm()
    context['offers_form'] = offers_form
    context['seo_meta_form'] = seo_meta_form
    context['seo_url_form'] = seo_url_form
    context['page_title'] = 'Добавить акцию'
    return render_to_response('administration/offers_prolongation/form.html', context)


@user_passes_test(lambda u: u.is_staff)
def offers_edit(request, offer_id):
    offer_id = int(offer_id)
    offer = get_object_or_404(Offers.all_objects, pk=offer_id)
    context = RequestContext(request)
    context = load_menu_context(context, request, show_secondary_menu=False)
    context['ADMIN_MENU_ACTIVE'] = 'OFFERS'
    if request.method == 'POST':
        offers_form = OffersForm(request.POST, request.FILES, instance=offer)
        seo_meta_form = SeoModelMetaForm(request.POST, instance=offer.get_seo_meta_object())
        seo_url_form = SeoModelUrlForm(request.POST, instance=offer.get_seo_url_object())
        if request.POST.get('delete') is not None:
            offer.delete()
            return redirect('administration.views.offers_index')
        else:
            if offers_form.is_valid() and seo_meta_form.is_valid() and seo_url_form.is_valid():
                offers_form.save()
                seo_meta_form.save()
                seo_url_form.save()
                if request.POST.get('publish') is not None:
                    offer.publish()
                return redirect('administration.views.offers_index')
    else:
        offers_form = OffersForm(instance=offer)
        seo_meta_form = SeoModelMetaForm(instance=offer.get_seo_meta_object())
        seo_url_form = SeoModelUrlForm(instance=offer.get_seo_url_object())

    context['offers_form'] = offers_form
    context['seo_meta_form'] = seo_meta_form
    context['seo_url_form'] = seo_url_form
    context['page_title'] = offer.title
    context['offer'] = offer
    return render_to_response('administration/offers/form.html', context)


@user_passes_test(lambda u: u.is_staff)
def offers_prolongation_edit(request, offer_id):
    offer_id = int(offer_id)
    offer = get_object_or_404(ProlongationOffers.all_objects, pk=offer_id)
    context = RequestContext(request)
    context = load_menu_context(context, request, show_secondary_menu=False)
    context['ADMIN_MENU_ACTIVE'] = 'OFFERS'
    if request.method == 'POST':
        offers_form = ProlongationOffersAdminForm(request.POST, request.FILES, instance=offer)
        seo_meta_form = SeoModelMetaForm(request.POST, instance=offer.get_seo_meta_object())
        seo_url_form = SeoModelUrlForm(request.POST, instance=offer.get_seo_url_object())
        if request.POST.get('delete') is not None:
            offer.delete()
            return redirect('administration.views.offers_prolongation_index')
        else:
            if offers_form.is_valid() and seo_meta_form.is_valid() and seo_url_form.is_valid():
                offers_form.save()
                seo_meta_form.save()
                seo_url_form.save()
                if request.POST.get('publish') is not None:
                    offer.publish()
                return redirect('administration.views.offers_prolongation_index')
    else:
        offers_form = ProlongationOffersAdminForm(instance=offer)
        seo_meta_form = SeoModelMetaForm(instance=offer.get_seo_meta_object())
        seo_url_form = SeoModelUrlForm(instance=offer.get_seo_url_object())

    context['offers_form'] = offers_form
    context['seo_meta_form'] = seo_meta_form
    context['seo_url_form'] = seo_url_form
    context['page_title'] = offer.title
    context['offer'] = offer
    return render_to_response('administration/offers_prolongation/form.html', context)


@csrf_exempt
def offers_ajax_validate(request):
    response = {'success': False, 'messages': []}
    offer_id = request.POST.get('offer_id')
    if offer_id:
        offer_instance = get_object_or_404(Offers.all_objects, pk=offer_id)
        seo_instance = offer_instance.get_seo_meta_object()
        url_instance = offer_instance.get_seo_url_object()
    else:
        offer_instance = None
        seo_instance = None
        url_instance = None
    if request.method == 'POST':
        offers_form = OffersForm(request.POST, request.FILES, instance=offer_instance)
        seo_meta_form = SeoModelMetaForm(request.POST, instance=seo_instance)
        seo_url_form = SeoModelUrlForm(request.POST, instance=url_instance)
        if offers_form.is_valid() and seo_meta_form.is_valid() and seo_url_form.is_valid():
            response['success'] = True
        else:
            for form in (offers_form, seo_meta_form, seo_url_form):
                for error in form.non_field_errors():
                    response['messages'].append(error)
                for field in form:
                    for error in field.errors:
                        response['messages'].append(field.label + ' - ' + error)
            response['messages'] = "\n".join(response['messages'])
    return HttpResponse(simplejson.dumps(response))


@user_passes_test(lambda u: u.is_staff)
def offers_delete(request, offer_id):
    offer_id = int(offer_id)
    offer = get_object_or_404(Offers, pk=offer_id)
    offer.delete()
    return redirect('administration.views.offers_index')


@user_passes_test(lambda u: u.is_staff)
def offers_prolongation_delete(request, offer_id):
    offer_id = int(offer_id)
    offer = get_object_or_404(ProlongationOffers, pk=offer_id)
    offer.delete()
    return redirect('administration.views.offers_prolongation_index')


@user_passes_test(lambda u: u.is_staff and u.is_superuser)
def categories_index(request):
    if request.method == 'POST':
        form = BulkCategoriesForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['action'] == 'delete':
                for category in form.cleaned_data['selected_items']:
                    category.delete()
            elif form.cleaned_data['action'] == 'publish':
                for category in form.cleaned_data['selected_items']:
                    category.is_published = True
                    category.save()
            elif form.cleaned_data['action'] == 'hide':
                for category in form.cleaned_data['selected_items']:
                    category.is_published = False
                    category.save()
        return redirect('administration.views.categories_index')
    per_page = 20
    page = request.GET.get('page', 1)
    context = RequestContext(request)
    context = load_menu_context(context, request, show_secondary_menu=False)
    context['ADMIN_MENU_ACTIVE'] = 'CATEGORIES'
    categories_list = Categories.all_objects.all()
    paginator = Paginator(categories_list, per_page)
    try:
        context['categories_list'] = paginator.page(page)
    except PageNotAnInteger:
        context['categories_list'] = paginator.page(1)
    except EmptyPage:
        context['categories_list'] = paginator.page(paginator.num_pages)
    return render_to_response('administration/categories/index.html', context)


@user_passes_test(lambda u: u.is_staff and u.is_superuser)
def categories_add(request):
    context = RequestContext(request)
    context = load_menu_context(context, request, show_secondary_menu=False)
    context['ADMIN_MENU_ACTIVE'] = 'CATEGORIES'
    if request.method == 'POST':
        categories_form = CategoriesForm(request.POST)
        seo_meta_form = SeoModelMetaForm(request.POST)
        seo_url_form = SeoModelUrlForm(request.POST)
        photo_form = PhotoForm(request.POST, request.FILES)
        if categories_form.is_valid() and seo_meta_form.is_valid() and \
                seo_url_form.is_valid() and photo_form.is_valid():
            categories_form.save()
            seo_meta_form.instance.content_object = categories_form.instance
            seo_meta_form.save()
            seo_url_form.instance.content_object = categories_form.instance
            seo_url_form.save()
            photo_form.instance.content_object = categories_form.instance
            photo_form.save()
            return redirect('administration.views.categories_index')
    else:
        categories_form = CategoriesForm()
        seo_meta_form = SeoModelMetaForm()
        seo_url_form = SeoModelUrlForm()
        photo_form = PhotoForm()
    context['categories_form'] = categories_form
    context['seo_meta_form'] = seo_meta_form
    context['seo_url_form'] = seo_url_form
    context['photo_form'] = photo_form
    context['page_title'] = 'Добавить категорию'
    return render_to_response('administration/categories/form.html', context)


@user_passes_test(lambda u: u.is_staff and u.is_superuser)
def categories_edit(request, category_id):
    category_id = int(category_id)
    category = get_object_or_404(Categories.all_objects, pk=category_id)
    context = RequestContext(request)
    context = load_menu_context(context, request, show_secondary_menu=False)
    context['ADMIN_MENU_ACTIVE'] = 'CATEGORIES'
    if request.method == 'POST':
        categories_form = CategoriesForm(instance=category, data=request.POST)
        seo_meta_form = SeoModelMetaForm(instance=category.get_seo_meta_object(), data=request.POST)
        seo_url_form = SeoModelUrlForm(instance=category.get_seo_url_object(), data=request.POST)
        photo_form = PhotoForm(instance=category.get_photo_object(), data=request.POST, files=request.FILES)
        if categories_form.is_valid() and seo_meta_form.is_valid() and \
                seo_url_form.is_valid() and photo_form.is_valid():
            categories_form.save()
            seo_meta_form.instance.content_object = categories_form.instance
            seo_meta_form.save()
            seo_url_form.instance.content_object = categories_form.instance
            seo_url_form.save()
            photo_form.instance.content_object = category
            photo_form.save()
            return redirect('administration.views.categories_index')
    else:
        categories_form = CategoriesForm(instance=category)
        seo_meta_form = SeoModelMetaForm(instance=category.get_seo_meta_object())
        seo_url_form = SeoModelUrlForm(instance=category.get_seo_url_object())
        photo_form = PhotoForm(instance=category.get_photo_object())
    context['categories_form'] = categories_form
    context['seo_meta_form'] = seo_meta_form
    context['seo_url_form'] = seo_url_form
    context['photo_form'] = photo_form
    context['page_title'] = u"%s" % (category.title, )
    context['category'] = category
    return render_to_response('administration/categories/form.html', context)


@user_passes_test(lambda u: u.is_staff and u.is_superuser)
def categories_delete(request, category_id):
    category_id = int(category_id)
    category = get_object_or_404(Categories.all_objects, pk=category_id)
    category.delete()
    return redirect('administration.views.categories_index')


@user_passes_test(lambda u: u.is_staff)
def partners_index(request):
    if request.method == 'POST':
        form = BulkPartnersForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['action'] == 'delete':
                for partner in form.cleaned_data['selected_items']:
                    partner.delete()
            elif form.cleaned_data['action'] == 'publish':
                for partner in form.cleaned_data['selected_items']:
                    partner.is_published = True
                    partner.save()
            elif form.cleaned_data['action'] == 'hide':
                for partner in form.cleaned_data['selected_items']:
                    partner.is_published = False
                    partner.save()
        return redirect('administration.views.partners_index')
    per_page = 20
    page = request.GET.get('page', 1)
    context = RequestContext(request)
    context = load_menu_context(context, request, show_secondary_menu=False)
    context['ADMIN_MENU_ACTIVE'] = 'PARTNERS'
    partners_list = Partner.objects.all()
    paginator = Paginator(partners_list, per_page)
    try:
        context['partners_list'] = paginator.page(page)
    except PageNotAnInteger:
        context['partners_list'] = paginator.page(1)
    except EmptyPage:
        context['partners_list'] = paginator.page(paginator.num_pages)
    return render_to_response('administration/partners/index.html', context)


@user_passes_test(lambda u: u.is_staff)
def partners_add(request):
    context = RequestContext(request)
    context = load_menu_context(context, request, show_secondary_menu=False)
    context['ADMIN_MENU_ACTIVE'] = 'PARTNERS'
    if request.method == 'POST':
        partner_form = PartnerForm(request.POST)
        seo_meta_form = SeoModelMetaForm(request.POST)
        seo_url_form = SeoModelUrlForm(request.POST)
        if partner_form.is_valid() and seo_meta_form.is_valid() and seo_url_form.is_valid():
            partner_form.save()
            seo_meta_form.instance.content_object = partner_form.instance
            seo_meta_form.save()
            seo_url_form.instance.content_object = partner_form.instance
            seo_url_form.save()
            return redirect('administration.views.partners_index')
    else:
        partner_form = PartnerForm()
        seo_meta_form = SeoModelMetaForm()
        seo_url_form = SeoModelUrlForm()
    context['partner_form'] = partner_form
    context['seo_meta_form'] = seo_meta_form
    context['seo_url_form'] = seo_url_form
    context['page_title'] = 'Добавить партнера'
    return render_to_response('administration/partners/form.html', context)


@user_passes_test(lambda u: u.is_staff)
def partners_edit(request, partner_id):
    partner_id = int(partner_id)
    partner = get_object_or_404(Partner.objects, pk=partner_id)
    context = RequestContext(request)
    context = load_menu_context(context, request, show_secondary_menu=False)
    context['ADMIN_MENU_ACTIVE'] = 'PARTNERS'
    if request.method == 'POST':
        partner_form = PartnerForm(request.POST, instance=partner)
        seo_meta_form = SeoModelMetaForm(request.POST, instance=partner.get_seo_meta_object())
        seo_url_form = SeoModelUrlForm(request.POST, instance=partner.get_seo_url_object())
        if partner_form.is_valid() and seo_meta_form.is_valid() and seo_url_form.is_valid():
            partner_form.save()
            seo_meta_form.save()
            seo_url_form.save()
            return redirect('administration.views.partners_index')
    else:
        partner_form = PartnerForm(instance=partner)
        seo_meta_form = SeoModelMetaForm(instance=partner.get_seo_meta_object())
        seo_url_form = SeoModelUrlForm(instance=partner.get_seo_url_object())
    context['partner_form'] = partner_form
    context['seo_meta_form'] = seo_meta_form
    context['seo_url_form'] = seo_url_form
    context['page_title'] = u'%s' % (partner.title, )
    context['partner'] = partner
    return render_to_response('administration/partners/form.html', context)



class PartnerAddressListView(ListView):
    paginate_by = 20
    template_name = 'administration/partners/address_index.html'
    def dispatch(self, request, *args, **kwargs):
        return super(PartnerAddressListView, self).dispatch(request, *args, **kwargs)
    def get_context_data(self, **kwargs):
        context = super(PartnerAddressListView, self).get_context_data(**kwargs)
        partner = get_object_or_404(Partner, pk=self.kwargs.get('partner_id'))
        context = load_menu_context(context, self.request, show_secondary_menu=False)
        context['partner'] = partner
        return context
    def get_queryset(self):
        return PartnerAddress.objects.filter(partner__pk=self.kwargs.get('partner_id'))

class PartnerAddressCreateView(BaseAdminView, CreateView):
    model = PartnerAddress
    form_class = PartnerAddressForm
    template_name = 'administration/partners/address_form.html'
    def get_success_url(self):
        return reverse_lazy('administration_partners_address_index', kwargs=self.kwargs)
    def form_valid(self, form):
        form.instance.partner = Partner.objects.get(pk=self.kwargs.get('partner_id'))
        form.save()
        return redirect(self.get_success_url())
    def get_context_data(self, **kwargs):
        context = super(PartnerAddressCreateView, self).get_context_data(**kwargs)
        partner = get_object_or_404(Partner, pk=self.kwargs.get('partner_id'))
        context['partner'] = partner
        context['page_title'] = 'Добавить адрес'
        return context

class PartnerAddressUpdateView(BaseAdminView, UpdateView):
    model = PartnerAddress
    form_class = PartnerAddressForm
    template_name = 'administration/partners/address_form.html'
    pk_url_kwarg = 'address_id'
    def get_success_url(self):
        address = get_object_or_404(PartnerAddress, pk=self.kwargs.get('address_id'))
        return reverse_lazy('administration_partners_address_index', kwargs={'partner_id':address.partner.pk})
    def get_context_data(self, **kwargs):
        context = super(PartnerAddressUpdateView, self).get_context_data(**kwargs)
        address = get_object_or_404(PartnerAddress, pk=self.kwargs.get('address_id'))
        context['address'] = address
        context['partner'] = address.partner
        context['page_title'] = address.title
        return context

class PartnerAddressDeleteView(BaseAdminView, DeleteView):
    model = PartnerAddress
    template_name = 'administration/partners/address_delete.html'
    pk_url_kwarg = 'address_id'
    address = None
    partner = None
    def get_success_url(self):
        return reverse_lazy('administration_partners_address_index', kwargs={'partner_id':self.partner.pk})
    def dispatch(self, request, *args, **kwargs):
        address = get_object_or_404(PartnerAddress, pk=kwargs.get('address_id'))
        self.address = address
        self.partner = address.partner
        return super(PartnerAddressDeleteView, self).dispatch(request, *args, **kwargs)
    def get_context_data(self, **kwargs):
        context = super(PartnerAddressDeleteView, self).get_context_data(**kwargs)
        address = self.address
        partner = self.partner
        context['address'] = address
        context['partner'] = partner
        return context

@user_passes_test(lambda u: u.is_staff)
def partners_delete(request, partner_id):
    partner_id = int(partner_id)
    partner = get_object_or_404(Partner, pk=partner_id)
    partner.delete()
    return redirect('administration.views.partners_index')


@user_passes_test(lambda u: u.is_staff)
def pages_index(request):
    if request.method == 'POST':
        form = BulkPagesForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['action'] == 'delete':
                for page in form.cleaned_data['selected_items']:
                    page.delete()
            elif form.cleaned_data['action'] == 'publish':
                for page in form.cleaned_data['selected_items']:
                    page.is_published = True
                    page.save()
            elif form.cleaned_data['action'] == 'hide':
                for page in form.cleaned_data['selected_items']:
                    page.is_published = False
                    page.save()
        return redirect('administration.views.pages_index')
    per_page = 20
    page = request.GET.get('page', 1)
    context = RequestContext(request)
    context = load_menu_context(context, request, show_secondary_menu=False)
    context['ADMIN_MENU_ACTIVE'] = 'PAGES'
    pages_list = FlatPage.objects.all()
    paginator = Paginator(pages_list, per_page)
    try:
        context['pages_list'] = paginator.page(page)
    except PageNotAnInteger:
        context['pages_list'] = paginator.page(1)
    except EmptyPage:
        context['pages_list'] = paginator.page(paginator.num_pages)
    return render_to_response('administration/pages/index.html', context)


@user_passes_test(lambda u: u.is_staff)
def pages_add(request):
    context = RequestContext(request)
    context = load_menu_context(context, request, show_secondary_menu=False)
    context['ADMIN_MENU_ACTIVE'] = 'PAGES'
    if request.method == 'POST':
        page_form = FlatPageForm(request.POST)
        seo_meta_form = SeoModelMetaForm(request.POST)
        seo_url_form = SeoModelUrlForm(request.POST)
        if page_form.is_valid() and seo_meta_form.is_valid() and seo_url_form.is_valid():
            page_form.save()
            seo_meta_form.instance.content_object = page_form.instance
            seo_meta_form.save()
            seo_url_form.instance.content_object = page_form.instance
            seo_url_form.save()
            return redirect('administration.views.pages_index')
    else:
        page_form = FlatPageForm()
        seo_meta_form = SeoModelMetaForm()
        seo_url_form = SeoModelUrlForm()
    context['page_form'] = page_form
    context['seo_meta_form'] = seo_meta_form
    context['seo_url_form'] = seo_url_form
    context['page_title'] = 'Добавить страницу'
    return render_to_response('administration/pages/form.html', context)


@user_passes_test(lambda u: u.is_staff)
def pages_edit(request, page_id):
    page_id = int(page_id)
    page = get_object_or_404(FlatPage, pk=page_id)
    context = RequestContext(request)
    context = load_menu_context(context, request, show_secondary_menu=False)
    context['ADMIN_MENU_ACTIVE'] = 'PAGES'
    if request.method == 'POST':
        page_form = FlatPageForm(request.POST, instance=page)
        seo_meta_form = SeoModelMetaForm(request.POST, instance=page.get_seo_meta_object())
        seo_meta_form.instance.content_object = page
        seo_url_form = SeoModelUrlForm(request.POST, instance=page.get_seo_url_object())
        seo_url_form.instance.content_object = page
        if page_form.is_valid() and seo_meta_form.is_valid() and seo_url_form.is_valid():
            page_form.save()
            seo_meta_form.save()
            seo_url_form.save()
            return redirect('administration.views.pages_index')
    else:
        page_form = FlatPageForm(instance=page)
        seo_meta_form = SeoModelMetaForm(instance=page.get_seo_meta_object())
        seo_url_form = SeoModelUrlForm(instance=page.get_seo_url_object())
    context['page_form'] = page_form
    context['seo_meta_form'] = seo_meta_form
    context['seo_url_form'] = seo_url_form
    context['page_title'] = u'%s' % (page.title, )
    context['page'] = page
    return render_to_response('administration/pages/form.html', context)


@user_passes_test(lambda u: u.is_staff)
def pages_delete(request, page_id):
    page_id = int(page_id)
    page = get_object_or_404(FlatPage, pk=page_id)
    page.delete()
    return redirect('administration.views.pages_index')


@user_passes_test(lambda u: u.is_staff)
def news_index(request):
    context = RequestContext(request)
    context = load_menu_context(context, request, show_secondary_menu=False)
    context['ADMIN_MENU_ACTIVE'] = 'PAGES'
    per_page = 20
    page = request.GET.get('page', 1)
    news_list = News.objects.all()
    paginator = Paginator(news_list, per_page)
    try:
        context['news_list'] = paginator.page(page)
    except PageNotAnInteger:
        context['news_list'] = paginator.page(1)
    except EmptyPage:
        context['news_list'] = paginator.page(paginator.num_pages)
    return render_to_response('administration/news/index.html', context)


@user_passes_test(lambda u: u.is_staff)
def news_add(request):
    context = RequestContext(request)
    context = load_menu_context(context, request, show_secondary_menu=False)
    if request.method == 'POST':
        news_form = NewsForm(request.POST, request.FILES)
        seo_meta_form = SeoModelMetaForm(request.POST)
        seo_url_form = SeoModelUrlForm(request.POST)
        if news_form.is_valid() and seo_meta_form.is_valid() and seo_url_form.is_valid():
            news_form.save()
            seo_meta_form.instance.content_object = news_form.instance
            seo_meta_form.save()
            seo_url_form.instance.content_object = news_form.instance
            seo_url_form.save()
            return redirect('administration.views.news_index')
    else:
        news_form = NewsForm()
        seo_meta_form = SeoModelMetaForm()
        seo_url_form = SeoModelUrlForm()
    context['news_form'] = news_form
    context['seo_meta_form'] = seo_meta_form
    context['seo_url_form'] = seo_url_form
    context['page_title'] = 'Добавить новость'
    return render_to_response('administration/news/form.html', context)


@user_passes_test(lambda u: u.is_staff)
def news_edit(request, post_id):
    post_id = int(post_id)
    post = get_object_or_404(News, pk=post_id)
    context = RequestContext(request)
    context = load_menu_context(context, request, show_secondary_menu=False)
    if request.method == 'POST':
        news_form = NewsForm(request.POST, request.FILES, instance=post)
        seo_meta_form = SeoModelMetaForm(request.POST, instance=post.get_seo_meta_object())
        seo_meta_form.instance.content_object = post
        seo_url_form = SeoModelUrlForm(request.POST, instance=post.get_seo_url_object())
        seo_url_form.instance.content_object = post
        if news_form.is_valid() and seo_meta_form.is_valid() and seo_url_form.is_valid():
            news_form.save()
            seo_meta_form.save()
            seo_url_form.save()
            return redirect('administration.views.news_index')
    else:
        news_form = NewsForm(instance=post)
        seo_meta_form = SeoModelMetaForm(instance=post.get_seo_meta_object())
        seo_url_form = SeoModelUrlForm(instance=post.get_seo_url_object())
    context['news_form'] = news_form
    context['seo_meta_form'] = seo_meta_form
    context['seo_url_form'] = seo_url_form
    context['page_title'] = u'Редактировать новость %s' % (post.title, )
    context['news_post'] = post
    return render_to_response('administration/news/form.html', context)


@user_passes_test(lambda u: u.is_staff)
def news_delete(request, post_id):
    post_id = int(post_id)
    post = get_object_or_404(News, pk=post_id)
    post.delete()
    return redirect('administration.views.news_index')


@user_passes_test(lambda u: u.is_staff)
def auctions_index(request):
    if request.method == 'POST':
        form = BulkAuctionsForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['action'] == 'delete':
                for item in form.cleaned_data['selected_items']:
                    item.delete()
            elif form.cleaned_data['action'] == 'publish':
                for item in form.cleaned_data['selected_items']:
                    item.is_published = True
                    item.save()
            elif form.cleaned_data['action'] == 'hide':
                for item in form.cleaned_data['selected_items']:
                    item.is_published = False
                    item.save()
        return redirect('administration.views.auctions_index')
    per_page = 20
    page = request.GET.get('page', 1)
    context = RequestContext(request)
    context = load_menu_context(context, request, show_secondary_menu=False)
    context['ADMIN_MENU_ACTIVE'] = 'AUCTIONS'
    auctions_list = Auction.all_objects.all()
    paginator = Paginator(auctions_list, per_page)
    try:
        context['auctions_list'] = paginator.page(page)
    except PageNotAnInteger:
        context['auctions_list'] = paginator.page(1)
    except EmptyPage:
        context['auctions_list'] = paginator.page(paginator.num_pages)
    return render_to_response('administration/auctions/index.html', context)


@user_passes_test(lambda u: u.is_staff)
def auctions_add(request):
    context = RequestContext(request)
    context = load_menu_context(context, request, show_secondary_menu=False)
    context['ADMIN_MENU_ACTIVE'] = 'AUCTIONS'
    if request.method == 'POST':
        auction_form = AuctionForm(request.POST, request.FILES)
        seo_meta_form = SeoModelMetaForm(request.POST)
        seo_url_form = SeoModelUrlForm(request.POST)
        if auction_form.is_valid() and seo_meta_form.is_valid() and seo_url_form.is_valid():
            auction_form.save()
            seo_meta_form.instance.content_object = auction_form.instance
            seo_meta_form.save()
            seo_url_form.instance.content_object = auction_form.instance
            seo_url_form.save()
            return redirect('administration.views.auctions_index')
    else:
        auction_form = AuctionForm()
        seo_meta_form = SeoModelMetaForm()
        seo_url_form = SeoModelUrlForm()
    context['auction_form'] = auction_form
    context['seo_meta_form'] = seo_meta_form
    context['seo_url_form'] = seo_url_form
    context['page_title'] = 'Создать аукцион'
    return render_to_response('administration/auctions/form.html', context)


@user_passes_test(lambda u: u.is_staff)
def auctions_edit(request, auction_id):
    auction = get_object_or_404(Auction.all_objects, pk=auction_id)
    context = RequestContext(request)
    context = load_menu_context(context, request, show_secondary_menu=False)
    context['ADMIN_MENU_ACTIVE'] = 'AUCTIONS'
    if request.method == 'POST':
        auction_form = AuctionForm(request.POST, request.FILES, instance=auction)
        seo_meta_form = SeoModelMetaForm(request.POST, instance=auction.get_seo_meta_object())
        seo_url_form = SeoModelUrlForm(request.POST, instance=auction.get_seo_url_object())
        if auction_form.is_valid() and seo_meta_form.is_valid() and seo_url_form.is_valid():
            auction_form.save()
            seo_meta_form.instance.content_object = auction
            seo_meta_form.save()
            seo_url_form.instance.content_object = auction
            seo_url_form.save()
            return redirect('administration.views.auctions_index')
    else:
        auction_form = AuctionForm(instance=auction)
        seo_meta_form = SeoModelMetaForm(instance=auction.get_seo_meta_object())
        seo_url_form = SeoModelUrlForm(instance=auction.get_seo_url_object())
    context['auction_form'] = auction_form
    context['auction'] = auction
    context['seo_meta_form'] = seo_meta_form
    context['seo_url_form'] = seo_url_form
    context['page_title'] = u'%s' % (auction.title, )
    return render_to_response('administration/auctions/form.html', context)


@user_passes_test(lambda u: u.is_staff)
def auctions_delete(request, auction_id):
    auction = get_object_or_404(Auction.all_objects, pk=auction_id)
    auction.delete()
    return redirect('administration.views.auctions_index')


@user_passes_test(lambda u: u.is_staff and u.is_superuser)
def advertising_index(request):
    if request.method == 'POST':
        form = BulkBannersForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['action'] == 'delete':
                for item in form.cleaned_data['selected_items']:
                    item.delete()
            elif form.cleaned_data['action'] == 'publish':
                for item in form.cleaned_data['selected_items']:
                    item.is_published = True
                    item.save()
            elif form.cleaned_data['action'] == 'hide':
                for item in form.cleaned_data['selected_items']:
                    item.is_published = False
                    item.save()
        return redirect('administration.views.advertising_index')
    per_page = 20
    page = request.GET.get('page', 1)
    context = RequestContext(request)
    context = load_menu_context(context, request, show_secondary_menu=False)
    context['ADMIN_MENU_ACTIVE'] = 'ADVERTISING'
    banners_list = Banner.admin_objects.all()
    paginator = Paginator(banners_list, per_page)
    try:
        context['banners_list'] = paginator.page(page)
    except PageNotAnInteger:
        context['banners_list'] = paginator.page(1)
    except EmptyPage:
        context['banners_list'] = paginator.page(paginator.num_pages)
    return render_to_response('administration/advertising/index.html', context)


@user_passes_test(lambda u: u.is_staff and u.is_superuser)
def advertising_add_banner(request):
    context = RequestContext(request)
    context = load_menu_context(context, request, show_secondary_menu=False)
    context['ADMIN_MENU_ACTIVE'] = 'ADVERTISING'
    if request.method == 'POST':
        banner_form = BannerForm(request.POST, request.FILES)
        if banner_form.is_valid():
            banner_form.save()
            return redirect('administration.views.advertising_index')
    else:
        banner_form = BannerForm()
    context['banner_form'] = banner_form
    context['page_title'] = 'Добавить баннер'
    return render_to_response('administration/advertising/banner-form.html', context)


@user_passes_test(lambda u: u.is_staff and u.is_superuser)
def advertising_banner_edit(request, banner_id):
    banner_id = int(banner_id)
    banner = get_object_or_404(Banner.admin_objects, pk=banner_id)
    context = RequestContext(request)
    context = load_menu_context(context, request, show_secondary_menu=False)
    if request.method == 'POST':
        banner_form = BannerForm(request.POST, request.FILES, instance=banner)
        if banner_form.is_valid():
            banner_form.save()
            return redirect('administration.views.advertising_index')
    else:
        banner_form = BannerForm(instance=banner)
    context['banner'] = banner
    context['banner_form'] = banner_form
    context['page_title'] = banner.title
    return render_to_response('administration/advertising/banner-form.html', context)


@user_passes_test(lambda u: u.is_staff and u.is_superuser)
def advertising_banner_delete(request, banner_id):
    banner_id = int(banner_id)
    banner = get_object_or_404(Banner.admin_objects, pk=banner_id)
    banner.delete()
    return redirect('administration.views.advertising_index')


@user_passes_test(lambda u: u.is_staff and u.is_superuser)
def reports_index(request):
    context = RequestContext(request)
    context = load_menu_context(context, request, show_secondary_menu=False)
    context['ADMIN_MENU_ACTIVE'] = 'REPORTS'
    return render_to_response('administration/reports/index.html', context)


@user_passes_test(lambda u: u.is_staff and u.is_superuser)
def reports_view(request, report_type):
    export_csv = False
    if request.method == 'POST' and request.POST.get('export_csv'):
        export_csv = True
    report_types = {'offers-sales-users': reports_offers_sales_users,
                    'offers-sales-general': reports_offers_sales_general, 'bonuses-got': reports_bonuses_got,
                    'bonuses-spent': reports_bonuses_spent,
                    'bonuses-users': reports_bonuses_users,
                    'fitnesshouse-report': reports_fitnesshouse_report,
                    'person-restruct-report': reports_person_restruct,
    }
    if report_type in report_types:
        view = report_types[report_type]
        return view(request, export_csv)
    else:
        raise Http404


@user_passes_test(lambda u: u.is_staff and u.is_superuser)
def reports_bonuses_got(request, export_csv=False):
    context = RequestContext(request)
    context = load_menu_context(context, request, show_secondary_menu=False)
    context['ADMIN_MENU_ACTIVE'] = 'REPORTS'
    if request.method == 'POST':
        date_from = localtime(now()).date() - datetime.timedelta(days=6)
        date_to = localtime(now()).date()
        date_range_form = DateRangeForm(request.POST, initial={'date_from': date_from, 'date_to': date_to})
        if date_range_form.is_valid():
            if date_range_form.cleaned_data['date_from']:
                date_from = date_range_form.cleaned_data['date_from']
            if date_range_form.cleaned_data['date_to']:
                date_to = date_range_form.cleaned_data['date_to']
    else:
        date_from = localtime(now()).date() - datetime.timedelta(days=6)
        date_to = localtime(now()).date()
        date_range_form = DateRangeForm(initial={'date_from': date_from, 'date_to': date_to})
    context['date_range_form'] = date_range_form
    users = User.objects.all()
    date_from = datetime.datetime.fromordinal(date_from.toordinal())
    date_to += datetime.timedelta(days=1)
    date_to = datetime.datetime.fromordinal(date_to.toordinal())
    date_from = make_aware(date_from, get_current_timezone())
    date_to = make_aware(date_to, get_current_timezone())
    date_to -= datetime.timedelta(seconds=1)
    for user in users:
        bonuses_got = BonusTransactions.objects.filter(amount__gt=0, user=user,
                                                       add_date__gte=date_from,
                                                       add_date__lte=date_to,
                                                       is_completed=True).aggregate(models.Sum('amount'))
        if bonuses_got['amount__sum']:
            bonuses_got = bonuses_got['amount__sum']
        else:
            bonuses_got = 0
        user.bonuses_got = bonuses_got
    context['users'] = users
    if export_csv:
        response = HttpResponse(mimetype='text/csv')
        response['Content-Disposition'] = 'attachment; filename="bonuses_got.csv"'
        writer = csv.writer(response, delimiter=';')
        row = [
            u'Бонусов получено'.encode('cp1251'),
            (u'с %s по %s' % (timezone.localtime(date_from).strftime('%d.%m.%Y'), timezone.localtime(date_to).strftime('%d.%m.%Y'))).encode('cp1251'),
        ]
        writer.writerow(row)
        row = [u'Пользователь'.encode('cp1251'), u'Бонусов получено'.encode('cp1251')]
        writer.writerow(row)
        for user in context['users']:
            row = [('%s (%s)' % (user.get_full_name(), user.username)).encode('cp1251'), user.bonuses_got]
            writer.writerow(row)
        return response
    else:
        return render_to_response('administration/reports/bonuses_got.html', context)


@user_passes_test(lambda u: u.is_staff and u.is_superuser)
def reports_bonuses_users(request, export_csv=False):
    context = RequestContext(request)
    context = load_menu_context(context, request, show_secondary_menu=False)
    context['ADMIN_MENU_ACTIVE'] = 'REPORTS'
    if request.method == 'POST':
        date_from = localtime(now()).date() - datetime.timedelta(days=6)
        date_to = localtime(now()).date()
        date_range_form = DateRangeForm(request.POST, initial={'date_from': date_from, 'date_to': date_to})
        if date_range_form.is_valid():
            if date_range_form.cleaned_data['date_from']:
                date_from = date_range_form.cleaned_data['date_from']
            if date_range_form.cleaned_data['date_to']:
                date_to = date_range_form.cleaned_data['date_to']
    else:
        date_from = localtime(now()).date() - datetime.timedelta(days=6)
        date_to = localtime(now()).date()
        date_range_form = DateRangeForm(initial={'date_from': date_from, 'date_to': date_to})
    context['date_range_form'] = date_range_form
    date_from = datetime.datetime.fromordinal(date_from.toordinal())
    date_to += datetime.timedelta(days=1)
    date_to = datetime.datetime.fromordinal(date_to.toordinal())
    date_from = make_aware(date_from, get_current_timezone())
    date_to = make_aware(date_to, get_current_timezone())
    date_to -= datetime.timedelta(seconds=1)
    bonus_transactions = BonusTransactions.objects.filter(add_date__gte=date_from, add_date__lte=date_to, is_completed=True)
    context['bonus_transactions'] = bonus_transactions
    if export_csv:
        response = HttpResponse(mimetype='text/csv')
        response['Content-Disposition'] = 'attachment; filename="bonuses_users.csv"'
        writer = csv.writer(response, delimiter=';')
        row = [
            u'Продажи по акциям'.encode('cp1251'),
            (u'с %s по %s' % (timezone.localtime(date_from).strftime('%d.%m.%Y'), timezone.localtime(date_to).strftime('%d.%m.%Y'))).encode('cp1251'),
            ]
        writer.writerow(row)
        row = [
            u'Пользователь'.encode('cp1251'),
            u'Дата'.encode('cp1251'),
            u'Сумма'.encode('cp1251'),
            u'Описание'.encode('cp1251'),
            ]
        writer.writerow(row)
        temp_row = [
            '{{ transaction.user.get_full_name }} ({{ transaction.user.username }})',
            '{{ transaction.add_date }}',
            '{{ transaction.amount }}',
            '{{ transaction.comment }}',
            ]
        for transaction in bonus_transactions:
            row = []
            context = Context({'transaction':transaction})
            for item in temp_row:
                row.append(Template(item).render(context).encode('cp1251'))
            writer.writerow(row)
        return response
    else:
        return render_to_response('administration/reports/bonuses_users.html', context)

@user_passes_test(lambda u: u.is_staff and u.is_superuser)
def reports_offers_sales_general(request, export_csv=False):
    context = RequestContext(request)
    context = load_menu_context(context, request, show_secondary_menu=False)
    context['ADMIN_MENU_ACTIVE'] = 'REPORTS'
    if request.method == 'POST':
        date_from = localtime(now()).date() - datetime.timedelta(days=6)
        date_to = localtime(now()).date()
        date_range_form = DateRangeForm(request.POST, initial={'date_from': date_from, 'date_to': date_to})
        if date_range_form.is_valid():
            if date_range_form.cleaned_data['date_from']:
                date_from = date_range_form.cleaned_data['date_from']
            if date_range_form.cleaned_data['date_to']:
                date_to = date_range_form.cleaned_data['date_to']
    else:
        date_from = localtime(now()).date() - datetime.timedelta(days=6)
        date_to = localtime(now()).date()
        date_range_form = DateRangeForm(initial={'date_from': date_from, 'date_to': date_to})
    context['date_range_form'] = date_range_form
    offers = Offers.all_objects.all()
    date_from = datetime.datetime.fromordinal(date_from.toordinal())
    date_to += datetime.timedelta(days=1)
    date_to = datetime.datetime.fromordinal(date_to.toordinal())
    date_from = make_aware(date_from, get_current_timezone())
    date_to = make_aware(date_to, get_current_timezone())
    date_to -= datetime.timedelta(seconds=1)
    for offer in offers:
        if offer.is_abonement():
            sales = AbonementOrder.objects.filter(offer=offer, is_completed=True, add_date__gte=date_from, add_date__lte=date_to).count()
        elif offer.is_additional_service():
            sales = AdditionalServicesOrder.objects.filter(offer=offer, is_completed=True, add_date__gte=date_from, add_date__lte=date_to).count()
        else:
            sales = Order.objects.filter(offer=offer,
                                     is_completed=True,
                                     add_date__gte=date_from,
                                     add_date__lte=date_to).aggregate(models.Sum('quantity'))
            if sales['quantity__sum']:
                sales = sales['quantity__sum']
            else:
                sales = 0
        gift_sales_code_used = GiftOrder.objects.filter(offer=offer, is_completed=True, gift_code_used=True, add_date__gte=date_from, add_date__lte=date_to).count()
        gift_sales_code_unused = GiftOrder.objects.filter(offer=offer, is_completed=True, gift_code_used=False, add_date__gte=date_from, add_date__lte=date_to).count()
        offer.sales = sales - gift_sales_code_used
        offer.gift_sales = gift_sales_code_used + gift_sales_code_unused
        offer.sales_total = sales + gift_sales_code_unused
    context['offers'] = offers
    if export_csv:
        response = HttpResponse(mimetype='text/csv')
        response['Content-Disposition'] = 'attachment; filename="sales_general.csv"'
        writer = csv.writer(response, delimiter=';')
        row = [
            u'Продажи по акциям'.encode('cp1251'),
            (u'с %s по %s' % (timezone.localtime(date_from).strftime('%d.%m.%Y'), timezone.localtime(date_to).strftime('%d.%m.%Y'))).encode('cp1251'),
            ]
        writer.writerow(row)
        row = [
            u'Акция'.encode('cp1251'),
            u'Продажи'.encode('cp1251'),
            u'В подарок'.encode('cp1251'),
            u'Всего'.encode('cp1251'),
            u'Из них в подарок'.encode('cp1251'),
            u'Цена'.encode('cp1251'),
        ]
        writer.writerow(row)
        for offer in context['offers']:
            row = [
                offer.title.encode('cp1251'),
                offer.sales,
                offer.gift_sales,
                offer.sales_total,
                (u'%s руб. %s бонусов' % (offer.coupon_price_money, offer.coupon_price_bonuses)).encode('cp1251'),
            ]
            writer.writerow(row)
        return response
    else:
        return render_to_response('administration/reports/offers_sales_general.html', context)


@user_passes_test(lambda u: u.is_staff and u.is_superuser)
def reports_offers_sales_users(request, export_csv=False):
    context = RequestContext(request)
    context = load_menu_context(context, request, show_secondary_menu=False)
    context['ADMIN_MENU_ACTIVE'] = 'REPORTS'
    if request.method == 'POST':
        date_from = localtime(now()).date() - datetime.timedelta(days=6)
        date_to = localtime(now()).date()
        date_range_form = DateRangeForm(request.POST, initial={'date_from': date_from, 'date_to': date_to})
        if date_range_form.is_valid():
            if date_range_form.cleaned_data['date_from']:
                date_from = date_range_form.cleaned_data['date_from']
            if date_range_form.cleaned_data['date_to']:
                date_to = date_range_form.cleaned_data['date_to']
    else:
        date_from = localtime(now()).date() - datetime.timedelta(days=6)
        date_to = localtime(now()).date()
        date_range_form = DateRangeForm(initial={'date_from': date_from, 'date_to': date_to})
    context['date_range_form'] = date_range_form
    date_from = datetime.datetime.fromordinal(date_from.toordinal())
    date_to += datetime.timedelta(days=1)
    date_to = datetime.datetime.fromordinal(date_to.toordinal())
    date_from = make_aware(date_from, get_current_timezone())
    date_to = make_aware(date_to, get_current_timezone())
    date_to -= datetime.timedelta(seconds=1)
    orders = MetaOrder.objects.filter(
        is_completed=True,
        add_date__gte=date_from,
        add_date__lte=date_to
    ).order_by('-add_date')
    context['orders'] = orders
    if export_csv:
        response = HttpResponse(mimetype='text/csv')
        response['Content-Disposition'] = 'attachment; filename="sales_users.csv"'
        writer = csv.writer(response, delimiter=';')
        row = [
            u'Продажи по пользователям'.encode('cp1251'),
            (u'с %s по %s' % (timezone.localtime(date_from).strftime('%d.%m.%Y'), timezone.localtime(date_to).strftime('%d.%m.%Y'))).encode('cp1251'),
        ]
        writer.writerow(row)
        row = [
            u'Пользователь'.encode('cp1251'),
            u'Акция'.encode('cp1251'),
            u'Куплено в подарок'.encode('cp1251'),
            u'Цена'.encode('cp1251'),
            u'Время'.encode('cp1251'),
            u'Откуда пришел'.encode('cp1251')
        ]
        writer.writerow(row)
        temp_row = [
            u'{{ order.user.get_full_name }} ({{ order.user.username }})',
            u'{{ order.order_object.offer.title }}',
            u'{% if order.is_gift_order %}Да({% if  order.order_object.gift_code_used %}Получатель: {{ order.order_object.get_real_order.user.get_profile.get_name }}{% else %}Код еще не использован{% endif %}){% else %}Нет{% endif %}',
            u'{% if order.is_gift_suborder %}Получен в подарок{% else %}{% if order.order_object.price_type == 1 %}{{ order.order_object.price }} руб.{% elif order.order_object.price_type == 2 %}{{ order.order_object.price }} бонусов{% endif %}{% endif %}',
            u'{{ order.add_date }}',
            u'{{ order.order_object.visitor_info.referer }}',
        ]
        for order in context['orders']:
            row = []
            context = Context({'order':order})
            for item in temp_row:
                row.append(Template(item).render(context).encode('cp1251'))
            writer.writerow(row)
        return response
    else:
        return render_to_response('administration/reports/offers_sales_users.html', context)


@user_passes_test(lambda u: u.is_staff and u.is_superuser)
def reports_bonuses_spent(request, export_csv=False):
    context = RequestContext(request)
    context = load_menu_context(context, request, show_secondary_menu=False)
    context['ADMIN_MENU_ACTIVE'] = 'REPORTS'
    date_from = localtime(now()).date() - datetime.timedelta(days=6)
    date_to = localtime(now()).date()
    if request.method == 'POST':
        date_range_form = DateRangeForm(request.POST, initial={'date_from': date_from, 'date_to': date_to})
        if date_range_form.is_valid():
            if date_range_form.cleaned_data['date_from']:
                date_from = date_range_form.cleaned_data['date_from']
            if date_range_form.cleaned_data['date_to']:
                date_to = date_range_form.cleaned_data['date_to']
    else:
        date_range_form = DateRangeForm(initial={'date_from': date_from, 'date_to': date_to})
    context['date_range_form'] = date_range_form
    users = User.objects.all()
    date_from = datetime.datetime.fromordinal(date_from.toordinal())
    date_to += datetime.timedelta(days=1)
    date_to = datetime.datetime.fromordinal(date_to.toordinal())
    date_from = make_aware(date_from, get_current_timezone())
    date_to = make_aware(date_to, get_current_timezone())
    date_to -= datetime.timedelta(seconds=1)
    for user in users:
        bonuses_spent = BonusTransactions.objects.filter(amount__lt=0, user=user, add_date__gte=date_from,
                                                         add_date__lte=date_to,
                                                         is_completed=True).aggregate(models.Sum('amount'))
        if bonuses_spent['amount__sum']:
            bonuses_spent = bonuses_spent['amount__sum']
        else:
            bonuses_spent = 0
        user.bonuses_spent = bonuses_spent
    context['users'] = users
    if export_csv:
        response = HttpResponse(mimetype='text/csv')
        response['Content-Disposition'] = 'attachment; filename="bonuses_spent.csv"'
        writer = csv.writer(response, delimiter=';')
        row = [
            u'Бонусов потрачено'.encode('cp1251'),
            (u'с %s по %s' % (timezone.localtime(date_from).strftime('%d.%m.%Y'), timezone.localtime(date_to).strftime('%d.%m.%Y'))).encode('cp1251'),
        ]
        writer.writerow(row)
        row = [u'Пользователь'.encode('cp1251'), u'Бонусов потрачено'.encode('cp1251')]
        writer.writerow(row)
        for user in context['users']:
            row = [('%s (%s)' % (user.get_full_name(), user.username)).encode('cp1251'), user.bonuses_spent]
            writer.writerow(row)
        return response
    else:
        return render_to_response('administration/reports/bonuses_spent.html', context)

@user_passes_test(lambda u: u.is_staff and u.is_superuser)
def reports_fitnesshouse_report(request, export_csv=False):
    context = RequestContext(request)
    context = load_menu_context(context, request, show_secondary_menu=False)
    context['ADMIN_MENU_ACTIVE'] = 'REPORTS'
    if request.method == 'POST':
        date_from = localtime(now()).date() - datetime.timedelta(days=6)
        date_to = localtime(now()).date()
        date_range_form = DateRangeForm(request.POST, initial={'date_from': date_from, 'date_to': date_to})
        if date_range_form.is_valid():
            if date_range_form.cleaned_data['date_from']:
                date_from = date_range_form.cleaned_data['date_from']
            if date_range_form.cleaned_data['date_to']:
                date_to = date_range_form.cleaned_data['date_to']
    else:
        date_from = localtime(now()).date() - datetime.timedelta(days=6)
        date_to = localtime(now()).date()
        date_range_form = DateRangeForm(initial={'date_from': date_from, 'date_to': date_to})
    context['date_range_form'] = date_range_form
    date_from = datetime.datetime.fromordinal(date_from.toordinal())
    date_to += datetime.timedelta(days=1)
    date_to = datetime.datetime.fromordinal(date_to.toordinal())
    date_from = make_aware(date_from, get_current_timezone())
    date_to = make_aware(date_to, get_current_timezone())
    date_to -= datetime.timedelta(seconds=1)
    needed_order_types = []
    needed_order_types.append(ContentType.objects.get_for_model(AdditionalServicesOrder))
    needed_order_types.append(ContentType.objects.get_for_model(AbonementOrder))
    orders = MetaOrder.objects.filter(order_type__in=needed_order_types)
    orders = orders.filter(
        add_date__gte=date_from,
        add_date__lte=date_to
    )
    context['orders'] = orders
    if export_csv:
        response = HttpResponse(mimetype='text/csv')
        response['Content-Disposition'] = 'attachment; filename="bonuses_spent.csv"'
        writer = csv.writer(response, delimiter=';')
        row = [
            u'Просмотр заявок'.encode('cp1251'),
            (u'с %s по %s' % (timezone.localtime(date_from).strftime('%d.%m.%Y'), timezone.localtime(date_to).strftime('%d.%m.%Y'))).encode('cp1251'),
        ]
        writer.writerow(row)
        row = [
            u'МетаID заявки'.encode('cp1251'),
            u'Дата'.encode('cp1251'),
            u'Акция'.encode('cp1251'),
            u'Номер договора'.encode('cp1251'),
            u'Клуб'.encode('cp1251'),
            u'ФИО'.encode('cp1251'),
            u'Дата начала'.encode('cp1251'),
            u'Дата окончания'.encode('cp1251'),
            u'Сумма'.encode('cp1251'),
            u'Паспорт'.encode('cp1251'),
            u'Пол'.encode('cp1251'),
            u'Дата рождения'.encode('cp1251'),
            u'Контактный телефон'.encode('cp1251'),
            u'Электронный адрес'.encode('cp1251'),
            u'Оплачено'.encode('cp1251'),
            u'Номер транзакции'.encode('cp1251'),
            u'Способ оплаты'.encode('cp1251'),
        ]
        writer.writerow(row)
        for order in context['orders']:
            temp_row = [
                u'{{ order.pk }}',
                u'{{ order.add_date }}',
                u'{{ order.order_object.offer.title }}',
                u'{{ order.order_object.get_agreement_id }}',
                u'{{ order.order_object.additional_info.address.title }}',
                u'{{ order.order_object.additional_info.last_name }} {{ order.order_object.additional_info.first_name }} {{ order.order_object.additional_info.father_name }}',
                u'{% if order.is_completed %}{{ order.order_object.get_start_date }}{% endif %}',
                u'{% if order.is_completed %}{{ order.order_object.get_end_date }}{% endif %}',
                u'{{ order.order_object.get_price_display }}',
                u'{% if order.order_object.offer.is_abonement %}{{ order.order_object.additional_info.passport_code }}{{ order.order_object.additional_info.passport_number }}{% endif %}',
                u'{% if order.order_object.offer.is_abonement %}{{ order.order_object.additional_info.get_gender_display }}{% endif %}',
                u'{{ order.order_object.additional_info.birth_date }}',
                u'{{ order.order_object.additional_info.phone }}',
                u'{{ order.order_object.additional_info.email }}',
                u'{{ order.get_payment_date }}',
                u'{{ order.get_payment_id }}{% if order.paid_via_dol %}(ДОЛ: {{ order.get_dol_payment_info.paymentid }}){% endif %}',
                u'{{ order.get_paid_source_display }}',
            ]
            row = []
            context = Context({'order':order})
            for item in temp_row:
                row.append(Template(item).render(context).encode('cp1251'))
            writer.writerow(row)
        return response
    else:
        return render_to_response('administration/reports/fitnesshouse_report.html', context)


@user_passes_test(lambda u: u.is_staff and u.is_superuser)
def reports_person_restruct(request, export_csv=False):
    pass

@user_passes_test(lambda u: u.is_staff and u.is_superuser)
def reports_metaorder_details(request, metaorder_id):
    metaorder = get_object_or_404(MetaOrder, pk=metaorder_id)
    context = RequestContext(request)
    context = load_menu_context(context, request, show_secondary_menu=False)
    context['metaorder'] = metaorder
    return render_to_response('administration/reports/metaorder_details.html', context)


@user_passes_test(lambda u: u.is_staff)
def emails_index(request):
    context = RequestContext(request)
    smsbliss_gate = Gate(django_settings.SMSBLISS_LOGIN, django_settings.SMSBLISS_PASSWORD)
    context['sms_credits'] = smsbliss_gate.credits()
    context = load_menu_context(context, request, show_secondary_menu=False)
    context['ADMIN_MENU_ACTIVE'] = 'NEWSLETTERS'
    campaigns = NewsletterCampaign.objects.all()
    context['campaigns'] = campaigns
    return render_to_response('administration/emails/index.html', context)


@user_passes_test(lambda u: u.is_staff)
def emails_campaigns_add(request):
    context = RequestContext(request)
    if request.method == 'POST':
        campaign_form = NewsletterCampaignForm(request.POST)
        if campaign_form.is_valid():
            campaign_form.save()
            return redirect('administration.views.emails_index')
    else:
        campaign_form = NewsletterCampaignForm()
    context = load_menu_context(context, request, show_secondary_menu=False)
    context['ADMIN_MENU_ACTIVE'] = 'NEWSLETTERS'
    context['page_title'] = 'Добавить кампанию'
    context['campaign_form'] = campaign_form
    return render_to_response('administration/emails/campaign_form.html', context)


@user_passes_test(lambda u: u.is_staff)
def emails_campaigns_edit(request, campaign_id):
    context = RequestContext(request)
    campaign = get_object_or_404(NewsletterCampaign, pk=campaign_id)
    if request.method == 'POST':
        campaign_form = NewsletterCampaignForm(request.POST, instance=campaign)
        if campaign_form.is_valid():
            campaign_form.save()
            return redirect('administration.views.emails_index')
    else:
        campaign_form = NewsletterCampaignForm(instance=campaign)
    context = load_menu_context(context, request, show_secondary_menu=False)
    context['ADMIN_MENU_ACTIVE'] = 'NEWSLETTERS'
    context['page_title'] = campaign.title
    context['campaign_form'] = campaign_form
    context['campaign'] = campaign
    return render_to_response('administration/emails/campaign_form.html', context)


@user_passes_test(lambda u: u.is_staff)
def emails_campaigns_delete(request, campaign_id):
    campaign = get_object_or_404(NewsletterCampaign, pk=campaign_id)
    campaign.delete()
    return redirect('administration.views.emails_index')


@user_passes_test(lambda u: u.is_staff)
def emails_add(request):
    if request.method == "POST":
        email_form = NewsletterEmailForm(request.POST)
        if email_form.is_valid():
            email_form.save()
            return redirect('administration.views.emails_index')
    else:
        email_form = NewsletterEmailForm()
    context = RequestContext(request)
    context = load_menu_context(context, request, show_secondary_menu=False)
    context['ADMIN_MENU_ACTIVE'] = 'NEWSLETTERS'
    context['page_title'] = 'Добавить письмо'
    context['email_form'] = email_form
    return render_to_response('administration/emails/email_form.html', context)


@user_passes_test(lambda u: u.is_staff)
def sms_add(request):
    if request.method == "POST":
        sms_form = NewsletterSmsForm(request.POST)
        if sms_form.is_valid():
            sms_form.save()
            return redirect('administration.views.emails_index')
    else:
        sms_form = NewsletterSmsForm()
    context = RequestContext(request)
    context = load_menu_context(context, request, show_secondary_menu=False)
    context['ADMIN_MENU_ACTIVE'] = 'NEWSLETTERS'
    context['page_title'] = 'Добавить SMS'
    context['sms_form'] = sms_form
    return render_to_response('administration/emails/sms_form.html', context)


@user_passes_test(lambda u: u.is_staff)
def emails_edit(request, email_id):
    context = RequestContext(request)
    email = get_object_or_404(NewsletterEmail, pk=email_id)
    if request.method == "POST":
        email_form = NewsletterEmailForm(request.POST, instance=email)
        if email_form.is_valid():
            email_form.save()
            return redirect('administration.views.emails_index')
    else:
        email_form = NewsletterEmailForm(instance=email)
    context = load_menu_context(context, request, show_secondary_menu=False)
    context['ADMIN_MENU_ACTIVE'] = 'NEWSLETTERS'
    context['page_title'] = email.subject
    context['email_form'] = email_form
    context['email'] = email
    return render_to_response('administration/emails/email_form.html', context)

@user_passes_test(lambda u: u.is_staff)
def sms_edit(request, sms_id):
    context = RequestContext(request)
    sms = get_object_or_404(NewsletterSms, pk=sms_id)
    if request.method == "POST":
        sms_form = NewsletterSmsForm(request.POST, instance=sms)
        if sms_form.is_valid():
            sms_form.save()
            return redirect('administration.views.emails_index')
    else:
        sms_form = NewsletterSmsForm(instance=sms)
    context = load_menu_context(context, request, show_secondary_menu=False)
    context['ADMIN_MENU_ACTIVE'] = 'NEWSLETTERS'
    context['page_title'] = 'SMS'
    context['sms_form'] = sms_form
    context['sms'] = sms
    return render_to_response('administration/emails/sms_form.html', context)


@user_passes_test(lambda u: u.is_staff)
def emails_delete(request, email_id):
    email = get_object_or_404(NewsletterEmail, pk=email_id)
    email.delete()
    return redirect('administration.views.emails_index')


@user_passes_test(lambda u: u.is_staff)
def sms_delete(request, sms_id):
    sms = get_object_or_404(NewsletterSms, pk=sms_id)
    sms.delete()
    return redirect('administration.views.emails_index')


@user_passes_test(lambda u: u.is_staff and u.is_superuser)
def settings(request):
    context = RequestContext(request)
    context = load_menu_context(context, request)
    context['ADMIN_MENU_ACTIVE'] = 'SETTINGS'
    context['call_me_departments'] = CallMeSubjects.objects.all()
    if request.method == 'POST':
        settings_form = SettingsForm(request.POST, request.FILES)
        if settings_form.is_valid():
            settings_form.save()
            return redirect('administration_index')
    else:
        settings_form = SettingsForm()
    context['settings_form'] = settings_form
    return render_to_response('administration/settings/index.html', context)


@user_passes_test(lambda u: u.is_staff)
def ideas(request):
    context = RequestContext(request)
    context = load_menu_context(context, request, show_secondary_menu=False)
    context['ADMIN_MENU_ACTIVE'] = 'BUSINESS_IDEAS'
    new_ideas = BusinessIdea.objects.filter(is_reviewed=False)
    context['new_ideas'] = new_ideas
    ideas = BusinessIdea.objects.filter(is_reviewed=True).order_by('-add_date')
    page = request.GET.get('page', 1)
    per_page = 20
    paginator = Paginator(ideas, per_page)
    try:
        context['ideas'] = paginator.page(page)
    except PageNotAnInteger:
        context['ideas'] = paginator.page(1)
    except EmptyPage:
        context['ideas'] = paginator.page(paginator.num_pages)
    return render_to_response('administration/ideas/index.html', context)


@user_passes_test(lambda u: u.is_staff)
def ideas_edit(request, idea_id):
    idea = get_object_or_404(BusinessIdea.objects, pk=idea_id)
    context = RequestContext(request)
    context = load_menu_context(context, request, show_secondary_menu=False)
    context['ADMIN_MENU_ACTIVE'] = 'BUSINESS_IDEAS'
    context['idea'] = idea
    if request.method == 'POST':
        reward_form = IdeaRewardForm(request.POST)
        if reward_form.is_valid():
            if idea.is_reviewed:
                messages.error(request, 'Пользователь уже получал награду за эту идею')
            else:
                idea.apply_reward(reward_form.cleaned_data['reward'])
                return redirect('administration_ideas')
    else:
        reward_form = IdeaRewardForm()
    context['reward_form'] = reward_form
    return render_to_response('administration/ideas/view.html', context)


@user_passes_test(lambda u: u.is_staff)
def ideas_delete(request, idea_id):
    idea = get_object_or_404(BusinessIdea, pk=idea_id)
    idea.delete()
    return redirect('administration.views.ideas')


@user_passes_test(lambda u: u.is_staff)
def moderator(request):
    context = RequestContext(request)
    if request.method == 'POST':
        form = BulkFeedbacksForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['action'] == 'delete':
                for feedback in form.cleaned_data['selected_items']:
                    feedback.delete()
            elif form.cleaned_data['action'] == 'approve':
                for feedback in form.cleaned_data['selected_items']:
                    feedback.is_approved = True
                    feedback.save()
        return redirect('administration.views.moderator')
    context = load_menu_context(context, request)
    context['ADMIN_MENU_ACTIVE'] = 'MODERATION'
    feedbacks_list = UserFeedbacks.moderation_objects.all()
    page = request.GET.get('page', 1)
    per_page = 20
    paginator = Paginator(feedbacks_list, per_page)
    try:
        context['feedbacks_list'] = paginator.page(page)
    except PageNotAnInteger:
        context['feedbacks_list'] = paginator.page(1)
    except EmptyPage:
        context['feedbacks_list'] = paginator.page(paginator.num_pages)
    return render_to_response('administration/moderator/index.html', context)


class UsersListView(ListView):
    ADMIN_MENU_ACTIVE = 'USERS'
    template_name = 'administration/users/index.html'
    queryset = User.objects.filter(is_staff=False)
    context_object_name = 'users_list'
    paginate_by = 20
    form_class = BulkUsersForm

    @method_decorator(user_passes_test(lambda u: u.is_staff))
    def dispatch(self, request, *args, **kwargs):
        return super(UsersListView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(UsersListView, self).get_context_data(**kwargs)
        context = load_menu_context(context, self.request)
        if self.kwargs.get('admins_view'):
            context['ADMIN_MENU_ACTIVE'] = 'ADMINISTRATORS'
        else:
            context['ADMIN_MENU_ACTIVE'] = 'USERS'
        return context



    def post(self, request, *args, **kwargs):
        form = BulkUsersForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['action'] == 'activate':
                for item in form.cleaned_data['selected_items']:
                    item.is_active = True
                    item.save()
            elif form.cleaned_data['action'] == 'disable':
                for item in form.cleaned_data['selected_items']:
                    item.is_active = False
                    item.save()
            return redirect('administration_users_administrators')
        else:
            self.object_list = self.get_queryset()
            return self.render_to_response(self.get_context_data(object_list=self.object_list))


class UsersFormView(FormView):
    form_class = UserForm
    template_name = 'administration/users/form.html'
    success_url = reverse_lazy('administration_users')

    @method_decorator(user_passes_test(lambda u: u.is_staff))
    def dispatch(self, request, *args, **kwargs):
        user_id = kwargs.get('user_id')
        if user_id:
            user = get_object_or_404(User, pk=user_id)
            self.user_object = user
        else:
            self.user_object = None
        return super(UsersFormView, self).dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(UsersFormView, self).get_form_kwargs()
        if self.user_object:
            kwargs['instance'] = self.user_object
        return kwargs

    def get_initial(self):
        initial = {}
        if self.user_object:
            initial['username'] = self.user_object.username
            initial['email'] = self.user_object.email
            initial['is_active'] = self.user_object.is_active
            if self.user_object.is_superuser:
                initial['type'] = 'admin'
            elif self.user_object.is_staff:
                initial['type'] = 'operator'
        return initial

    def form_valid(self, form):
        form.save()
        if form.cleaned_data['type'] in ('admin','operator',):
            return redirect('administration_users_administrators')
        else:
            return redirect('administration_users')

    def get_context_data(self, **kwargs):
        context = super(UsersFormView, self).get_context_data(**kwargs)
        context = load_menu_context(context, self.request)
        context['ADMIN_MENU_ACTIVE'] = 'USERS'
        if self.user_object:
            context['page_title'] = self.user_object.username
        else:
            context['page_title'] = 'Добавить пользователя'
        return context


class PartnersPageListView(BaseAdminView, ListView):
    paginate_by = 20
    queryset = PartnersPage.objects.all()
    template_name = 'administration/partners/page_list.html'
    def get_context_data(self, **kwargs):
        context = super(PartnersPageListView, self).get_context_data(**kwargs)
        context['ADMIN_MENU_ACTIVE'] = 'PARTNERS_PAGE'
        return context
    def post(self, request, *args, **kwargs):
        form = BulkPartnersPageForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['action'] == 'delete':
                for item in form.cleaned_data['selected_items']:
                    item.delete()
            return redirect('administration_partners_page')
        else:
            self.object_list = self.get_queryset()
            return self.render_to_response(self.get_context_data(object_list=self.object_list))

class PartnersPageCreateView(BaseAdminView, CreateView):
    form_class = PartnersPageForm
    template_name = 'administration/partners/page_form.html'
    success_url = reverse_lazy('administration_partners_page')
    def get_context_data(self, **kwargs):
        context = super(PartnersPageCreateView, self).get_context_data(**kwargs)
        context['page_title'] = 'Добавить партнера'
        context['ADMIN_MENU_ACTIVE'] = 'PARTNERS_PAGE'
        return context

class PartnersPageUpdateView(BaseAdminView, UpdateView):
    pk_url_kwarg = 'partner_id'
    model = PartnersPage
    form_class = PartnersPageForm
    template_name = 'administration/partners/page_form.html'
    success_url = reverse_lazy('administration_partners_page')
    def get_context_data(self, **kwargs):
        context = super(PartnersPageUpdateView, self).get_context_data(**kwargs)
        context['page_title'] = self.get_object().title
        context['ADMIN_MENU_ACTIVE'] = 'PARTNERS_PAGE'
        return context


class ClubCardNumbersListView(SuperUserRequiredView, ListView):
    paginate_by = 20
    queryset = ClubCardNumbers.objects.all()
    template_name = 'administration/club_cards/list.html'
    def get_context_data(self, **kwargs):
        context = super(ClubCardNumbersListView, self).get_context_data(**kwargs)
        context['ADMIN_MENU_ACTIVE'] = 'CLUB_CARD_TEMPLATES'
        context = load_menu_context(context, self.request)
        return context
    def post(self, request, *args, **kwargs):
        form = BulkClubCardNumbersForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['action'] == 'delete':
                for item in form.cleaned_data['selected_items']:
                    item.delete()
            return redirect('administration_club_card_numbers_index')
        else:
            self.object_list = self.get_queryset()
            return self.render_to_response(self.get_context_data(object_list=self.object_list))


class ClubCardNumbersCreateView(SuperUserRequiredView, CreateView):
    form_class = ClubCardNumbersForm
    template_name = 'administration/club_cards/form.html'
    success_url = reverse_lazy('administration_club_card_numbers_index')
    def get_context_data(self, **kwargs):
        context = super(ClubCardNumbersCreateView, self).get_context_data(**kwargs)
        context['page_title'] = 'Добавить диапазон'
        context['ADMIN_MENU_ACTIVE'] = 'CLUB_CARD_TEMPLATES'
        return context


class ClubCardNumbersUpdateView(SuperUserRequiredView, UpdateView):
    pk_url_kwarg = 'number_id'
    model = ClubCardNumbers
    form_class = ClubCardNumbersForm
    template_name = 'administration/club_cards/form.html'
    success_url = reverse_lazy('administration_club_card_numbers_index')
    def get_context_data(self, **kwargs):
        context = super(ClubCardNumbersUpdateView, self).get_context_data(**kwargs)
        context['page_title'] = self.get_object().title
        context['ADMIN_MENU_ACTIVE'] = 'CLUB_CARD_TEMPLATES'
        return context

class CallMeSubjectCreateView(SuperUserRequiredView, CreateView):
    template_name = 'administration/call_me_form/form.html'
    success_url = reverse_lazy('administration_settings')
    form_class = CallMeSubjectForm
    def get_context_data(self, **kwargs):
        context = super(CallMeSubjectCreateView, self).get_context_data(**kwargs)
        context['page_title'] = 'Добавить отдел'
        context['ADMIN_MENU_ACTIVE'] = 'SETTINGS'
        return context
    def get_success_url(self):
        url = super(CallMeSubjectCreateView, self).get_success_url()
        url += '#call_me_departments'
        return url

class CallMeSubjectUpdateView(SuperUserRequiredView, UpdateView):
    pk_url_kwarg = 'department_id'
    model = CallMeSubjects
    form_class = CallMeSubjectForm
    template_name = 'administration/call_me_form/form.html'
    success_url = reverse_lazy('administration_settings')
    def get_success_url(self):
        url = super(CallMeSubjectUpdateView, self).get_success_url()
        url += '#call_me_departments'
        return url
    def get_context_data(self, **kwargs):
        context = super(CallMeSubjectUpdateView, self).get_context_data(**kwargs)
        context['page_title'] = self.get_object().title
        context['ADMIN_MENU_ACTIVE'] = 'SETTINGS'
        return context

@user_passes_test(lambda u: u.is_staff and u.is_superuser)
def call_me_subject_delete(request, department_id):
    subject = get_object_or_404(CallMeSubjects, pk=department_id)
    subject.delete()
    url = reverse_lazy('administration_settings')
    url += '#call_me_departments'
    return redirect(url)


def uploaded_photo(request):
    photo_id = request.GET.get('photo_id')
    if not photo_id:
        raise Http404
    photo_id = int(photo_id)
    photo = get_object_or_404(UploadedFile, pk=photo_id)
    context = RequestContext(request)
    context['photo'] = photo
    return render_to_response('administration/_uploaded_photo_item.html', context)

class ModelChangelogListView(SuperUserRequiredView, ListView):
    model = LogMessage
    template_name = 'administration/model_changelog.html'
    paginate_by = 50
    def get_context_data(self, **kwargs):
        context = super(ModelChangelogListView, self).get_context_data(**kwargs)
        context = load_menu_context(context, self.request, show_secondary_menu=True)
        context['ADMIN_MENU_ACTIVE'] = 'MODEL_CHANGELOG'
        return context

@csrf_exempt
@user_passes_test(lambda u: u.is_staff and u.is_superuser)
def metaorders_resend_notification(request, metaorder_id):
    if request.method == 'POST':
        metaorder = get_object_or_404(MetaOrder, pk=metaorder_id)
        result = {}
        if metaorder.order_object.is_completed:
            metaorder.order_object.send_notification()
            result['success'] = True
            result['message'] = 'Отправлено'
        else:
            result['success'] = False
            result['message'] = 'Заказ еще не оплачен'
        return HttpResponse(simplejson.dumps(result))
    else:
        return redirect('administration_index')