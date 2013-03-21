# -*- coding: utf-8 -*-
from django import forms
from offers.models import Offers
from common.models import Categories
from partners.models import Partner, PartnersPage, ClubCardNumbers
from flatpages.models import FlatPage
from advertising.models import Banner
from auctions.models import Auction
from bonushouse.models import UserFeedbacks
from django.contrib.auth.models import User
from django.contrib.formtools.preview import FormPreview
from django.shortcuts import redirect
from administration.menu import load_menu_context
from administration.models import CallMeSubjects
from news.models import News

class BulkPartnersPageForm(forms.Form):
    selected_items = forms.ModelMultipleChoiceField(queryset=PartnersPage.objects.all(), label='Партнеры')
    action = forms.CharField(label='Действие')


class BulkClubCardNumbersForm(forms.Form):
    selected_items = forms.ModelMultipleChoiceField(queryset=ClubCardNumbers.objects.all(), label='Номера')
    action = forms.CharField(label='Действие')


class BulkOffersForm(forms.Form):
    selected_items = forms.ModelMultipleChoiceField(queryset=Offers.all_objects.all(), label='Акции')
    action = forms.CharField(label='Действие')

class BulkCategoriesForm(forms.Form):
    selected_items = forms.ModelMultipleChoiceField(queryset=Categories.all_objects.all(), label='Категории')
    action = forms.CharField(label='Действие')

class BulkPartnersForm(forms.Form):
    selected_items = forms.ModelMultipleChoiceField(queryset=Partner.objects.all(), label='Партнеры')
    action = forms.CharField(label='Действие')

class BulkPagesForm(forms.Form):
    selected_items = forms.ModelMultipleChoiceField(queryset=FlatPage.objects.all(), label='Страницы')
    action = forms.CharField(label='Действие')


class BulkNewsForm(forms.Form):
    selected_items = forms.ModelMultipleChoiceField(queryset=News.objects.all(), label='Страницы')
    action = forms.CharField(label='Действие')

class BulkBannersForm(forms.Form):
    selected_items = forms.ModelMultipleChoiceField(queryset=Banner.admin_objects.all(), label='Баннеры')
    action = forms.CharField(label='Действие')

class BulkFeedbacksForm(forms.Form):
    selected_items = forms.ModelMultipleChoiceField(queryset=UserFeedbacks.moderation_objects.all(), label='Отзывы')
    action = forms.CharField(label='Действие')

class BulkUsersForm(forms.Form):
    selected_items = forms.ModelMultipleChoiceField(queryset=User.objects.all(), label='Пользователи')
    action = forms.CharField(label='Действие')

class BulkAuctionsForm(forms.Form):
    selected_items = forms.ModelMultipleChoiceField(queryset=Auction.all_objects.all(), label='Аукционы')
    action = forms.CharField(label='Действие')

class DateRangeForm(forms.Form):
    date_from = forms.DateField(input_formats=('%d.%m.%Y', ),label='С', required=False, widget=forms.DateInput(format='%d.%m.%Y', attrs={'class':'text datepicker'}))
    date_to = forms.DateField(input_formats=('%d.%m.%Y', ),label='По', required=False, widget=forms.DateInput(format='%d.%m.%Y', attrs={'class':'text datepicker'}))

class IdeaRewardForm(forms.Form):
    reward = forms.IntegerField(min_value=1, label='Вознаграждение автору', widget=forms.TextInput(attrs={'class':'text','style':'width:200px;'}))


USER_TYPE_CHOICES = (
    ('basic','Простой пользователь'),
    ('operator', 'Оператор'),
    ('admin', 'Администратор'),
)


class UserForm(forms.Form):
    username = forms.CharField(label='Имя пользователя', widget=forms.TextInput(attrs={'class':'text'}))
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput(attrs={'class':'text'}))
    password_confirm = forms.CharField(label='Подтверждение пароля', widget=forms.PasswordInput(attrs={'class':'text'}))
    email = forms.EmailField(label='E-mail', widget=forms.TextInput(attrs={'class':'text'}))
    is_active = forms.BooleanField(label='Активен', initial=True, required=False)
    type = forms.ChoiceField(label='Тип', choices=USER_TYPE_CHOICES)
    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance')
        if instance:
            self.instance = instance
            del(kwargs['instance'])
        else:
            self.instance = None
        super(UserForm, self).__init__(*args, **kwargs)
        if self.instance:
            self.fields['password'].required = False
            self.fields['password_confirm'].required = False
    def clean_username(self):
        username = self.cleaned_data['username']
        if not self.instance or username != self.instance.username:
            try:
                user = User.objects.get(username=username)
                raise forms.ValidationError('Пользователь с таким логином уже существует')
            except User.DoesNotExist:
                pass
        return username
    def clean_email(self):
        email = self.cleaned_data['email']
        if not self.instance or email != self.instance.email:
            users = User.objects.filter(email=email)
            if users.count():
                raise forms.ValidationError('Пользователь с таким e-mail уже существует')
        return email
    def clean(self):
        cleaned_data = super(UserForm, self).clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        if password != password_confirm:
            raise forms.ValidationError('Пароли не совпадают')
        return cleaned_data
    def save(self):
        #Редактирование
        if self.instance:
            self.instance.username = self.cleaned_data['username']
            self.instance.email = self.cleaned_data['email']
            if self.cleaned_data['is_active']:
                self.instance.is_active = True
            else:
                self.instance.is_active = False
            if self.cleaned_data['type'] == 'operator':
                self.instance.is_superuser = False
                self.instance.is_staff = True
            elif self.cleaned_data['type'] == 'admin':
                self.instance.is_superuser = True
                self.instance.is_staff = True
            else:
                self.instance.is_superuser = False
                self.instance.is_staff = False
            if len(self.cleaned_data['password']):
                self.instance.set_password(self.cleaned_data['password'])
            self.instance.save()
        #Новый пользователь
        else:
            user = User.objects.create_user(self.cleaned_data['username'], self.cleaned_data['email'], self.cleaned_data['password'])
            if self.cleaned_data['is_active']:
                user.is_active = True
            else:
                user.is_active = False
            if self.cleaned_data['type'] == 'operator':
                user.is_superuser = False
                user.is_staff = True
            elif self.cleaned_data['type'] == 'admin':
                user.is_superuser = True
                user.is_staff = True
            else:
                user.is_superuser = False
                user.is_staff = False
            user.save()

class OffersFormPreview(FormPreview):
    preview_template = 'administration/offers/preview.html'
    form_template = 'administration/offers/preview_error.html'
    def done(self, request, cleaned_data):
        return redirect('administration_index')
    def get_context(self, request, form):
        context = super(OffersFormPreview, self).get_context(request, form)
        context = load_menu_context(context)
        return context

class PagesFormPreview(FormPreview):
    preview_template = 'administration/pages/preview.html'
    form_template = 'administration/pages/preview_error.html'
    def done(self, request, cleaned_data):
        return redirect('administration_index')
    def get_context(self, request, form):
        context = super(PagesFormPreview, self).get_context(request, form)
        context = load_menu_context(context)
        return context

class AuctionFormPreview(FormPreview):
    preview_template = 'administration/auctions/preview.html'
    form_template = 'administration/auctions/preview_error.html'
    def done(self, request, cleaned_data):
        return redirect('administration_index')
    def get_context(self, request, form):
        context = super(AuctionFormPreview, self).get_context(request, form)
        context = load_menu_context(context)
        return context

class CallMeSubjectForm(forms.ModelForm):
    class Meta:
        model = CallMeSubjects
        widgets = {
            'title': forms.TextInput(attrs={'class':'text'}),
            'email': forms.TextInput(attrs={'class':'text'}),
        }