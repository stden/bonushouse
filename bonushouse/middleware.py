# -*- coding: utf-8 -*-
from django.core.urlresolvers import resolve
from django.shortcuts import redirect
from bonushouse.views import edit_profile
from bonushouse.views import logout_view
from django.contrib import messages
from bonushouse.forms import CallMeForm

class CheckUserDataMiddleware(object):
    def process_request(self, request):

        if request.user.is_authenticated():
            try:
                resolve_match = resolve(request.path)
            except:
                resolve_match = None
            if not request.user.is_staff and \
                (
                   not request.user.email or
                   not request.user.first_name or
                   not request.user.last_name or
                   request.user.get_profile().gender is None or
                   not request.user.get_profile().avatar or
                   not request.user.get_profile().birth_date or
                   not request.user.get_profile().phone

                ) and (
                    not resolve_match or
                    (resolve_match.func != edit_profile and resolve_match.func != logout_view)
                ):
                messages.info(request, 'Чтобы продолжить, укажите, пожалуйста, информацию о себе.')
                return redirect('bonushouse.views.edit_profile')

class CallMeMiddleware(object):
    def process_request(self, request):
        if request.method == 'POST' and request.POST.get('call_me'):
            call_me_form = CallMeForm(request.POST)
            if call_me_form.is_valid():
                call_me_form.save()
                return redirect('call_me_success')