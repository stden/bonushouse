# -*- coding: utf-8 -*-
from django import forms
from partners.models import Partner, PartnerAddress, PartnersPage, ClubCardNumbers
from administration.forms import BulkFeedbacksForm
from bonushouse.models import UserFeedbacks
from bonushouse.forms import CheckBoxSelectMultipleToggleAll
from offers.models import CouponCodes
from auctions.models import Auction
from model_changelog.signals import important_model_change
from dbsettings.utils import get_settings_value
from django.template import Template, Context
from django.core.mail import send_mail
from django.conf import settings
import re
from django.contrib.auth.models import User

class PartnerForm(forms.ModelForm):

    admin_user = forms.ModelMultipleChoiceField(label='Пользователь-администратор',queryset=User.objects.filter(is_staff=True).order_by('username'), widget=forms.CheckboxSelectMultiple())

    def save(self, commit=True):
        is_new = False
        if not self.instance.pk:
            is_new = True
        result = super(PartnerForm, self).save(commit)
        for photo in self.instance.get_photos_list():
            weight = self.data.get('weight-%s' % (photo.pk))
            if weight is not None and weight.isdigit() and weight != photo.weight:
                photo.weight = weight
                photo.save()
        important_model_change.send(sender=self.instance, created=is_new)
        return result

    class Meta:
        model = Partner
        widgets = {
            'title': forms.TextInput(attrs={'class':'text'}),
            'description': forms.Textarea(attrs={'class':'textarea', 'rows':10, 'cols':30}),
            'site': forms.TextInput(attrs={'class':'text'}),
        }

class PartnerAddressForm(forms.ModelForm):
    def save(self, commit=True):
        is_new = False
        if not self.instance.pk:
            is_new = True
        result = super(PartnerAddressForm, self).save(commit)
        important_model_change.send(sender=self.instance, created=is_new)
        return result
    class Meta:
        model = PartnerAddress
        widgets = {
            'title': forms.TextInput(attrs={'class':'text'}),
            'address': forms.TextInput(attrs={'class':'text'}),
            'schedule': forms.Textarea(attrs={'class':'textarea'}),
            'phone': forms.TextInput(attrs={'class':'text'}),
            'geocode_latitude': forms.HiddenInput(),
            'geocode_longitude': forms.HiddenInput(),
            'fitnesshouse_id': forms.TextInput(attrs={'class':'text'}),
        }

class BulkPartnerFeedbacksForm(BulkFeedbacksForm):
    def __init__(self, *args, **kwargs):
        partner_user = kwargs.get('partner_user')
        if not partner_user:
            raise Exception('Please, provide partner user')
        else:
            self.partner_user = partner_user
            del(kwargs['partner_user'])
            result = super(BulkPartnerFeedbacksForm, self).__init__(*args, **kwargs)
            self.fields['selected_items'] = forms.ModelMultipleChoiceField(queryset=UserFeedbacks.moderation_objects.filter(partner_user=self.partner_user), label='Отзывы')
        return result

class PartnersPageForm(forms.ModelForm):
    class Meta:
        model = PartnersPage
        widgets = {
            'title': forms.TextInput(attrs={'class':'text'}),
            'site_url': forms.TextInput(attrs={'class':'text'}),
            'description': forms.Textarea(attrs={'class':'textarea'}),
        }


class PinCodeForm(forms.Form):
    pin_code = forms.CharField(label='Введите пин-код', widget=forms.TextInput(attrs={'class':'text'}))

    def __init__(self, *args, **kwargs):
        partner_user = kwargs.get('partner_user')
        if partner_user is None:
            raise Exception('Partner user is not set')
        else:
            self.partner_user = partner_user
            del(kwargs['partner_user'])
        return super(PinCodeForm, self).__init__(*args, **kwargs)

    def clean_pin_code(self):
        pin_code = self.cleaned_data.get('pin_code')
        try:
            code = CouponCodes.objects.get(code=pin_code, is_used=False, partner__admin_user=self.partner_user)
            self.pin_code_order = code.get_order()
            self.pin_code_code = code
        except CouponCodes.DoesNotExist:
            raise forms.ValidationError('Пин-код не найден в базе')
        return pin_code


class ForPartnersPageForm(forms.Form):
    organisation = forms.CharField(label='Название организации', widget=forms.TextInput(attrs={'class':'text'}))
    subject = forms.CharField(label='Тема обращения', widget=forms.TextInput(attrs={'class':'text'}))
    text = forms.CharField(widget=forms.Textarea(attrs={'class':'textarea'}), label='Текст')
    contact = forms.CharField(widget=forms.Textarea(attrs={'class':'textarea'}), label='Контактные данные')
    def send(self):
        context = Context(self.cleaned_data)
        template = Template(get_settings_value('FOR_PARTNERS_FORM_TEMPLATE'))
        message = template.render(context)
        subject = get_settings_value('FOR_PARTNERS_FORM_SUBJECT')
        to = get_settings_value('FOR_PARTNERS_FORM_EMAIL')
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [to,], True)


class ClubCardNumbersForm(forms.ModelForm):
    def clean_first_chars(self):
        first_chars = self.cleaned_data.get('first_chars')
        nums_re = re.compile('^\d+$')
        if not nums_re.match(first_chars):
            raise forms.ValidationError('Допускаются только цифры')
        return first_chars

    class Meta:
        model = ClubCardNumbers
        widgets = {
            'title': forms.TextInput(attrs={'class':'text'}),
            'clubs': CheckBoxSelectMultipleToggleAll,
            'first_chars': forms.TextInput(attrs={'class':'text'}),
            'total_chars': forms.TextInput(attrs={'class':'text', 'style':'width:120px;'}),
            }