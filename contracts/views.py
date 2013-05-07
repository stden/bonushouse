# -*- coding: utf-8 -*-
import logging
import datetime
import urllib, urllib2, base64, md5
import requests
import urlparse

import xml.etree.ElementTree as ElementTree

from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import redirect
from django.conf import settings
from django.utils.timezone import now
from django import forms
from django.http import HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from payment_gateways.models import PaymentRequest


from datetime import timedelta
from django.contrib import messages

from contracts.models import ContractTransaction, ContractTransactionInfo
from contracts.forms import ContractClubRestructingForm, ContractPersonRestructingForm, ContractProlongationForm, PersonalContractForm
from offers.models import ProlongationOffers


########################
# Коды операций:
# 1 - переоформление
# 2 - перевод
# 3 - продление
# 4 - смена вида договора
# 5 - заморозка
#########################

#@TODO: Рефакторинг этого говна


# Get an instance of a logger

logger = logging.getLogger(__name__)


@login_required
def prolongate_contract(request):
    """Продление договоров"""
    context = RequestContext(request)
    form = PersonalContractForm()
    context['form'] = form
    # del request.session['contract_valid']

    if not request.session.get('contract_valid'):
        form = PersonalContractForm()
        context['form'] = form
        #  Получение данных по договору
        if request.method == 'POST':
            form = PersonalContractForm(request.POST)
            if form.is_valid():
                # Достаём данные по договору
                response = get_contract_data(request, form)
                total_time = calculate_dates(request, response)
                print total_time
                if response['?status'][0] == '1' or response['?status'][0] == '2': # status=1 и status=2 - успех, всё остальное - ошибки
                    #Грузим данные в сессию
                    load_data_to_session(request, response)
                    messages.success(request, 'Теперь выберите новый договор.')
                    return redirect('prolongate_contract')  # Редирект на эту же страницу, форма будет уже для нового клиента
    else:
        form = ContractProlongationForm(queryset=ProlongationOffers.all_objects.all())
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
                elif response['?status'][0] == '-2':
                    messages.info(request, 'Договор не найден!')
                    # r['message'] = render_to_string('_form_errors.html', context)
                    return render_to_response('contracts/contract_form.html', context)

    else:
        # Договор валидный и его можно переоформлять
        form = ContractPersonRestructingForm(request.user)
        context['form'] = form
        if request.method == 'POST':
            form = ContractPersonRestructingForm(request.user, request.POST)
            context = RequestContext(request)
            context['form'] = form
            if form.is_valid():

                new_user = User.objects.get(email=form.cleaned_data['email'])
                cid = request.session['dognumber']

                if len(request.session['dognumber'].split('/')) == 2:
                    cid = request.session['dognumber'] + '/1'
                elif len(request.session['dognumber'].split('/')) == 3:
                    old_number = request.session['dognumber'].split('/')
                    old_number[-1] = str(int(old_number[-1]) + 1)
                    cid = '/'.join(old_number)

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
                #if settings.DEBUG:
                fh_url = settings.FITNESSHOUSE_NOTIFY_URL_DEBUG
                #else:
                #    fh_url = settings.FITNESSHOUSE_NOTIFY_URL
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
                # for key in request_params.keys():
                #     request_params[key] = request_params[key].encode('cp1251')
                if settings.DEBUG:
                    request_params['paymentid'] = '123456789' + str(transaction.transaction_id)
                else:
                    request_params['paymentid'] = transaction.transaction_id
                logger.info(request_params)
                request_params['bh_key'] = md5.new('0.00' + str(request.user.id) + request_params['paymentid'] + settings.BH_PASSWORD).hexdigest(),  # md5 BH_KEY,
                #Урлкодируем и переводим в base64
                other_info_encoded = '&' + urllib.urlencode(dict([key, value] for key, value in other_info.items()))
                other_info_encoded = base64.b64encode(urllib2.unquote(other_info_encoded).replace('+',' '))
                request_params['other_info'] = other_info_encoded
                # Шлем запрос
                response = requests.get(fh_url, params=request_params, verify=False)
                # response = urlparse.parse_qs(response.text)
                xml_response = ElementTree.fromstring(response.text)
                code = xml_response.find('code').text
                comment = xml_response.find('comment').text
                if code == 'YES' and comment == 'NO':
                    del request.session['contract_valid']   # Удаляем ключ из сессии
                    print code, comment
                    context['response'] = response
                    return render_to_response('contracts/success.html', context)
                else:
                    messages.info(request, 'Произошла ошибка!')
                    del request.session['contract_valid']   # Удаляем ключ из сессии
                    return render_to_response('contracts/contract_form.html', context)
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

    request.session['user_contract_number'] = form.cleaned_data['contract_number']
    # Переводим все в cp1251
    for key in request_params.keys():
        request_params[key] = request_params[key]
        # Шлем запрос
    # if settings.DEBUG:
    fh_url = settings.FITNESSHOUSE_NOTIFY_URL_DEBUG
    # else:
        # fh_url = settings.FITNESSHOUSE_NOTIFY_URL
    response = requests.get(fh_url, params=request_params, verify=False)
    response = urlparse.parse_qs(response.text)
    print response
    return response


def load_data_to_session(request, response):
    """Данные с сервера FH записываем в сессию"""
    contract_index = response['dognumber'].index(request.session['user_contract_number'])
    request.session['contract_valid'] = True  # Договор валидный
    request.session['src_id'] = response['src_id'][contract_index]
    request.session['dognumber'] = response['dognumber'][contract_index].encode('ISO-8859-1')
    request.session['src_club'] = response['src_club'][contract_index].encode('ISO-8859-1')
    request.session['sdate'] = response['sdate'][contract_index]
    request.session['edate'] = response['edate'][contract_index]
    request.session['type'] = response['type'][contract_index].encode('ISO-8859-1')# + '~ё+*&'


def calculate_dates(request, response):
    i = 0
    total_time = 0
    print response
    while i < len(response['sdate']):
        start_date = lambda i: datetime.datetime.strptime(response['sdate'][i], '%Y.%m.%d')
        end_date = lambda i: datetime.datetime.strptime(response['edate'][i], '%Y.%m.%d')
        if end_date(i) < start_date(i + 1):
            print 'PARALLEL'
        i += 1
    # end_date = datetime.datetime.strptime(request.session.get('edate'), '%Y.%m.%d')
    # new_date = datetime.datetime.strptime(request.POST.get('new_date'), '%d.%m.%Y')
    # print (end_date-new_date).days
    #prolongation_term = new_date - end_date
    return total_time