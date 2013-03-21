# -*- coding: utf-8 -*-
from django.template import RequestContext
from contact.forms import ContactUsForm
from django.shortcuts import render_to_response, redirect
from django.contrib import messages
from django.core.mail import EmailMessage
from dbsettings.utils import get_settings_value
from django.template import Template, Context
from django.core.mail import send_mail
from django.conf import settings

# Create your views here.
def index(request):
    context = RequestContext(request)
    if request.method == 'POST':
        form = ContactUsForm(request.POST)
        if form.is_valid():
            subject = get_settings_value('CONTACTS_EMAIL_SUBJECT')
            to = get_settings_value('CONTACTS_EMAIL_ADDRESS')
            template = Template(get_settings_value('CONTACTS_EMAIL_TEMPLATE'))
            context = Context(form.cleaned_data)
            message = template.render(context)
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [to,], True)
            return redirect('contact.views.contact_form_success')
    else:
        form = ContactUsForm()
    context['form'] = form
    context['contacts_text'] = get_settings_value('CONTACTS_ADDRESS')
    return render_to_response('contact/contact_form.html', context)


def contact_form_success(request):
    context = RequestContext(request)
    return render_to_response('contact/contact_form_success.html', context)