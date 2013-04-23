# -*- coding: utf-8 -*-
import datetime
import urllib, urllib2, base64, md5
import requests
import urlparse


from contracts.forms import ContractClubRestructingForm, ContractPersonRestructingForm, ContractProlongationForm, PersonalContractForm
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
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
from django.http import HttpResponseRedirect, QueryDict
from django.contrib.sites.models import get_current_site
from django.template.response import TemplateResponse
from offers.cart import ShoppingCart
from django.utils.translation import ugettext as _
from django.utils import timezone

from django.template import Context, Template
from django.core.mail import send_mail
from django.utils import simplejson
from django.contrib.sites.models import Site
from django import forms

from contracts.models import ContractTransaction



########################
# Коды операций:
# 1 - переоформление
# 2 - перевод
# 3 - продление
# 4 - смена вида договора
# 5 - заморозка
#########################


@login_required
def prolongate_contract(request):
    """Продление договоров и отсылка уведомлений на обработчик FH"""
    form = ContractProlongationForm()
    context = RequestContext(request)
    context['form'] = form
    if request.method == 'POST':
        pass
    return render_to_response('contracts/contract_form.html', context)


@login_required
def person_restruct_contract(request):
    """Переоформление договора на другого человека"""
    if not request.session.get('contract_valid'):
    #  Получение данных по договору
        form = PersonalContractForm()
        if request.method == 'POST':
            form = PersonalContractForm(request.POST)
            if form.is_valid():
                # Достаём данные по договору
                request_params = {}
                request_params['bh_key'] = md5.new(str(request.user.id) + settings.BH_PASSWORD).hexdigest()  # md5 BH_KEY
                request_params['userid'] = str(request.user.id)
                request_params['dognumber'] = form.cleaned_data['contract_number']
                request_params['passport'] = form.cleaned_data['passport_series'] + form.cleaned_data['passport_number']  # test
                request_params['other_info'] = ''
                request_params['sid'] = '300'

                # Переводим все в cp1251
                for key in request_params.keys():
                    request_params[key] = unicode(request_params[key]).encode('cp1251')
                    # Шлем запрос
                if settings.DEBUG:
                    fh_url = settings.FITNESSHOUSE_NOTIFY_URL_DEBUG
                else:
                    fh_url = settings.FITNESSHOUSE_NOTIFY_URL
                response = requests.get(fh_url, params=request_params, verify=False)
                response = urlparse.parse_qs(response.text)
                if response['?status'][0] == '1' or response['?status'][0] == '2':
                    request.session['contract_valid'] = True  # Договор валидный
                    request.session['src_id'] = response['src_id'][0]
                    request.session['dognumber'] = response['dognumber'][0]
                    request.session['src_club'] = response['src_club'][0]
                    messages.success(request, 'Теперь введите данные нового клиента.')
                    return redirect('person_restruct_contract')  # Редирект на эту же страницу, форма будет уже для нового клиента
    else:
        # Договор валидный и его можно переоформлять
        form = ContractPersonRestructingForm()
        if request.method == 'POST':
            del request.session['contract_valid']   # Удаляем ключ из сессии
            form = ContractPersonRestructingForm(request.POST)
            context = RequestContext(request)
            if form.is_valid():
                request_params = {}
                request_params['bh_key'] = md5.new(str(request.user.id) + settings.BH_PASSWORD).hexdigest()  # md5 BH_KEY
                request_params['userid'] = str(request.user.id)
                request_params['fname'] = form.cleaned_data['first_name']
                request_params['lname'] = form.cleaned_data['last_name']
                request_params['sname'] = form.cleaned_data['second_name']
                request_params['bd'] = datetime.datetime.strptime(form.cleaned_data['birthdate'], '%d.%m.%Y').strftime('%Y-%m-%d')
                request_params['dognumber'] = request.session['dognumber']
                request_params['passport'] = form.cleaned_data['passport_series'] + form.cleaned_data['passport_number']  # test
                request_params['other_info'] = ''
                request_params['sid'] = '301'
                request_params['type'] = '301'
                request_params['payment_id'] = ''
                del request.session['dognumber']
                del request.session['src_id']
                # Переводим все в cp1251
                for key in request_params.keys():
                    request_params[key] = unicode(request_params[key]).encode('cp1251')
                    # Шлем запрос
                if settings.DEBUG:
                    fh_url = settings.FITNESSHOUSE_NOTIFY_URL_DEBUG
                else:
                    fh_url = settings.FITNESSHOUSE_NOTIFY_URL
                request_params['src_club'] = request.session['src_club']
                del request.session['src_club']
                response = requests.get(fh_url, params=request_params, verify=False)
                response = urlparse.parse_qs(response.text)
                if response.get('?status') == '1' or response.get('?status') == '2':
                    context['response'] = response
                    comment = 'Переоформление договора %(number)s на клиента '
                    transaction = ContractTransaction(operation_type=1, user=request.user, amount=0, payment_date=now(), ) #@TODO: Допилить транзакции
                    return render_to_response('contracts/success.html', context)
                else:
                    messages.warning(request, 'Произошла ошибка')
                    return redirect('person_restruct_contract')
    context = RequestContext(request)
    context['form'] = form
    return render_to_response('contracts/contract_form.html', context)


@login_required
def club_restruct_contract(request):
    pass


