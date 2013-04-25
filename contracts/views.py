# -*- coding: utf-8 -*-
import datetime
import urllib, urllib2, base64, md5
import requests
import urlparse

from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import redirect
from django.conf import settings
from django.utils.timezone import now
from django.http import HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from bonushouse.models import AccountDepositTransactions, UserProfile, BonusTransactions, CronFitnesshouseNotifications
from payment_gateways.models import PaymentRequest

from django.contrib.auth import login
from offers.models import Order, AbonementOrder, CouponCodes, AdditionalServicesOrder, GiftOrder
from newsletter.models import NewsletterEmail, NewsletterSms

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

from contracts.models import ContractTransaction, ContractTransactionInfo
from contracts.forms import ContractClubRestructingForm, ContractPersonRestructingForm, ContractProlongationForm, PersonalContractForm


########################
# Коды операций:
# 1 - переоформление
# 2 - перевод
# 3 - продление
# 4 - смена вида договора
# 5 - заморозка
#########################

#@TODO: Рефакторинг этого говна



@login_required
def prolongate_contract(request):
    """Продление договоров"""
    context = RequestContext(request)
    form = PersonalContractForm()
    context['form'] = form
    # request.session.clear()
    if not request.session.get('contract_valid'):
        form = PersonalContractForm()
        context['form'] = form
        #  Получение данных по договору
        if request.method == 'POST':
            form = PersonalContractForm(request.POST)
            if form.is_valid():
                # Достаём данные по договору
                response = get_contract_data(request, form)
                if response['?status'][0] == '1' or response['?status'][0] == '2': # status=1 и status=2 - успех, всё остальное - ошибки
                    #Грузим данные в сессию
                    load_data_to_session(request, response)
                    messages.success(request, 'Теперь введите новую дату, до которой необходимо продлить договор.')
                    return redirect('prolongate_contract')  # Редирект на эту же страницу, форма будет уже для нового клиента
    else:
        form = ContractProlongationForm()
        context['form'] = form

        return render_to_response('contracts/contract_prolongation_form.html', context)
    return render_to_response('contracts/contract_form.html', context)


@login_required
def person_restruct_contract(request):
    """Переоформление договора на другого человека"""
    context = RequestContext(request)
    form = PersonalContractForm()
    context['form'] = form
    if not request.session.get('contract_valid'):
        form = PersonalContractForm()
        context['form'] = form
        #  Получение данных по договору
        if request.method == 'POST':
            form = PersonalContractForm(request.POST)
            if form.is_valid():
                # Достаём данные по договору
                response = get_contract_data(request, form)
                if response['?status'][0] == '1' or response['?status'][0] == '2':
                    load_data_to_session(request, response)
                    messages.success(request, 'Теперь введите данные нового клиента.')
                    return redirect('person_restruct_contract')  # Редирект на эту же страницу, форма будет уже для нового клиента
    else:
        # Договор валидный и его можно переоформлять
        form = ContractPersonRestructingForm(request.user)
        context['form'] = form
        if request.method == 'POST':
            form = ContractPersonRestructingForm(request.user, request.POST)
            context = RequestContext(request)
            context['form'] = form
            if form.is_valid():
                del request.session['contract_valid']   # Удаляем ключ из сессии

                new_user = User.objects.get(email=form.cleaned_data['email'])
                cid = request.session['dognumber']

                if len(request.session['dognumber'].split('/')) == 2:
                    cid = request.session['dognumber'] + '/1'
                elif len(request.session['dognumber'].split('/')) == 3:
                    first_number = request.session['dognumber'].split('/')[:-1]  # Номер договора без слэша
                    cid = first_number + str(int(request.session['dognumber'].split('/')[-1]) + 1)

                other_info = {
                    'fname': new_user.first_name,
                    'lname': new_user.last_name,
                    'sname': form.cleaned_data['second_name'],
                    'email': new_user.email,
                    'phone': new_user.get_profile().phone.replace('(', ' ').replace(')', ' '),
                    'sex': u'жен.' if new_user.get_profile().gender == 0 else u'муж.',
                    'bd': new_user.get_profile().birth_date.strftime('%Y-%m-%d'),
                    'dognumber': request.session['dognumber'],
                    'pserial': form.cleaned_data['passport_series'],
                    'pnumber': form.cleaned_data['passport_number'],
                    'shash': md5.new('0.00' + cid + request.session['src_club'] + request.session['type'] + settings.FH_SALT).hexdigest(),
                    'sid': '301',
                    'sdate': request.session['sdate'],
                    'edate': request.session['edate'],
                    'cid': cid,
                    'src_id': request.session['src_id'],
                    'src_club': request.session['src_club'],
                }

                # Всё в cp1251
                for key in other_info.keys():
                    if key != 'src_club':
                        other_info[key] = unicode(other_info[key]).encode('cp1251')
                other_info['type'] = request.session['type']
                if settings.DEBUG:
                    fh_url = settings.FITNESSHOUSE_NOTIFY_URL_DEBUG
                else:
                    fh_url = settings.FITNESSHOUSE_NOTIFY_URL
                # if response.get('?status') == '1' or response.get('?status') == '2':
                comment = u'Переоформление договора %s на клиента %s %s  ' % (other_info['cid'], new_user.first_name, new_user.last_name)
                transaction_info = ContractTransactionInfo()
                transaction_info.save()
                transaction = ContractTransaction(operation_type=1, user=request.user, amount=0, transaction_date=now(), comment=comment, transaction_object=transaction_info) #@TODO: Допилить транзакции
                transaction.save()
                request_params = {
                    'userid': str(request.user.id),
                    'amount': '0.00',
                    'paymode': '1',
                    }
                del request.session['dognumber']
                del request.session['src_id']
                del request.session['src_club']
                # Переводим все в cp1251
                for key in request_params.keys():
                    request_params[key] = request_params[key].encode('cp1251')
                if settings.DEBUG:
                    request_params['paymentid'] = '123456789' + str(transaction.transaction_id)
                else:
                    request_params['paymentid'] = transaction.transaction_id
                request_params['bh_key'] = md5.new('0.00' + str(request.user.id) + request_params['paymentid'] + settings.BH_PASSWORD).hexdigest(),  # md5 BH_KEY,
                #Урлкодируем и переводим в base64
                other_info_encoded = '&' + urllib.urlencode(dict([key, value] for key, value in other_info.items()))
                other_info_encoded = base64.b64encode(urllib2.unquote(other_info_encoded).replace('+',' '))
                request_params['other_info'] = other_info_encoded
                # Шлем запрос
                print request_params['other_info']
                response = requests.get(fh_url, params=request_params, verify=False)
                response = urlparse.parse_qs(response.text)

                context['response'] = response
                return render_to_response('contracts/success.html', context)
                # else:
                #     messages.warning(request, 'Произошла ошибка')
                #     return redirect('person_restruct_contract')

    return render_to_response('contracts/contract_form.html', context)


@login_required
def club_restruct_contract(request):
    pass


def get_contract_data(request, form):
    """Достаёт данные по договору, возвращает словарь с ответом"""
    request_params = {}
    request_params['bh_key'] = md5.new(str(request.user.id) + settings.BH_PASSWORD).hexdigest()  # md5 BH_KEY
    request_params['userid'] = str(request.user.id)
    request_params['dognumber'] = form.cleaned_data['contract_number']
    request_params['passport'] = form.cleaned_data['passport_series'] + form.cleaned_data['passport_number']  # test
    request_params['other_info'] = ''
    request_params['sid'] = '300'

    # Переводим все в cp1251
    for key in request_params.keys():
        request_params[key] = request_params[key]
        # Шлем запрос
    if settings.DEBUG:
        fh_url = settings.FITNESSHOUSE_NOTIFY_URL_DEBUG
    else:
        fh_url = settings.FITNESSHOUSE_NOTIFY_URL
    response = requests.get(fh_url, params=request_params, verify=False)
    response = urlparse.parse_qs(response.text)
    return response


def load_data_to_session(request, response):
    """Данные с сервера FH записываем в сессию"""
    request.session['contract_valid'] = True  # Договор валидный
    request.session['src_id'] = response['src_id'][0]
    request.session['dognumber'] = response['dognumber'][0].encode('ISO-8859-1')
    request.session['src_club'] = response['src_club'][0].encode('ISO-8859-1')
    request.session['sdate'] = response['sdate'][0]
    request.session['edate'] = response['edate'][0]
    request.session['type'] = response['type'][0].encode('ISO-8859-1')# + '~ё+*&'

@csrf_exempt
def calculate_price(request):
    if request.method == 'POST' and request.is_ajax():
        end_date = datetime.datetime.strptime(request.session.get('edate'), '%Y.%m.%d')
        new_date = datetime.datetime.strptime(request.POST.get('new_date'), '%d.%m.%Y')
        print (end_date-new_date).days
        #prolongation_term = new_date - end_date
    return HttpResponse()