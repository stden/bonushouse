# -*- coding: utf-8 -*-
from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from partners.models import Partner


class PersonalContractForm(forms.Form):
    contract_number = forms.CharField(max_length=20, label='№ договора',
                                      widget=forms.TextInput(attrs={'class': 'text'}),
                                      required=True)
    passport_series = forms.CharField(label='Серия паспорта', widget=forms.TextInput(attrs={'class': 'text'}),
                                      required=True)
    passport_number = forms.CharField(label='Номер паспорта', widget=forms.TextInput(attrs={'class': 'text'}),
                                      required=True)


class ContractProlongationForm(forms.Form):
    club = forms.ModelChoiceField(queryset=Partner.objects.get(title='Fitness House').partneraddress_set,
                                  widget=forms.Select(attrs={'class': 'text'}), label='Клуб', empty_label='')
    price = forms.CharField(max_length=100, label='Стоимость',
                            widget=forms.TextInput(attrs={'class': 'text', 'disabled': True}))

    def __init__(self, queryset, *args, **kwargs):
        super(ContractProlongationForm, self).__init__(*args, **kwargs)
        self.fields['new_order'] = forms.ModelChoiceField(queryset=queryset, label='Договоры', empty_label='')


class ContractPersonRestructingForm(forms.Form):
    email = forms.EmailField(label='Email пользователя Бонус-Хаус', widget=forms.TextInput(attrs={'class': 'text'}),
                             required=True)
    # last_name = forms.CharField(max_length=100, label='Фамилия', widget=forms.TextInput(attrs={'class':'text'}))
    # first_name = forms.CharField(max_length=100, label='Имя', widget=forms.TextInput(attrs={'class':'text'}))
    # birthdate = forms.CharField(max_length=100, label='Дата рождения', widget=forms.DateInput(attrs={'class':'text mask_date', 'placeholder':'дд.мм.гггг'}))
    # second_name = forms.CharField(max_length=100, label='Отчество', required=False, widget=forms.TextInput(attrs={'class':'text'}))
    passport_series = forms.CharField(max_length=4, label='Серия паспорта',
                                      widget=forms.TextInput(attrs={'class': 'text'}), required=True)
    passport_number = forms.CharField(max_length=6, label='Номер паспорта',
                                      widget=forms.TextInput(attrs={'class': 'text'}), required=True)

    def __init__(self, user, *args, **kwargs):
        super(ContractPersonRestructingForm, self).__init__(*args, **kwargs)
        self.current_user = user

    def clean(self):
        cleaned_data = super(ContractPersonRestructingForm, self).clean()
        email = self.cleaned_data.get('email')
        try:
            user = User.objects.get(email=email)
        except ObjectDoesNotExist:
            raise forms.ValidationError('Пользователь с таким email не зарегистрирован на сайте Бонус-Хаус!')
        if user == self.current_user:
            raise forms.ValidationError('Нельзя указать свой email!')
        return cleaned_data


class ContractClubRestructingForm(forms.Form):
    pass


class GetContractNumberForm(forms.Form):
    passport_series = forms.CharField(label='Серия паспорта', widget=forms.TextInput(attrs={'class': 'text'}),
                                      required=False)
    passport_number = forms.CharField(label='Номер паспорта', widget=forms.TextInput(attrs={'class': 'text'}),
                                      required=False)
    clubcard_number = forms.CharField(label='Номер клубной карты', widget=forms.TextInput(attrs={'class': 'text'}),
                                      required=False)
    search_type = forms.ChoiceField(widget=forms.RadioSelect(attrs={'class': 'text'}), choices=((1, ''), (2, '')))

    def clean(self):
        cleaned_data = super(GetContractNumberForm, self).clean()
        if not ((cleaned_data.get('clubcard_number')) or (
                cleaned_data.get('passport_series') and cleaned_data.get('passport_number'))):
            raise forms.ValidationError(u'Пожалуйста, заполните все поля')
        return cleaned_data