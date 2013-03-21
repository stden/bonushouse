# -*- coding: utf-8 -*-
from django.utils.safestring import mark_safe
from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db.models import Q
from bonushouse.models import UserFeedbacks, GENDER_CHOICES, BusinessIdea
from dbsettings.utils import get_settings_value
from django.core.mail import send_mail
from django.template import Template, Context
from django.conf import settings
from django.contrib.sites.models import Site
from common.models import Categories, MetroStations
from haystack.forms import SearchForm
from offers.models import Offers
import re
from administration.models import CallMeSubjects
from bonushouse.utils import get_object_or_none
from partners.models import Partner
from threadlocals_user.utils import get_current_user

class ProfileForm(forms.Form):
    first_name = forms.CharField(label='Имя', widget=forms.TextInput(attrs={'class':'text'}))
    last_name = forms.CharField(label='Фамилия', widget=forms.TextInput(attrs={'class':'text'}))
    email = forms.EmailField(label='E-mail', widget=forms.TextInput(attrs={'class':'text'}))
    gender = forms.IntegerField(widget=forms.Select(choices=GENDER_CHOICES), label='Пол')
    birth_date = forms.DateField(label='Дата рождения', widget=forms.DateInput(attrs={'class':'mask_date text'}))
    phone = forms.CharField(max_length=32, label='Контактный телефон', widget=forms.TextInput(attrs={'class':'mask_phone text'}))
    avatar = forms.ImageField(label='Аватар')
    def  clean_phone(self):
        phone = self.cleaned_data.get('phone')
        phone_re = re.compile('8\(\d{3}\)\d{7}')
        if not phone_re.match(phone):
            raise forms.ValidationError('Неправильно указан номер телефона')
        return phone
    def save(self, user):
        profile = user.get_profile()
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        profile.gender = self.cleaned_data['gender']
        profile.birth_date = self.cleaned_data['birth_date']
        profile.avatar = self.cleaned_data['avatar']
        profile.phone = self.cleaned_data['phone']
        profile.save()
        user.save()

class DepositForm(forms.Form):
    amount = forms.IntegerField(label='Сумма пополнения', initial=1000, widget=forms.TextInput(attrs={'class':'text'}), min_value=1)

class LoginForm(forms.Form):
    email = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'E-mail','class':'text'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder':'Пароль','class':'text'}))
    def clean_email(self):
        email = self.cleaned_data.get('email')
        password = self.data.get('password')
        user = authenticate(username=email, password=password)
        if user is not None:
            if user.is_active:
                self.user = user
                return email
            else:
                raise forms.ValidationError("Ваш акаунт отключен")
        else:
            raise forms.ValidationError("Вы ввели неправильный логин или пароль")

class RegisterForm(forms.Form):
    email = forms.EmailField(max_length=75, widget=forms.TextInput(attrs={'placeholder':'E-mail','class':'text'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder':'Пароль','class':'text'}))
    # Временно не нужно:
    # agreement = forms.BooleanField(label='Я согласен с правилами оферты', required=True)

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(Q(email=email)|Q(username=email)).count():
            raise forms.ValidationError('Пользователь с таким E-mail уже существует')
        return email
    def save(self):
        user = User.objects.create_user(self.cleaned_data['email'], email=self.cleaned_data['email'], password=self.cleaned_data['password'])
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        user.save()
        return user

class FeedbacksForm(forms.ModelForm):
    rating = forms.IntegerField(min_value=1, label='Оценка')
    class Meta:
        model = UserFeedbacks
        widgets = {
            'text': forms.Textarea(attrs={'placeholder':'Ваш отзыв...','rows':5,'cols':30,'class':'textarea'})
        }

class BusinessIdeaForm(forms.ModelForm):
    class Meta:
        model = BusinessIdea
        widgets = {
            'title': forms.TextInput(attrs={'class':'text'}),
            'text': forms.Textarea(attrs={'class':'textarea','rows':10,'cols':30}),
        }


def get_call_me_subjects():
    result = []
    subjects = get_settings_value('CALL_ME_AVAILABLE_SUBJECTS')
    if subjects is not None:
        for subject in subjects:
            result.append((subject, subject))
    return result

class CallMeForm(forms.Form):
    name = forms.CharField(max_length=255, label='Как вас зовут:', widget=forms.TextInput(attrs={'class':'text'}))
    phone = forms.CharField(widget=forms.TextInput(attrs={'class':'text mask_phone'}), label='Ваш номер телефона:')
    suitable_time = forms.CharField(label='Удобное вам время для звонка:', required=False, widget=forms.TextInput(attrs={'class':'text'}))
    subject = forms.ModelChoiceField(label='Тема', queryset=CallMeSubjects.objects.all(), initial=get_object_or_none(CallMeSubjects, title='Общие вопросы'))
    def save(self):
        phone = self.cleaned_data.get('phone')
        form_subject = self.cleaned_data.get('subject')
        name = self.cleaned_data.get('name')
        suitable_time = self.cleaned_data.get('suitable_time')
        to = form_subject.email
        #Рендерим тему письма
        template = Template(get_settings_value('CALL_ME_EMAIL_SUBJECT'))
        context = Context({'subject': form_subject})
        subject = template.render(context).strip()
        #Рендерим сообщение
        template = Template(get_settings_value('CALL_ME_EMAIL_TEMPLATE'))
        context = Context({'phone':phone, 'subject':form_subject.title,'name':name,'suitable_time':suitable_time})
        message = template.render(context)
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [to,], True)


class ReferFriendForm(forms.Form):
    name = forms.CharField(label='Как зовут вашего друга', widget=forms.TextInput(attrs={'class':'text'}))
    email = forms.EmailField(label='E-mail вашего друга', widget=forms.TextInput(attrs={'class':'text'}))
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            users = User.objects.filter(email=email)
            if users.count():
                raise forms.ValidationError('Этот пользователь уже зарегистрирован у нас.')
        return email
    def save(self, referer):
        to = self.cleaned_data['email']
        name = self.cleaned_data['name']
        subject = get_settings_value('REFER_FRIEND_EMAIL_SUBJECT')
        template = Template(get_settings_value('REFER_FRIEND_EMAIL_TEMPLATE'))
        site = Site.objects.get_current()
        link = 'http://' + site.domain + '/?refered_by='+str(referer.pk)
        context = Context({'name': name, 'link': link, 'sender':get_current_user().get_profile().get_name()})
        message = template.render(context)
        send_mail(subject, message,  settings.DEFAULT_FROM_EMAIL, [to,], True)

class CheckBoxSelectMultipleToggleAll(forms.CheckboxSelectMultiple):
    def render(self, name, value, attrs=None, choices=()):
        attrs['class'] = 'disable-fancy'
        result = super(CheckBoxSelectMultipleToggleAll, self).render(name, value, attrs, choices)
        result = u"""<div class="all_toggle_wrapper">
                    <ul class="all_toggle">
                        <li><a href="#" onclick="$('input:checkbox', $(this).parents('div:first')).attr('checked','checked');return false;">Выбрать все</a></li>
                        <li><a href="#" onclick="$('input:checkbox', $(this).parents('div:first')).removeAttr('checked');return false;">Убрать все</a></li>
                    </ul>
                    %s
                    </div>""" % (unicode(result),)
        return mark_safe(result)


DISCOUNT_CHOICES = (
    (1, 'до 50%'),
    (2, '50%-60%'),
    (3, '60%-70%'),
    (4, '70%-90%'),
    (5, 'свыше 90%'),
)

class ExtendedSearchForm(SearchForm):
    q = forms.CharField(widget=forms.TextInput(attrs={'class': 'text'}), label='Ключевые слова:')
    price_min = forms.IntegerField(required=False, label='Цена купона от', widget=forms.HiddenInput)
    price_max = forms.IntegerField(required=False, label='Цена купона до', widget=forms.HiddenInput)
    discount = forms.MultipleChoiceField(widget=CheckBoxSelectMultipleToggleAll, choices=DISCOUNT_CHOICES, label='Скидка:', initial=(1,2,3,4,5,))
    include_categories = forms.ModelMultipleChoiceField(widget=CheckBoxSelectMultipleToggleAll, queryset=Categories.objects.all(), initial=Categories.objects.all(), label='Включая категории:')
    exclude_categories = forms.ModelMultipleChoiceField(widget=CheckBoxSelectMultipleToggleAll, queryset=Categories.objects.all(), label='Исключая категории:', required=False)
    metro = forms.ModelMultipleChoiceField(widget=CheckBoxSelectMultipleToggleAll, queryset=MetroStations.objects.all(), initial=MetroStations.objects.all(), label='Станции метро:')
    partners = forms.ModelMultipleChoiceField(widget=CheckBoxSelectMultipleToggleAll, queryset=Partner.objects.all(), initial=Partner.objects.all(), label='Сети заведений')
    def search(self):
        sqs = super(ExtendedSearchForm, self).search()
        sqs = sqs.models(*(Offers,))
        #Категории
        sqs = sqs.filter(categories__in=[category.pk for category in self.cleaned_data.get('include_categories')])
        sqs = sqs.exclude(categories__in=[category.pk for category in self.cleaned_data.get('exclude_categories')])
        #Партнеры
        sqs = sqs.filter(partner__in=[partner.pk for partner in self.cleaned_data.get('partners')])
        #Метро
        sqs = sqs.filter(metro__in=[station.pk for station in self.cleaned_data.get('metro')])
        #Цена
        price_min = self.cleaned_data.get('price_min')
        price_max = self.cleaned_data.get('price_max')
        if price_min:
            sqs = sqs.filter(coupon_price_money__gte=price_min)
        if price_max:
            sqs = sqs.filter(coupon_price_money__lte=price_max)
        #Скидка
        discount = self.cleaned_data.get('discount')
        sqs = sqs.filter(discount__in=[int(item) for item in discount])
        return sqs


class ShareLinkForm(forms.Form):
    name = forms.CharField(label='Как зовут вашего друга:', widget=forms.TextInput(attrs={'class':'text'}))
    email = forms.EmailField(label='E-mail вашего друга:', widget=forms.TextInput(attrs={'class':'text'}))
    url = forms.CharField(label='Ссылка')