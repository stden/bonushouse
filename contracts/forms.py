# -*- coding: utf-8 -*-
from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist


class PersonalContractForm(forms.Form):
    contract_number = forms.CharField(max_length=20, label='Номер договора', widget=forms.TextInput(attrs={'class':'text'}))
    passport_series = forms.CharField(max_length=4, label='Серия паспорта', widget=forms.TextInput(attrs={'class':'text'}))
    passport_number = forms.CharField(max_length=6, label='Номер паспорта', widget=forms.TextInput(attrs={'class':'text'}))


class ContractProlongationForm(forms.Form):
    pass


class ContractPersonRestructingForm(forms.Form):
    email = forms.EmailField(label='Email пользователя Бонус-Хаус', widget=forms.TextInput(attrs={'class':'text'}))
    # last_name = forms.CharField(max_length=100, label='Фамилия', widget=forms.TextInput(attrs={'class':'text'}))
    # first_name = forms.CharField(max_length=100, label='Имя', widget=forms.TextInput(attrs={'class':'text'}))
    # birthdate = forms.CharField(max_length=100, label='Дата рождения', widget=forms.DateInput(attrs={'class':'text mask_date', 'placeholder':'дд.мм.гггг'}))
    second_name = forms.CharField(max_length=100, label='Отчество', widget=forms.TextInput(attrs={'class':'text'}))
    passport_series = forms.CharField(max_length=4, label='Серия паспорта', widget=forms.TextInput(attrs={'class':'text'}))
    passport_number = forms.CharField(max_length=6, label='Номер паспорта', widget=forms.TextInput(attrs={'class':'text'}))

    def __init__(self, user, *args, **kwargs):
        super(ContractPersonRestructingForm, self).__init__(*args, **kwargs)
        self.current_user = user

    def clean(self):
        cleaned_data = super(ContractPersonRestructingForm, self).clean()
        email = self.cleaned_data['email']
        try:
            user = User.objects.get(email=email)
        except ObjectDoesNotExist:
            raise forms.ValidationError('Пользователь с таким email не зарегистрирован!')
        if user == self.current_user:
            raise forms.ValidationError('Нельзя указать свой email!')
        return cleaned_data


class ContractClubRestructingForm(forms.Form):
    pass