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
from django.template.context import Context
from django.contrib.auth.models import User
from django.shortcuts import redirect
from django.conf import settings
from django.utils.timezone import now
from django.http import HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.core.urlresolvers import reverse_lazy
from django.core.exceptions import ObjectDoesNotExist

from datetime import timedelta
from django.contrib import messages

from contracts.models import ContractTransaction, ContractTransactionInfo
from contracts.forms import ContractClubRestructingForm, ContractPersonRestructingForm, ContractProlongationForm, PersonalContractForm
from offers.models import ProlongationOffers, ContractOrder

from .utils import send_notification, is_exclusive, clean_session

########################
# Коды операций:
# 1 - переоформление
# 2 - перевод
# 3 - продление
# 4 - смена вида договора
# 5 - заморозка
#########################

#@TODO: Рефакторинг этого говна
# С кодировками полный бардак

ALLOWED_PREFIXES = ('M', 'MB')

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
                    load_data_to_session(request, response, 2)
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
    if not request.session.get('step') or request.session.get('step') == 1:
        form = PersonalContractForm()
        context['form'] = form
        #  Получение данных по договору
        if request.method == 'POST':
            form = PersonalContractForm(request.POST)
            if form.is_valid():
                if ContractOrder.objects.filter(user=request.user, contract_number = form.cleaned_data['contract_number'], is_completed=True).count():
                    messages.info(request, 'Данный договор уже переоформлен!')
                    return render_to_response('contracts/contract_form.html', context)
                # Достаём данные по договору
                response = get_contract_data(request, form)
                print response
                if response['?status'][0] == '1' or response['?status'][0] == '2':
                    contract_index = response['dognumber'].index(request.session['user_contract_number'])
                    response_index = lambda key: response[key][contract_index]  # Чтобы каждый раз не писать [contract_index]

                    if ContractOrder.objects.filter(user=request.user, contract_number = response_index('dognumber'), is_completed=False).count():
                        messages.info(request, 'Ваш договор уже находится в обработке!')
                        return render_to_response('contracts/contract_form.html', context)
                    # if response['?status'][0] == '1' or response_index('?status') == '2':
                    # Договор найден
                    if len(response_index('dognumber').split('/')) > 1:
                        if response_index('type').encode('ISO-8859-1').lower().find('визиты') or response_index('type').encode('ISO-8859-1').lower().find('визитов'):
                            messages.info(request, 'Данный договор нельзя перевести через интернет-сайт, обратитесь за информацией в отдел продаж 610-06-06')
                            return render_to_response('contracts/contract_form.html', context)
                        try:
                            # Проверка на префиксы договоров. Префиксом может быть число и латинские M, MB
                            int(response_index('dognumber').split('/')[0])
                        except ValueError:
                            # Значит префикс не число
                            if (response_index('dognumber').split('/')[0].find('M') != 0) or (response_index('dognumber').split('/')[0].find('MB') != 0):
                                messages.info(request, 'Данный договор нельзя перевести через интернет-сайт, обратитесь за информацией в отдел продаж 610-06-06')
                                return render_to_response('contracts/contract_form.html', context)

                    # print response_index('fname').encode('cp1252').decode('cp1251'), request.user.first_name
                    # print response_index('lname').encode('cp1252').decode('cp1251'), request.user.last_name

                    if response_index('fname').encode('cp1252').decode('cp1251') != request.user.first_name and response_index('lname').encode('cp1252').decode('cp1251') != request.user.last_name:
                        messages.info(request, 'Переоформление договоров доступно только с личного аккаунта Бонус-Хаус!')
                        return redirect('person_restruct_contract')
                    elif response_index('activity').split('?')[0].replace('\r\n', '') != '1':
                        # Если договор не активен
                        messages.info(request, 'Договор не активен! Переоформлению не подлежит.')
                        return render_to_response('contracts/contract_form.html', context)
                    elif response_index('debt') != '0.00':
                        # Если по договору имеется задолженность
                        messages.info(request, 'Имеется задолженность по договору! Переоформлению не подлежит.')
                        return render_to_response('contracts/contract_form.html', context)
                    elif is_exclusive(response_index('sdate'), response_index('edate')):
                        # Если по договору имеется задолженность
                        messages.info(request, 'Данный договор нельзя перевести через интернет-сайт, обратитесь за информацией в отдел продаж 610-06-06')
                        return render_to_response('contracts/contract_form.html', context)
                    # elif response_index('type').lower().find('мультикарта') != -1:
                    #     # Мультикарты тоже нельзя переоформлять
                    #     messages.info(request, 'Это мультикарта! Переоформлению не подлежит.')
                    #     return render_to_response('contracts/contract_form.html', context)

                    # Всё ок, идём дальше
                    load_data_to_session(request, response, 2)  # Грузим данные в сессию, переход на шаг 2
                    messages.success(request, 'Теперь введите данные нового клиента.')
                    return redirect('person_restruct_contract')
                elif response['?status'][0] == '3':
                    messages.info(request, 'Ваш договор уже находится в обработке.')
                    return render_to_response('contracts/contract_form.html', context)
                elif response['?status'][0] == '-2' or response['?status'][0] == '0':
                    messages.info(request, 'Договор не найден или данные неверны!')
                    return render_to_response('contracts/contract_form.html', context)
    elif request.session.get('step') == 2:
        # Договор валидный и его можно переоформлять
        form = ContractPersonRestructingForm(request.user)
        context['form'] = form
        if request.method == 'POST':
            form = ContractPersonRestructingForm(request.user, request.POST)
            context = RequestContext(request)
            context['form'] = form
            if form.is_valid():
                cid = ''
                new_user = User.objects.get(email=form.cleaned_data['email'])

                if len(request.session.get('dognumber').split('/')) == 2:
                    cid = request.session.get('dognumber') + '/1'
                elif len(request.session.get('dognumber').split('/')) == 3:
                    old_number = request.session.get('dognumber').split('/')
                    old_number[-1] = str(int(old_number[-1]) + 1)
                    cid = '/'.join(old_number)
                elif len(request.session.get('dognumber').split('/')) == 1:
                    cid = request.session.get('dognumber') + '/1'

                other_info = {
                    'fname': new_user.first_name,
                    'lname': new_user.last_name,
                    'sname': '',
                    'email': new_user.email,
                    'phone': new_user.get_profile().phone.replace('(', ' ').replace(')', ' '),
                    'sex': u'жен.' if new_user.get_profile().gender == 0 else u'муж.',
                    'bd': new_user.get_profile().birth_date.strftime('%Y-%m-%d'),
                    'dognumber': request.session.get('dognumber'),
                    'pserial': form.cleaned_data['passport_series'],
                    'pnumber': form.cleaned_data['passport_number'],
                    'shash': md5.new('0.00' + cid + request.session.get('src_club') + request.session.get('type') + settings.FH_SALT).hexdigest(),
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
                # if settings.DEBUG:
                #     fh_url = settings.FITNESSHOUSE_NOTIFY_URL_DEBUG
                # else:
                fh_url = settings.FITNESSHOUSE_NOTIFY_URL

                comment = u'Переоформление договора %s на клиента %s %s  ' % (other_info['cid'], new_user.first_name, new_user.last_name)
                transaction_info = ContractTransactionInfo()
                transaction_info.save()
                transaction = ContractTransaction(operation_type=1, user=request.user, amount=0, transaction_date=now(), comment=comment, transaction_object=transaction_info) #@TODO: Допилить транзакции
                transaction.save()
                order = ContractOrder()
                order.user = new_user
                order.old_user = request.user
                order.contract_number = cid
                order.user_passport_series = form.cleaned_data['passport_series']
                order.user_passport_number = form.cleaned_data['passport_number']
                order.offer_name = request.session.get('type').decode('ISO-8859-1').encode('cp1252').decode('cp1251')
                order.club_name = request.session.get('src_club').decode('ISO-8859-1').encode('cp1252').decode('cp1251')
                order.old_start_date = datetime.datetime.strptime(request.session['sdate'], '%Y.%m.%d')
                order.end_date = datetime.datetime.strptime(request.session.get('edate'), '%Y.%m.%d')
                order.transaction_object = transaction
                order.save()
                request_params = {
                    'userid': str(request.user.id),
                    'amount': '0.00',
                    'paymode': '1',
                    }

                # Переводим все в cp1251
                for key in request_params.keys():
                    request_params[key] = request_params[key].encode('cp1251')
                if settings.DEBUG:
                    request_params['paymentid'] = '123456789' + str(transaction.transaction_id)
                else:
                    request_params['paymentid'] = transaction.transaction_id

                request_params['bh_key'] = md5.new(str('0.00') + str(request.user.id) + str(request_params['paymentid']) + settings.BH_PASSWORD).hexdigest(),  # md5 BH_KEY,
                #Урлкодируем и переводим в base64
                other_info_encoded = '&'
                encoded_list = []
                for key, value in other_info.items():
                    encoded_list.append(key + '=' + urllib2.quote(value))
                other_info_encoded = '&' + '&'.join(encoded_list)
                #other_info_encoded = '&' + urllib2.quote(dict([key, value] for key, value in other_info.items()))
                other_info_encoded = base64.b64encode(urllib2.unquote(other_info_encoded))
                request_params['other_info'] = other_info_encoded
                # Шлем запрос
                response = requests.get(fh_url, params=request_params, verify=False)

                # response = urlparse.parse_qs(response.text)
                xml_response = ElementTree.fromstring(response.text)
                code = xml_response.find('code').text
                comment = xml_response.find('comment').text
                if code == 'YES':
                    context['response'] = response
                    transaction.complete()
                    order.complete()
                    try:
                        old_order = ContractOrder.objects.get(contract_number=request.session['dognumber'], user=request.user)
                        old_order.delete()
                    except ObjectDoesNotExist:
                        pass

                    old_user_notification_context = Context({
                        'old_user_first_name': request.user.first_name,
                        'old_user_last_name': request.user.last_name,
                        'contract_number': request.session.get('dognumber'),
                        'club_name': request.session.get('src_club').decode('ISO-8859-1').encode('cp1252').decode('cp1251'),
                        'add_date': datetime.datetime.strptime(request.session['sdate'], '%Y.%m.%d'),
                        'end_date': datetime.datetime.strptime(request.session['edate'], '%Y.%m.%d'),
                        'cancelation_date': transaction.complete_date,  # test
                        'new_user_first_name': new_user.first_name,
                        'new_user_last_name': new_user.last_name,
                        'new_passport_series': order.user_passport_series,
                        'new_passport_number': order.user_passport_number,
                    })

                    new_user_notification_context = Context({
                        'LINK':settings.BASE_URL + str(reverse_lazy('bonushouse.views.cabinet_abonements')),
                        'new_user_first_name': new_user.first_name,
                        'new_user_last_name': new_user.last_name,
                        'contract_number': cid,
                        'club_name': request.session.get('src_club').decode('ISO-8859-1').encode('cp1252').decode('cp1251'),
                        'start_date': datetime.datetime.strptime(request.session['sdate'], '%Y.%m.%d'),
                        'end_date': datetime.datetime.strptime(request.session['edate'], '%Y.%m.%d'),
                        'cancelation_date': transaction.complete_date,  # test
                        })

                    # Уведомление старому пользователю о расторжении договора
                    send_notification(request.user.email, old_user_notification_context, 'PERSON_RESTRUCT_TEMPLATE', settings.CONTRACT_RESTRUCT_SUBJECT)
                    # Уведомление новому пользователю о переоформленном на него договоре
                    send_notification(new_user.email, new_user_notification_context, 'NEW_PERSON_RESTRUCT_TEMPLATE', settings.CONTRACT_RESTRUCT_SUBJECT)

                    #Чистим сессию
                    clean_session(request)
                    del request.session['step']
                    return render_to_response('contracts/success.html', context)
                else:
                    print code, comment
                    messages.info(request, 'Произошла ошибка!')
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
    request_params['passport'] = form.cleaned_data.get('passport_series') + form.cleaned_data.get('passport_number')  # test
    request_params['other_info'] = ''
    request_params['sid'] = '300'


    request.session['user_contract_number'] = form.cleaned_data['contract_number']
    # Переводим все в cp1251
    for key in request_params.keys():
        request_params[key] = request_params[key]
        # Шлем запрос
    # if settings.DEBUG:
        # fh_url = settings.FITNESSHOUSE_NOTIFY_URL_DEBUG
    # else:
    fh_url = settings.FITNESSHOUSE_NOTIFY_URL
    response = requests.get(fh_url, params=request_params, verify=False)
    response = urlparse.parse_qs(response.text)
    return response


def load_data_to_session(request, response, step):
    """Данные с сервера FH записываем в сессию"""
    contract_index = response['dognumber'].index(request.session['user_contract_number'])
    response_index = lambda key: response[key][contract_index]
    request.session['step'] = step  # Договор валидный, переход на следующий шаг
    request.session['src_id'] = response_index('src_id')
    request.session['fname'] = response_index('fname').encode('ISO-8859-1')
    request.session['lname'] = response_index('lname').encode('ISO-8859-1')
    request.session['bd'] = response_index('bd')
    request.session['dognumber'] = response_index('dognumber').encode('ISO-8859-1')
    request.session['src_club'] = response_index('src_club').encode('ISO-8859-1')
    request.session['sdate'] = response_index('sdate')
    request.session['edate'] = response_index('edate')
    request.session['type'] = response_index('type').encode('ISO-8859-1')# + '~ё+*&'


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

@csrf_exempt
def back_to_1_step(request):
    """Возврат на шаг 1 при переоформлении (поиск договора)"""
    request.session['step'] = 1
    clean_session(request)
    return HttpResponse()

