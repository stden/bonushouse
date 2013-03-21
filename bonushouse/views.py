# -*- coding: utf-8 -*-
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from bonushouse.forms import ProfileForm, DepositForm, LoginForm, RegisterForm, BusinessIdeaForm, ReferFriendForm, ExtendedSearchForm, ShareLinkForm
from django.shortcuts import redirect
from bonushouse.models import AccountDepositTransactions, UserProfile, BonusTransactions, CronFitnesshouseNotifications
from payment_gateways.models import PaymentRequest
from django.conf import settings
from django.contrib.auth import login
from offers.models import Order, AbonementOrder, CouponCodes, AdditionalServicesOrder, GiftOrder
from newsletter.models import NewsletterEmail, NewsletterSms
from django.utils.timezone import now
from django.http import HttpResponse, Http404
from django.db.models import Sum
from datetime import timedelta
from auctions.models import Auction
from flatpages.models import FlatPage
from django.views.generic import TemplateView, FormView
from django.utils.decorators import method_decorator
from dbsettings.utils import get_settings_value
from django.core.urlresolvers import reverse_lazy
from offers.models import Offers
from bonushouse.utils import total_seconds
import math
from offers.forms import GiftCodeForm, AbonementsClubCardForm, AbonementsAdditionalInfoForm
from django.contrib import messages
from django.contrib.auth import REDIRECT_FIELD_NAME, login as auth_login, logout as auth_logout
import urlparse
from django.http import HttpResponseRedirect, QueryDict
from django.contrib.sites.models import get_current_site
from django.template.response import TemplateResponse
from offers.cart import ShoppingCart
from django.utils.translation import ugettext as _
from django.utils import timezone
import datetime
from django.template import Context, Template
from django.core.mail import send_mail
from django.utils import simplejson

class LoginRequiredView(object):
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(LoginRequiredView, self).dispatch(request, *args, **kwargs)


def home(request, show_login=False):
    #Проверяем, пришел ли юзер по приглашению друга.
    if not request.user.is_authenticated():
        refered_by = request.GET.get('refered_by')
        if refered_by and refered_by != request.session.get('refered_by'):
            request.session['refered_by'] = refered_by
    context = RequestContext(request)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'login':
            login_form = LoginForm(request.POST)
            register_form = RegisterForm()
            if login_form.is_valid():
                login(request, login_form.user)
                redirect_url = request.GET.get('next')
                if redirect_url is None:
                    redirect_url = settings.LOGIN_REDIRECT_URL
                return redirect(redirect_url)
        elif action == 'register':
            login_form = LoginForm()
            register_form = RegisterForm(request.POST)
            if register_form.is_valid():
                user = register_form.save()
                login(request, user)
                return redirect('home')
        else:
            login_form = LoginForm()
            register_form = RegisterForm()
        context['login_form'] = login_form
        context['register_form'] = register_form
    context['is_home'] = True
    context['top3'] = get_top_users(3)
    shortest_offer = Offers.objects.order_by('end_date')[:1]
    cur_time = now()
    if shortest_offer.count():
        context['shortest_offer'] = shortest_offer[0]
        delta = context['shortest_offer'].end_date - cur_time
        total_secs = int(total_seconds(delta))
        hours = int(math.floor(total_secs/3600))
        remainder = total_secs % 3600
        minutes = int(math.floor(remainder/60))
        seconds = remainder % 60
        if hours > 99:
            hours = 99
            minutes = 59
            seconds = 59
        else:
            if hours < 10:
                hours = str(hours)
            if minutes < 10:
                minutes = str(minutes)
            if seconds < 10:
                seconds = str(seconds)
        context['shortest_offer_hours_left'] = hours
        context['shortest_offer_minutes_left'] = minutes
        context['shortest_offer_seconds_left'] = seconds
    try:
        context['home_page'] = FlatPage.objects.get(pk=settings.HOME_PAGE_ID)
    except:
        pass
    cur_time -= timedelta(hours=cur_time.hour, minutes=cur_time.minute, seconds=cur_time.second, microseconds=cur_time.microsecond)
    context['top_yesterday'] = get_top_users(1, cur_time-timedelta(days=1), cur_time)
    context['top_week'] = get_top_users(1, cur_time - timedelta(days=7), cur_time)
    context['show_login_overlay'] = show_login
    return render_to_response('home.html', context)

def login_view(request):
    return home(request, show_login=True)

def logout_view(request, next_page=None,
           template_name='registration/logged_out.html',
           redirect_field_name=REDIRECT_FIELD_NAME,
           current_app=None, extra_context=None):
    """
    Logs out the user and displays 'You are logged out' message.
    """
    cart = ShoppingCart(request)
    cart_contents = cart.get_contents()
    visitor_info = request.session['visitor_info']
    auth_logout(request)
    cart.set_contents(cart_contents)
    request.session['visitor_info'] = visitor_info
    redirect_to = request.REQUEST.get(redirect_field_name, '')
    if redirect_to:
        netloc = urlparse.urlparse(redirect_to)[1]
        # Security check -- don't allow redirection to a different host.
        if not (netloc and netloc != request.get_host()):
            return HttpResponseRedirect(redirect_to)

    if next_page is None:
        current_site = get_current_site(request)
        context = RequestContext(request)
        context.update({
            'site': current_site,
            'site_name': current_site.name,
            'title': _('Logged out')
        })
        if extra_context is not None:
            context.update(extra_context)
        return TemplateResponse(request, template_name, context,
            current_app=current_app)
    else:
        # Redirect to this page until the session has been cleared.
        return HttpResponseRedirect(next_page or request.path)


@login_required
def edit_profile(request):
    #Если в сессии есть реферер, а в модели нет, сохраняем в модель.
    if not request.user.get_profile().referer_checked:
        if request.session.get('refered_by'):
            try:
                referer = User.objects.get(pk=request.session.get('refered_by'))
                request.user.get_profile().refered_by = referer
            except User.DoesNotExist:
                pass
        request.user.get_profile().referer_checked = True
        request.user.get_profile().save()
    context = RequestContext(request)
    initial_data = {
        'first_name': request.user.first_name,
        'last_name': request.user.last_name,
        'email': request.user.email,
        'gender': request.user.get_profile().gender,
        'birth_date': request.user.get_profile().birth_date,
        'avatar': request.user.get_profile().avatar,
        'phone': request.user.get_profile().phone,
    }
    if request.method == 'POST':
        profile_form = ProfileForm(request.POST, request.FILES, initial=initial_data)
        if profile_form.is_valid():
            profile_form.save(request.user)
            return redirect('home')
    else:
        profile_form = ProfileForm(initial=initial_data)
    context['profile_form'] = profile_form
    return render_to_response('users/edit_profile.html', context)


@login_required
def cabinet(request):
    context = RequestContext(request)
    filter = request.GET.get('filter', 'active')
    my_coupons = CouponCodes.objects.filter(order__is_completed=True, order__user=request.user)
    if filter == 'all':
        pass
    elif filter == 'used':
        my_coupons = my_coupons.filter(is_used=True)
    elif filter == 'expired':
        my_coupons == my_coupons.filter(order__offer__end_date__lt=now())
    else:
        my_coupons = my_coupons.filter(order__offer__end_date__gt=now(),is_used=False)
    context['coupons_filter'] = filter
    context['my_coupons'] = my_coupons
    return render_to_response('users/cabinet.html', context)

@login_required
def cabinet_abonements(request):
    context = RequestContext(request)
    my_abonements = AbonementOrder.objects.filter(is_completed=True, user=request.user)
    context['my_abonements'] = my_abonements
    return render_to_response('users/cabinet_abonements.html', context)

@login_required
def cabinet_additional_services(request):
    context = RequestContext(request)
    my_abonements = AdditionalServicesOrder.objects.filter(is_completed=True, user=request.user)
    context['my_abonements'] = my_abonements
    return render_to_response('users/cabinet_additional_services.html', context)

@login_required
def cabinet_gifts(request):
    context = RequestContext(request)
    filter = 'gift'
    context['coupons_filter'] = filter
    my_coupons = GiftOrder.objects.filter(is_completed=True, user=request.user, gift_code_used=False)
    context['my_coupons'] = my_coupons
    return render_to_response('users/cabinet.html', context)


@login_required
def cabinet_coupons_print(request, coupon_id):
    context = RequestContext(request)
    coupon = get_object_or_404(CouponCodes, pk=coupon_id, order__is_completed=True, order__user=request.user)
    context['coupon'] = coupon
    context['offer'] = coupon.get_order().offer
    context['addresses'] = context['offer'].addresses.all()
    context['coupon_code'] = coupon.code
    context['barcode'] = coupon.get_barcode()
    context['offer_title'] = context['offer'].title
    context['end_date'] = context['offer'].end_date
    context['terms'] = context['offer'].terms
    return render_to_response('users/cabinet_coupons_print.html', context)

@login_required
def cabinet_gift_coupons_print(request, coupon_id):
    context = RequestContext(request)
    coupon = get_object_or_404(GiftOrder, pk=coupon_id, gift_code_used=False, is_completed=True, user=request.user)
    context['coupon'] = coupon
    context['offer'] = coupon.offer
    context['addresses'] = context['offer'].addresses.all()
    context['coupon_code'] = coupon.gift_code
    context['offer_title'] = context['offer'].title
    context['end_date'] = context['offer'].end_date
    context['terms'] = context['offer'].terms
    return render_to_response('users/cabinet_gift_coupons_print.html', context)

@login_required
def cabinet_abonements_print(request, abonement_id):
    context = RequestContext(request)
    abonement = get_object_or_404(AbonementOrder, pk=abonement_id, is_completed=True, user=request.user)
    context['abonement'] = abonement
    context['barcode'] = abonement.get_barcode()
    context['agreement_id'] = abonement.agreement_id
    context['additional_info'] = abonement.additional_info
    context['terms'] = abonement.offer.terms
    context['offer_title'] = abonement.offer.title
    context['add_date'] = abonement.get_start_date()
    if abonement.offer.abonements_term:
        context['end_date'] = abonement.get_end_date()
    context['price'] = abonement.get_price_display()
    context['partner'] = abonement.offer.partner
    return render_to_response('users/cabinet_abonements_print.html', context)


@login_required
def cabinet_additional_services_print(request, abonement_id):
    context = RequestContext(request)
    abonement = get_object_or_404(AdditionalServicesOrder, pk=abonement_id, is_completed=True, user=request.user)
    context['abonement'] = abonement
    context['agreement_id'] = abonement.get_agreement_id()
    context['add_date'] = abonement.add_date
    context['offer_title'] = abonement.offer.title
    context['additional_info'] = abonement.additional_info
    context['valid_term'] = u'с %s по %s' % (timezone.localtime(abonement.get_start_date()).strftime('%d.%m.%Y'), timezone.localtime(abonement.get_end_date()).strftime('%d.%m.%Y'))
    context['terms'] = abonement.offer.terms
    context['price'] = abonement.get_price_display()
    return render_to_response('users/cabinet_additional_services_print.html', context)


@login_required
def cabinet_auctions_print(request, auction_id):
    context = RequestContext(request)
    auction = get_object_or_404(Auction.all_objects, pk=auction_id, is_completed=True, winner=request.user)
    context['abonement'] = auction
    if auction.is_abonement():
        template_name = 'users/cabinet_abonements_print.html'
        context['barcode'] = auction.get_barcode()
        context['agreement_id'] = auction.get_agreement_id()
        context['additional_info'] = auction.abonements_additional_info
        context['terms'] = auction.description
        context['offer_title'] = auction.title
        context['add_date'] = auction.completed_date+datetime.timedelta(days=1)
        context['end_date'] = auction.completed_date + datetime.timedelta(days=auction.abonements_term+1)
        context['price'] = str(auction.get_winner_bid().amount) + ' руб.'
        context['partner'] = auction.partner
    elif auction.is_additional_service():
        template_name = 'users/cabinet_additional_services_print.html'
        context['agreement_id'] = auction.get_agreement_id()
        context['add_date'] = auction.completed_date
        context['offer_title'] = auction.title
        context['additional_info'] = auction.additional_services_additional_info
        context['terms'] = auction.description
        context['price'] = str(auction.get_winner_bid().amount) + ' руб.'
        completed_date = timezone.localtime(auction.completed_date)
        context['valid_term'] = u'с %s по %s' % (timezone.localtime((completed_date+timedelta(days=1))).strftime('%d.%m.%Y'), timezone.localtime((completed_date+timedelta(days=auction.additional_services_term+1))).strftime('%d.%m.%Y'))
    else:
        template_name = 'users/cabinet_coupons_print.html'
        context['addresses'] = auction.addresses.all()
        context['coupon_code'] = auction.get_coupon_code()
        context['barcode'] = auction.get_barcode()
        context['offer_title'] = auction.title
        context['end_date'] = auction.completed_date + timedelta(days=30)
        context['terms'] = auction.description
    return render_to_response(template_name, context)


@login_required
def cabinet_auctions(request):
    context = RequestContext(request)
    my_auctions = Auction.all_objects.filter(is_completed=True, winner=request.user, coupon_code_used=False)
    context['my_auctions'] = my_auctions
    return render_to_response('users/cabinet_auctions.html', context)


@login_required
def deposit_account(request):
    context = RequestContext(request)
    if request.method == 'POST':
        deposit_form = DepositForm(request.POST)
        if deposit_form.is_valid():
            deposit = AccountDepositTransactions(user=request.user, amount=deposit_form.cleaned_data['amount'],
                                                 comment='Пополнение личного счета')
            deposit.save()
            payment_request = PaymentRequest(inner_transaction=deposit, amount=deposit.amount,
                                             comment="Bonus-House.ru. Пополнение личного счета. Пользователь #%s"
                                             % (deposit.user.pk,))
            payment_request.save()
            context = RequestContext(request)
            context['amount'] = deposit_form.cleaned_data['amount']
            context['nickname'] = request.user.email
            context['order_id'] = payment_request.pk
            return render_to_response('payments/dol/redirect_form.html', context)
    else:
        deposit_form = DepositForm()
    context['deposit_form'] = deposit_form
    return render_to_response('users/deposit_account.html', context)


@login_required
def buy_bonuses(request):
    context = RequestContext(request)
    if request.method == 'POST':
        deposit_form = DepositForm(request.POST)
        if deposit_form.is_valid():
            bonus_transaction = BonusTransactions(user=request.user,
                                                  amount=int(float(deposit_form.cleaned_data['amount']) /
                                                             float(context['BONUS_PRICE'])),
                                                  comment='Пополнение личного счета')
            bonus_transaction.save()
            payment_request = PaymentRequest(inner_transaction=bonus_transaction,
                                             amount=deposit_form.cleaned_data['amount'],
                                             comment="Bonus-House.ru. Покупка бонусов. Пользователь #%s" %
                                             (bonus_transaction.user.pk,))
            payment_request.save()
            context = RequestContext(request)
            context['amount'] = deposit_form.cleaned_data['amount']
            context['nickname'] = request.user.email
            context['order_id'] = payment_request.pk
            return render_to_response('payments/dol/redirect_form.html', context)
    else:
        deposit_form = DepositForm()
    context['deposit_form'] = deposit_form
    return render_to_response('users/buy_bonuses.html', context)


@login_required
def deposit_account_log(request):
    context = RequestContext(request)
    deposit_log = AccountDepositTransactions.objects.filter(user=request.user).order_by('-add_date')
    context['deposit_log'] = deposit_log
    return render_to_response('users/deposit_log.html', context)


@login_required
def suggest_business_idea(request):
    context = RequestContext(request)
    if request.method == 'POST':
        idea_form = BusinessIdeaForm(request.POST, request.FILES)
        if idea_form.is_valid():
            idea_form.instance.user = request.user
            idea_form.save()
            return redirect('suggest_idea_success')
    else:
        idea_form = BusinessIdeaForm()
    context['idea_form'] = idea_form
    return render_to_response('ideas/form.html', context)

@login_required
def suggest_business_idea_success(request):
    context = RequestContext(request)
    return render_to_response('ideas/success.html', context)


class ReferFriendView(LoginRequiredView, FormView):
    form_class = ReferFriendForm
    template_name = 'users/refer_friend_form.html'
    success_url = reverse_lazy('refer_friend_success')
    def get_context_data(self, **kwargs):
        context = super(ReferFriendView, self).get_context_data(**kwargs)
        context['description_text'] = get_settings_value('REFER_FRIEND_DESCRIPTION_TEXT')
        return context
    def form_valid(self, form):
        form.save(self.request.user)
        return super(ReferFriendView, self).form_valid(form)


class ReferFriendSuccessView(LoginRequiredView, TemplateView):
    template_name = 'users/refer_friend_success.html'

class ExtendedSearchFormView(FormView):
    form_class = ExtendedSearchForm
    template_name = 'search/extended-search.html'
    def get_context_data(self, **kwargs):
        result = super(ExtendedSearchFormView, self).get_context_data(**kwargs)
        #Определяем диапазон цен среди действующих акций
        cheapest_offer = Offers.objects.order_by('coupon_price_money')[:1]
        if cheapest_offer.count():
            result['price_range_min'] = cheapest_offer[0].coupon_price_money
            highest_offer = Offers.objects.order_by('-coupon_price_money')[:1]
            result['price_range_max'] = highest_offer[0].coupon_price_money
        else:
            result['price_range_min'] = 100
            result['price_range_max'] = 20000
        return result
    def form_valid(self, form):
        search_result = form.search()
        nothing_found = False
        if not search_result.count():
            nothing_found = True
        return self.render_to_response(self.get_context_data(search_result=search_result, form=form, nothing_found=nothing_found))



def cron(request):
    #Пересчет возраста
    profiles = UserProfile.objects.all()
    for profile in profiles:
        if profile.age != profile.calculate_age():
            profile.age = profile.calculate_age()
            profile.save()
    #Отправка рассылок
    current_time = now()
    email_letters = NewsletterEmail.objects.filter(is_sent=False, send_date__lte=current_time)
    for letter in email_letters:
        emails = []
        for campaign in letter.campaigns.all():
            emails += campaign.get_subscriber_emails_list()
        emails = list(set(emails))
        for email in emails:
            letter.send(email)
        letter.is_sent = True
        letter.save()
    newsletter_sms = NewsletterSms.objects.filter(is_sent=False, send_date__lte=current_time)
    for sms in newsletter_sms:
        phones = []
        for campaign in sms.campaigns.all():
            phones += campaign.get_subscriber_phones_list()
        phones = list(set(phones))
        for phone in phones:
            sms.send(phone)
        sms.is_sent = True
        sms.save()
    #Завершаем истекшие аукционы
    auctions = Auction.all_objects.filter(is_completed=False, end_date__lte=current_time)
    for auction in auctions:
        auction.complete()
    #Отправляем уведомления в базу FitnessHouse
    fh_notifications = CronFitnesshouseNotifications.objects.filter(is_completed=False)
    for notification in fh_notifications:
        notification.send()
    #Обновляем поисковые индексы
    #from haystack.management.commands.update_index import Command
    #Command().handle()
    return HttpResponse('OK')


class CallMeView(TemplateView):
    template_name = 'call_me_success.html'


def top(request):
    context = RequestContext(request)
    context['top'] = get_top_users(10)
    return render_to_response('top.html', context)

@login_required
def cabinet_gift_code_form(request):
    context = RequestContext(request)
    if request.method == 'POST':
        code_form = GiftCodeForm(request.POST)
        if code_form.is_valid():
            additional_info_form_active = request.POST.get('additional_info_form_active')
            if additional_info_form_active == '1':
                additional_info_form_active = True
            else:
                additional_info_form_active = False
            if code_form.gift_order.offer.is_abonement():
                if additional_info_form_active:
                    additional_info_form = AbonementsAdditionalInfoForm(request.POST, offer=code_form.gift_order.offer)
                    if additional_info_form.is_valid():
                        additional_info_form.save()
                        code_form.gift_order.create_real_order(request.user, request.session['visitor_info'], additional_info=additional_info_form.instance)
                        messages.info(request, (u'Поздравляем! Вы получили в подарок договор %s' % (code_form.gift_order.offer.title)))
                        return redirect('cabinet_additional_services')
                else:
                    additional_info_form = AbonementsAdditionalInfoForm(offer=code_form.gift_order.offer)
                context['additional_info_form'] = additional_info_form
            elif code_form.gift_order.offer.is_additional_service():
                if additional_info_form_active:
                    additional_info_form = AbonementsClubCardForm(request.POST, offer=code_form.gift_order.offer)
                    if additional_info_form.is_valid():
                        additional_info_form.save()
                        code_form.gift_order.create_real_order(request.user, request.session['visitor_info'], additional_info=additional_info_form.instance)
                        messages.info(request, (u'Поздравляем! Вы получили в подарок абонемент %s' % (code_form.gift_order.offer.title)))
                        return redirect('cabinet_additional_services')
                else:
                    additional_info_form = AbonementsClubCardForm(offer=code_form.gift_order.offer)
                context['additional_info_form'] = additional_info_form
            else:
                code_form.gift_order.create_real_order(request.user, request.session['visitor_info'])
                messages.info(request, (u'Поздравляем! Вы получили в подарок купон %s' % (code_form.gift_order.offer.title)))
                return redirect('cabinet')
    else:
        code_form = GiftCodeForm()
    context['code_form'] = code_form
    return render_to_response('users/cabinet_gift_code_form.html', context)


def get_top_users(count=3, date_from=None, date_to=None):
    result = []
    transactions = BonusTransactions.objects.filter(is_completed=True, amount__gt=0)
    if date_from:
        transactions = transactions.filter(add_date__gte=date_from)
    if date_to:
        transactions = transactions.filter(add_date__lte=date_to)
    transactions = transactions.values('user').annotate(bonuses_acquired=Sum('amount')).order_by('-bonuses_acquired')[:count]
    for transaction in transactions:
        result.append({'user':User.objects.get(pk=transaction['user']),'bonuses_acquired':transaction['bonuses_acquired']})
    if len(result):
        return result
    else:
        return None

def share_link(request):
    redirect_url = request.POST.get('url','/')
    message = ''
    response = {}
    if request.method == 'POST':
        share_link_form = ShareLinkForm(request.POST)
        if share_link_form.is_valid():
            response['success'] = True
            share_link_context = Context({'LINK':settings.BASE_URL+share_link_form.cleaned_data['url'], 'NAME': share_link_form.cleaned_data['name'], 'SENDER': request.user.get_profile().get_name()})
            share_link_template = Template(get_settings_value('SHARE_LINK_EMAIL_TEMPLATE'))
            message = share_link_template.render(share_link_context)
            subject = get_settings_value('SHARE_LINK_EMAIL_SUBJECT')
            to = share_link_form.cleaned_data['email']
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [to, ], True)
            if request.is_ajax():
                message = u'Спасибо! Мы отправим ссылку вашему другу в самое ближайшее время. Приятных покупок!'
            else:
                messages.info(request, u'Спасибо! Мы отправим ссылку вашему другу в самое ближайшее время. Приятных покупок!')
        else:
            response['success'] = False
            for field in share_link_form:
                for error in field.errors:
                    if request.is_ajax():
                        message += u"%s - %s<br/>" % (field.label, error)
                    else:
                        messages.error(request, (u'%s - %s' % (field.label, error)))
    if request.is_ajax():
        response['message'] = message
        return HttpResponse(simplejson.dumps(response))
    else:
        return redirect(redirect_url)