# -*- coding: utf-8 -*-
from django import forms

class PersonalContractForm(forms.Form):
    contract_number = forms.CharField(max_length=20, label='Номер договора', widget=forms.TextInput(attrs={'class':'text'}))
    passport_series = forms.CharField(max_length=4, label='Серия паспорта', widget=forms.TextInput(attrs={'class':'text'}))
    passport_number = forms.CharField(max_length=6, label='Номер паспорта', widget=forms.TextInput(attrs={'class':'text'}))


class ContractProlongationForm(forms.Form):
    pass


class ContractPersonRestructingForm(forms.Form):
    last_name = forms.CharField(max_length=100, label='Фамилия', widget=forms.TextInput(attrs={'class':'text'}))
    first_name = forms.CharField(max_length=100, label='Имя', widget=forms.TextInput(attrs={'class':'text'}))
    second_name = forms.CharField(max_length=100, label='Отчество', widget=forms.TextInput(attrs={'class':'text'}))
    birthdate = forms.CharField(max_length=100, label='Дата рождения', widget=forms.DateInput(attrs={'class':'text mask_date', 'placeholder':'дд.мм.гггг'}))
    passport_series = forms.CharField(max_length=4, label='Серия паспорта', widget=forms.TextInput(attrs={'class':'text'}))
    passport_number = forms.CharField(max_length=6, label='Номер паспорта', widget=forms.TextInput(attrs={'class':'text'}))

    # def clean_

class ContractClubRestructingForm(forms.Form):
    pass