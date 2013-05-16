# -*- coding: utf-8 -*-
import datetime

from django.template.base import Template
from django.conf import settings
from django.core.urlresolvers import reverse_lazy
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
