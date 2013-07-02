# -*- coding: utf-8 -*-
import datetime
import urllib2
import base64
import md5
import urlparse
import xml.etree.ElementTree as ElementTree

import requests
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.template.context import Context
from django.contrib.auth.models import User
from django.shortcuts import redirect
from django.conf import settings
from django.utils.timezone import now
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.urlresolvers import reverse_lazy
from django.contrib import messages

from contracts.models import ContractTransaction, ContractTransactionInfo
from contracts.forms import ContractPersonRestructingForm, ContractProlongationForm, PersonalContractForm, GetContractNumberForm
from offers.models import ProlongationOffers, ContractOrder
from .utils import send_notification, is_exclusive, clean_session, load_data_to_session, get_contract_data, calculate_dates


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


# Префиксы, доступные для переоформления
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
                if response['?status'][0] == '1' or response['?status'][
                    0] == '2': # status=1 и status=2 - успех, всё остальное - ошибки
                    #Грузим данные в сессию
                    load_data_to_session(request, response, 2)
                    messages.success(request, 'Теперь выберите новый договор.')
                    return redirect(
                        'prolongate_contract')  # Редирект на эту же страницу, форма будет уже для нового клиента
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
                if ContractOrder.objects.filter(user=request.user,
                                                new_contract_number=form.cleaned_data['contract_number'],
                                                is_completed=True).count():
                    messages.info(request, 'Данный договор уже переоформлен!')
                    return render_to_response('contracts/contract_form.html', context)
                    # Достаём данные по договору
                response = get_contract_data(request, form)
                try:
                    g = response['?status'][0]
                except KeyError:
                    raise Exception(response)

                if response['?status'][0] == '1' or response['?status'][0] == '2':
                    contract_index = response['dognumber'].index(request.session['user_contract_number'])
                    response_index = lambda key: response[key][
                        contract_index]  # Чтобы каждый раз не писать [contract_index]

                    if ContractOrder.objects.filter(user=request.user, old_contract_number=response_index('dognumber'),
                                                    is_completed=False).count():
                        messages.info(request, 'Ваш договор уже находится в обработке!')
                        return render_to_response('contracts/contract_form.html', context)
                        # if response['?status'][0] == '1' or response_index('?status') == '2':
                    # Договор найден
                    if len(response_index('dognumber').split('/')) > 1:
                        if response_index('type').encode('ISO-8859-1').decode('cp1251').lower().find(
                                u'визиты') != -1 or response_index('type').encode('ISO-8859-1').decode(
                                'cp1251').lower().find(u'визитов') != -1:
                            messages.info(request,
                                          'Данный договор нельзя перевести через интернет-сайт, обратитесь за информацией в отдел продаж 610-06-06')
                            return render_to_response('contracts/contract_form.html', context)
                        try:
                            # Проверка на префиксы договоров. Префиксом может быть число и латинские M, MB
                            int(response_index('dognumber').split('/')[0])
                        except ValueError:
                            # Значит префикс не число
                            if (response_index('dognumber').split('/')[0].find('M') != 0) or (
                                    response_index('dognumber').split('/')[0].find('MB') != 0):
                                messages.info(request,
                                              'Данный договор нельзя перевести через интернет-сайт, обратитесь за информацией в отдел продаж 610-06-06')
                                return render_to_response('contracts/contract_form.html', context)

                    # print response_index('fname').encode('cp1252').decode('cp1251'), request.user.first_name
                    # print response_index('lname').encode('cp1252').decode('cp1251'), request.user.last_name

                    if response_index('fname').encode('cp1252').decode(
                            'cp1251') != request.user.first_name and response_index('lname').encode('cp1252').decode(
                            'cp1251') != request.user.last_name:
                        messages.info(request,
                                      'Переоформление договоров доступно только с личного аккаунта Бонус-Хаус!')
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
                        messages.info(request,
                                      'Данный договор нельзя перевести через интернет-сайт, обратитесь за информацией в отдел продаж 610-06-06')
                        return render_to_response('contracts/contract_form.html', context)

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
                    'shash': md5.new('0.00' + cid + request.session.get('src_club') + request.session.get(
                        'type') + settings.FH_SALT).hexdigest(),
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

                comment = u'Переоформление договора %s на клиента %s %s  ' % (
                    other_info['cid'], new_user.first_name, new_user.last_name)
                transaction_info = ContractTransactionInfo()
                transaction_info.save()
                transaction = ContractTransaction(operation_type=1, user=request.user, amount=0, transaction_date=now(),
                                                  comment=comment,
                                                  transaction_object=transaction_info) #@TODO: Допилить транзакции
                transaction.save()
                order = ContractOrder()
                order.user = new_user
                order.old_user = request.user
                order.old_contract_number = request.session.get('dognumber')
                order.new_contract_number = cid
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

                request_params['bh_key'] = md5.new(str('0.00') + str(request.user.id) + str(
                    request_params['paymentid']) + settings.BH_PASSWORD).hexdigest(),  # md5 BH_KEY,
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

                    old_user_notification_context = Context({
                        'old_user_first_name': request.user.first_name,
                        'old_user_last_name': request.user.last_name,
                        'contract_number': request.session.get('dognumber'),
                        'club_name': request.session.get('src_club').decode('ISO-8859-1').encode('cp1252').decode(
                            'cp1251'),
                        'add_date': datetime.datetime.strptime(request.session['sdate'], '%Y.%m.%d'),
                        'end_date': datetime.datetime.strptime(request.session['edate'], '%Y.%m.%d'),
                        'cancelation_date': transaction.complete_date, # test
                        'new_user_first_name': new_user.first_name,
                        'new_user_last_name': new_user.last_name,
                        'new_passport_series': order.user_passport_series,
                        'new_passport_number': order.user_passport_number,
                    })

                    new_user_notification_context = Context({
                        'LINK': settings.BASE_URL + str(reverse_lazy('bonushouse.views.cabinet_abonements')),
                        'new_user_first_name': new_user.first_name,
                        'new_user_last_name': new_user.last_name,
                        'contract_number': cid,
                        'club_name': request.session.get('src_club').decode('ISO-8859-1').encode('cp1252').decode(
                            'cp1251'),
                        'start_date': datetime.datetime.strptime(request.session['sdate'], '%Y.%m.%d'),
                        'end_date': datetime.datetime.strptime(request.session['edate'], '%Y.%m.%d'),
                        'cancelation_date': transaction.complete_date, # test
                    })

                    # Уведомление старому пользователю о расторжении договора
                    send_notification(request.user.email, old_user_notification_context, 'PERSON_RESTRUCT_TEMPLATE',
                                      settings.CONTRACT_RESTRUCT_SUBJECT)
                    # Уведомление новому пользователю о переоформленном на него договоре
                    send_notification(new_user.email, new_user_notification_context, 'NEW_PERSON_RESTRUCT_TEMPLATE',
                                      settings.CONTRACT_RESTRUCT_SUBJECT)

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
def get_contract_number(request):
    context = RequestContext(request)
    form = GetContractNumberForm()
    context['form'] = form
    if request.method == 'POST' and request.POST:
        form = GetContractNumberForm(request.POST)
        if form.is_valid():
            request_params = dict(
                # чтобы найти договор по паспорту,вместо параметра &dognumber или &cardnumber
                # надо указать серию и номер паспорта в полях &pserial &pnumber
                pserial=form.cleaned_data.get('passport_series', ''),
                pnumber=form.cleaned_data.get('passport_number', ''),
                cardnumber=form.cleaned_data.get('clubcard_number', ''),
                other_info='',
                sid='300',
                bh_key=md5.new(str(request.user.id) + settings.BH_PASSWORD).hexdigest(),
                userid=str(request.user.id),
            )
            print request_params
            fh_url = settings.FITNESSHOUSE_NOTIFY_URL_DEBUG
            if settings.DEBUG:
                response = {'?status': ['0']}
            else:
                response = requests.get(fh_url, params=request_params, verify=False)
                response = urlparse.parse_qs(response.text.encode('ASCII'))
            if response.get('?status')[0] == '1' or response.get('?status')[0] == '2':
                context['status'] = 'not_active'
                # Ищем активный договор
                index = 0
                for activity in response['activity']:
                    if activity.startswith('1\r\n'):  # '0\r\n?status=2' '1\r\n?status=2'
                        context['status'] = 'OK'  # Нашли активный договор
                        # Отправляем данные в context для отображения
                        for key in response:
                            data = response[key] # Массив данных для разных договоров
                            context[key] = data[index if len(data) > index else 0].decode('cp1251')
                    index += 1
            else:
                context['status'] = 'not_found'
            context['request'] = request_params
            context['url'] = fh_url
            context['response'] = response
            return render_to_response('contracts/get_number_success.html', context)
        context['form'] = form
    return render_to_response('contracts/get_number.html', context)


@login_required
def club_restruct_contract(request):
    pass


@csrf_exempt
def back_to_1_step(request):
    """Возврат на шаг 1 при переоформлении (поиск договора)"""
    request.session['step'] = 1
    clean_session(request)
    return HttpResponse()

