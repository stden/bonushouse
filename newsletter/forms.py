# -*- coding: utf-8 -*-
from django import forms
from newsletter.models import NewsletterCampaign, NewsletterEmail, NewsletterSms
from common.forms import CategoriesCheckboxSelectMultiple

class NewsletterCampaignForm(forms.ModelForm):
    class Meta:
        model = NewsletterCampaign
        widgets = {
            'title': forms.TextInput(attrs={'class':'text'}),
            'min_bonuses_ballance': forms.TextInput(attrs={'class':'text'}),
            'min_age': forms.TextInput(attrs={'class':'text','style':'width:50px;'}),
            'max_age': forms.TextInput(attrs={'class':'text','style':'width:50px;'}),
        }

class NewsletterEmailForm(forms.ModelForm):
    class Meta:
        model = NewsletterEmail
        widgets = {
            'campaigns': CategoriesCheckboxSelectMultiple(),
            'subject': forms.TextInput(attrs={'class':'text'}),
            'send_date': forms.DateTimeInput(attrs={'class':'datetimepicker'}, format='%d.%m.%Y %H:%M'),
        }

class NewsletterSmsForm(forms.ModelForm):
    def clean_text(self):
        text = self.cleaned_data.get('text')
        if len(text) > 140:
            raise forms.ValidationError('Длина сообщения не может превышать 140 символов')
        return text
    class Meta:
        model = NewsletterSms
        widgets = {
            'campaigns': CategoriesCheckboxSelectMultiple(),
            'send_date': forms.DateTimeInput(attrs={'class':'datetimepicker'}, format='%d.%m.%Y %H:%M'),
        }