# -*- coding: utf-8 -*-
from django.shortcuts import get_object_or_404, render_to_response, redirect
from partners.models import Partner, PartnersPage
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from bonushouse.forms import FeedbacksForm
from bonushouse.models import UserFeedbacks, UserRatings, PincodeTransaction
from offers.models import CouponCodes
from django.contrib import messages
from django.views.generic import TemplateView, ListView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import user_passes_test
from partners.menu import load_menu_context
from offers.models import Offers
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from offers.forms import OffersForm
from seo.forms import SeoModelMetaForm, SeoModelUrlForm
from partners.forms import BulkPartnerFeedbacksForm, PinCodeForm
from django.http import Http404
from django.utils.timezone import now
# Create your views here.

def partner_page(request, partner_id):
    context = RequestContext(request)
    partner = get_object_or_404(Partner, pk=partner_id)
    if partner.admin_user == request.user:
        can_write_replies = True
    else:
        can_write_replies = False
    context['can_write_replies'] = can_write_replies
    context['partner'] = partner
    if request.method == 'POST':
        if (request.user.is_staff or can_write_replies) and request.POST.get('admin-reply'):
            feedback_form = FeedbacksForm()
            admin_reply = request.POST.get('admin_reply')
            feedback_id = request.POST.get('feedback_id')
            if feedback_id:
                try:
                    feedback_id = int(feedback_id)
                    feedback = UserFeedbacks.objects.get(pk=feedback_id)
                    if not request.user.is_staff and feedback.content_object.admin_user != request.user:
                        raise Http404
                    feedback.admin_reply = admin_reply
                    feedback.save()
                    return redirect(partner.get_url())
                except:
                    pass
        else:
            feedback_form = FeedbacksForm(request.POST)
            if feedback_form.is_valid():
                feedback_form.instance.content_object = partner
                feedback_form.instance.user = request.user
                feedback_form.save()
                rating = UserRatings(content_object=feedback_form.instance, user=request.user, rating=feedback_form.cleaned_data['rating'])
                rating.save()
                messages.info(request, 'Спасибо! Ваш отзыв отправлен на проверку администрации.')
                return redirect(partner.get_url())
    else:
        feedback_form  = FeedbacksForm()
    context['feedback_form'] = feedback_form
    return render_to_response('partners/partner_page.html', context)

class BasePartnerMenuView(object):
    @method_decorator(user_passes_test(lambda u: u.get_profile().is_partner()))
    def dispatch(self, request, *args, **kwargs):
        return super(BasePartnerMenuView, self).dispatch(request, *args, **kwargs)
    def get_context_data(self, **kwargs):
        context = super(BasePartnerMenuView, self).get_context_data(**kwargs)
        context = load_menu_context(context)
        return context

class MenuIndexView(BasePartnerMenuView, TemplateView):
    template_name = 'partners/menu_index.html'

@user_passes_test(lambda u: u.get_profile().is_partner())
def menu_offers_index(request):
    per_page = 20
    page = request.GET.get('page', 1)
    context = RequestContext(request)
    context = load_menu_context(context)
    context['ADMIN_MENU_ACTIVE'] = 'Акции'
    offers_list = Offers.all_objects.filter(partner__admin_user=request.user)
    paginator = Paginator(offers_list, per_page)
    try:
        context['offers_list'] = paginator.page(page)
    except PageNotAnInteger:
        context['offers_list'] = paginator.page(1)
    except EmptyPage:
        context['offers_list'] = paginator.page(paginator.num_pages)
    return render_to_response('partners/menu/offers/index.html', context)


@user_passes_test(lambda u: u.get_profile().is_partner())
def menu_offers_add(request):
    context = RequestContext(request)
    context = load_menu_context(context)
    context['ADMIN_MENU_ACTIVE'] = 'Акции'
    if request.method == 'POST':
        offers_form = OffersForm(request.POST, partner_user=request.user)
        seo_meta_form = SeoModelMetaForm(request.POST)
        seo_url_form = SeoModelUrlForm(request.POST)
        if offers_form.is_valid() and seo_meta_form.is_valid() and seo_url_form.is_valid():
            offers_form.instance.type = 1
            instance = offers_form.save()
            instance.is_published = False
            instance.save()
            seo_meta_form.instance.content_object = offers_form.instance
            seo_meta_form.save()
            seo_url_form.instance.content_object = offers_form.instance
            seo_url_form.save()
            return redirect('partners.views.menu_offers_index')
    else:
        offers_form = OffersForm(partner_user=request.user)
        seo_meta_form = SeoModelMetaForm()
        seo_url_form = SeoModelUrlForm()
    context['offers_form'] = offers_form
    context['seo_meta_form'] = seo_meta_form
    context['seo_url_form'] = seo_url_form
    context['page_title'] = 'Добавить акцию'
    return render_to_response('partners/menu/offers/form.html', context)


@user_passes_test(lambda u: u.get_profile().is_partner())
def menu_offers_edit(request, offer_id):
    offer_id = int(offer_id)
    offer = get_object_or_404(Offers.all_objects, pk=offer_id, partner__admin_user=request.user)
    context = RequestContext(request)
    context = load_menu_context(context)
    context['ADMIN_MENU_ACTIVE'] = 'Акции'
    if request.method == 'POST':
        offers_form = OffersForm(request.POST, request.FILES, instance=offer, partner_user=request.user)
        seo_meta_form = SeoModelMetaForm(request.POST, instance=offer.get_seo_meta_object())
        seo_url_form = SeoModelUrlForm(request.POST, instance=offer.get_seo_url_object())
        if request.POST.get('delete') is not None:
            offer.delete()
            return redirect('partners.views.menu_offers_index')
        else:
            if offers_form.is_valid() and seo_meta_form.is_valid() and seo_url_form.is_valid():
                offers_form.instance.type = 1
                instance = offers_form.save()
                instance.is_published = False
                instance.save()
                seo_meta_form.save()
                seo_url_form.save()
                return redirect('partners.views.menu_offers_index')
    else:
        offers_form = OffersForm(instance=offer, partner_user=request.user)
        seo_meta_form = SeoModelMetaForm(instance=offer.get_seo_meta_object())
        seo_url_form = SeoModelUrlForm(instance=offer.get_seo_url_object())

    context['offers_form'] = offers_form
    context['seo_meta_form'] = seo_meta_form
    context['seo_url_form'] = seo_url_form
    context['page_title'] = offer.title
    context['offer'] = offer
    return render_to_response('partners/menu/offers/form.html', context)


@user_passes_test(lambda u: u.get_profile().is_partner())
def menu_moderator(request):
    context = RequestContext(request)
    if request.method == 'POST':
        form = BulkPartnerFeedbacksForm(request.POST, partner_user=request.user)
        if form.is_valid():
            if form.cleaned_data['action'] == 'delete':
                for feedback in form.cleaned_data['selected_items']:
                    feedback.delete()
            elif form.cleaned_data['action'] == 'approve':
                for feedback in form.cleaned_data['selected_items']:
                    feedback.is_approved = True
                    feedback.save()
        return redirect('partners.views.menu_moderator')
    context = load_menu_context(context)
    context['ADMIN_MENU_ACTIVE'] = 'Модерация'
    feedbacks_list = UserFeedbacks.moderation_objects.filter(partner_user=request.user)
    page = request.GET.get('page', 1)
    per_page = 20
    paginator = Paginator(feedbacks_list, per_page)
    try:
        context['feedbacks_list'] = paginator.page(page)
    except PageNotAnInteger:
        context['feedbacks_list'] = paginator.page(1)
    except EmptyPage:
        context['feedbacks_list'] = paginator.page(paginator.num_pages)
    return render_to_response('partners/menu/moderator/index.html', context)


@user_passes_test(lambda u: u.get_profile().is_partner())
def pin_codes(request):
    context = RequestContext(request)
    context = load_menu_context(context)
    context['ADMIN_MENU_ACTIVE'] = 'Проверка пин-кодов'
    if request.method == 'POST':
        pin_code_form = PinCodeForm(request.POST, partner_user=request.user)
        use_pin_code = request.POST.get('use_pin_code')

        if pin_code_form.is_valid():
            code = CouponCodes.objects.get(code=pin_code_form.cleaned_data['pin_code'], is_used=False)
            if code.get_order().offer.type == 1 and not code.get_order().offer.activation_due_date:
                messages.info(request, 'У акции не указан срок активации! Акция %s' % code.get_order().offer.get_administration_edit_url())
                return redirect('partner_menu_pin_codes')
            else:
                if code.get_order().offer.activation_due_date.date() < now().date():
                    messages.info(request, 'Невозможно погасить! Истёк срок действия купона!')
                    return redirect('partner_menu_pin_codes')
                elif use_pin_code is not None:
                    pin_code_form.pin_code_code.set_used()
                    order = pin_code_form.pin_code_code.order_set.all()[0]
                    transaction = PincodeTransaction(action_name=order.offer.title,
                                                     price=order.price,
                                                     consumer=order.user,
                                                     buy_date=order.add_date,
                                                     maturity_date=now(),
                                                     operator=request.user,
                                                     is_gift=pin_code_form.pin_code_code.is_gift,
                                                     add_date=now(),
                                                     is_completed=True)
                    #TODO Если купон подарен, то указать User, кому подарен
                    # if pin_code_form.pin_code_code.is_gift:

                    transaction.save()
                    messages.info(request, 'Пин-код помечен, как использованный')
                    return redirect('partner_menu_pin_codes')
    else:
        pin_code_form = PinCodeForm(partner_user=request.user)
    context['pin_code_form'] = pin_code_form
    return render_to_response('partners/menu/pin_code_form.html', context)

@user_passes_test(lambda u: u.get_profile().is_partner())
def reports(request):
    context = RequestContext(request)
    context = load_menu_context(context)
    context['ADMIN_MENU_ACTIVE'] = 'Отчеты'
    context['offers_list'] = Offers.all_objects.filter(partner__admin_user=request.user)
    return render_to_response('partners/menu/reports.html', context)


class PartnersPageListView(ListView):
    template_name = 'partners/page.html'
    model = PartnersPage