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