# -*- coding: utf-8 -*-
from partners.forms import ForPartnersPageForm
from django.contrib import messages
from django.shortcuts import redirect

class ForPartnersPageFormMiddleware(object):
    def process_request(self, request):
        if request.method == 'POST':
            form_id = request.POST.get('form_id')
            if form_id == 'for_partners_form':
                form = ForPartnersPageForm(request.POST)
                if form.is_valid():
                    form.send()
                    messages.info(request, 'Спасибо! Мы рассмотрим ваше обращение в ближайшее время')
                    return redirect('home')