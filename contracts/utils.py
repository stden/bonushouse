# -*- coding: utf-8 -*-
import datetime
import md5
import urlparse

import requests
from django.template.base import Template
from django.conf import settings
from django.core.mail import send_mail

from dbsettings.utils import get_settings_value


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
    for key in request_params.keys():
        request_params[key] = request_params[key]
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