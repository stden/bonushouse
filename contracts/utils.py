# -*- coding: utf-8 -*-
import collections
import datetime
import md5
import urlparse
import xml.etree.ElementTree as ET

import requests
from django.template.base import Template
from django.conf import settings
from django.core.mail import send_mail

from dbsettings.utils import get_settings_value
from offers.models import ContractOrder


def send_notification(email, context, settings_value, subject):
    notification_template = Template(get_settings_value(settings_value))
    notification_context = context
    message = notification_template.render(notification_context)
    subject = subject
    to = [email, ]
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, to, True)


def is_exclusive(start_date_str, end_date_str):
    """Проверка на эксклюзивы (срок действия 100 лет (36500 дней)"""
    start_date = datetime.datetime.strptime(start_date_str, '%Y.%m.%d')
    end_date = datetime.datetime.strptime(end_date_str, '%Y.%m.%d')
    if (end_date - start_date).days >= 36500:
        return True
    else:
        return False


def clean_session(request):
    try:
        del request.session['src_id']
        del request.session['fname']
        del request.session['lname']
        del request.session['bd']
        del request.session['dognumber']
        del request.session['src_club']
        del request.session['sdate']
        del request.session['edate']
        del request.session['type']
    except KeyError as e:
        print 'ERROR', e


def get_contract_data(request, form):
    """Достаёт данные по договору, возвращает словарь с ответом"""
    request_params = {'bh_key': md5.new(str(request.user.id) + settings.BH_PASSWORD).hexdigest(),
                      'userid': str(request.user.id),
                      'dognumber': form.cleaned_data['contract_number'],
                      'passport': form.cleaned_data.get('passport_series') + form.cleaned_data.get('passport_number'),
                      'other_info': '',
                      'sid': '300'}
    request.session['user_contract_number'] = form.cleaned_data['contract_number']
    # Переводим все в cp1251
    #for key in request_params.keys():
    #    request_params[key] = request_params[key]
    if settings.DEBUG:
        fh_url = settings.FITNESSHOUSE_NOTIFY_URL_DEBUG
    else:
        fh_url = settings.FITNESSHOUSE_NOTIFY_URL
    response = requests.get(fh_url, params=request_params, verify=False)   # Шлем запрос
    response = urlparse.parse_qs(response.text.encode('ASCII'))
    return response


def load_data_to_session(request, response, step):
    """Данные с сервера FH записываем в сессию"""
    contract_index = response['dognumber'].index(request.session['user_contract_number'])
    response_index = lambda key: response[key][contract_index]
    request.session['step'] = step  # Договор валидный, переход на следующий шаг
    request.session['src_id'] = response_index('src_id')
    request.session['fname'] = response_index('fname')
    request.session['lname'] = response_index('lname')
    request.session['bd'] = response_index('bd')
    request.session['dognumber'] = response_index('dognumber')
    request.session['src_club'] = response_index('src_club')
    request.session['sdate'] = response_index('sdate')
    request.session['edate'] = response_index('edate')
    request.session['type'] = response_index('type')


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


def can_restructure_contract(contract):
    """ Переоформить можно только «клубные» номера договоров (например, 13/12121201)
    с любым кол-вом цифр после префикса.
    Список префиксов по клубам в приложении «префиксы договоров».
    И интернет договоры с латинской буквой M и МВ перед префиксом (пример M13/12121201).
    Также переоформленные договоры (например, 13/12121201/1).
    Договоры с другими буквами перед префиксом (К/, Г/, A/, Z/  и т.д.)
    переводу через сайт не подлежат, необходимо выводить надпись «Данный договор нельзя перевести через интернет-сайт,
    обратитесь за информацией в отдел продаж 610-06-06»"""
    prefix = contract.split('/')[0]
    try:
        # Проверка на префиксы договоров. Префиксом может быть число и латинские M, MB
        int(prefix)
    except ValueError:
        # Значит префикс не число
        if (prefix.find('M') == 0) or (prefix.find('MB') == 0):
            return None
        return 'Данный договор нельзя перевести через интернет-сайт, обратитесь за информацией в отдел продаж 610-06-06'
    return None


def restructure_contract_1(response, user_contract_number, user, passport):
    print response

    status = response['?status'][0]
    if status == '1' or status == '2':
        contract_index = response['dognumber'].index(user_contract_number)
        response_index = lambda key: response[key][
            contract_index]   # Чтобы каждый раз не писать [contract_index]

        dognumber = response_index('dognumber')
        if ContractOrder.objects.filter(user=user, old_contract_number=dognumber, is_completed=False).count():
            return 'Ваш договор уже находится в обработке!'

        # Договор найден
        if len(dognumber.split('/')) > 1:
            type_lower = response_index('type').decode('cp1251').lower()
            if type_lower.find(u'визиты') != -1 or type_lower.find(u'визитов') != -1:
                return 'Данный договор нельзя перевести через интернет-сайт, обратитесь за информацией в отдел продаж 610-06-06'
            res = can_restructure_contract(dognumber)
            if res:
                return res

        passport_dog = response_index('passport').decode('cp1251').lower()
        if passport != passport_dog:
            return "Договор не найден или неверные данные!"

        elif response_index('activity').split('?')[0].replace('\r\n', '') != '1':
            # Если договор не активен
            return 'Договор ' + dognumber + ' не активен! Переоформлению не подлежит.'
        elif response_index('debt') != '0.00':
            # Если по договору имеется задолженность
            return 'Имеется задолженность по договору! Переоформлению не подлежит.'
        elif is_exclusive(response_index('sdate'), response_index('edate')):
            # Если по договору имеется задолженность
            return 'Данный договор нельзя перевести через интернет-сайт, обратитесь за информацией в отдел продаж 610-06-06'
    elif status == '3':
        return 'Ваш договор уже находится в обработке.'
    elif status == '-2' or status == '0':
        return 'Договор не найден или данные неверны!'
    return None


class Result:
    id, code, comment, comment_id, comment_str = None, None, None, None, None

    def __init__(self, xml):
        """ Разбор XML """
        for child in ET.fromstring(xml):
            setattr(self, child.tag, child.text)
        x = str.split(str(self.comment))
        if len(x) > 0:
            self.comment_id = int(x[0])
        if len(x) > 1:
            self.comment_str = x[1]


def convert(data):
    """ Перевод из кодировки ответа cp1251 в Unicode """
    if isinstance(data, str):
        return data.decode("cp1251")
    elif isinstance(data, collections.Mapping):
        return dict(map(convert, data.iteritems()))
    elif isinstance(data, collections.Iterable):
        return type(data)(map(convert, data))
    else:
        return data


def response_to_str(data):
    """ Ответ от FH в пригодный для печати вид """
    return repr(convert(data)).decode("unicode-escape")