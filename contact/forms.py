# -*- coding: utf-8 -*-
from django import forms

class ContactUsForm(forms.Form):
    name = forms.CharField(label='Ваше имя', widget=forms.TextInput(attrs={'class':'text'}))
    email = forms.EmailField(label='Ваш E-mail', widget=forms.TextInput(attrs={'class':'text'}))
    #phone = forms.CharField(label='Ваш телефон', required=False)
    message = forms.CharField(label='Ваш вопрос', widget=forms.Textarea(attrs={'class':'textarea','cols':30, 'rows':5}))