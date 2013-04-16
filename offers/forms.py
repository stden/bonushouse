# -*- coding: utf-8 -*-
from django import forms
from offers.models import Offers, AbonementsAdditionalInfo, AdditionalServicesInfo, DELIVERY_CHOICES, GiftOrder
from common.forms import CategoriesCheckboxSelectMultiple
from django.forms.util import flatatt, ErrorDict, ErrorList
from common.models import Categories
from django.utils.timezone import now
from bonushouse.utils import total_seconds
from partners.models import PartnerAddress, Partner, ClubCardNumbers
import re
from django.db.models import Q
from django.conf import settings
from model_changelog.signals import important_model_change
from django.utils.html import mark_safe
from dbsettings.utils import get_settings_value
from django.utils.timezone import now
import datetime


class ClubCardOrAgreementField(forms.CharField):
    card_template = None

    def validate(self, value):
        super(ClubCardOrAgreementField, self).validate(value)
        card_number = value
        agreement_re = settings.FITNESSHOUSE_AGREEMENT_RE
        if len(card_number) < 5:
            raise forms.ValidationError('Проверьте правильность ввода номера')
        agreement_match = agreement_re.match(card_number)
        if agreement_match:
            #Ввод совпал с шаблоном договора, получаем id клуба и ищем его среди клубов для данной акции
            club_id = agreement_match.groups()[0]
        else:
            #С шаблоном договора ввод не совпадает. Проверяем, может это номер карты.
            card_template = None
            card_templates = ClubCardNumbers.objects.filter(Q(total_chars=len(card_number), total_chars_sign='=') | Q(total_chars_sign='>=', total_chars__lte=len(card_number)))
            for template in card_templates:
                if template.first_chars == card_number[0:len(template.first_chars)]:
                    card_template = template
                    break
            if card_template is None:
                raise forms.ValidationError('Номер карты не опознан, проверьте правильность ввода.')


def get_clubs_by_card_number(card_number):
    """Принимает номер договора или клубной карты и возвращает список клубов или None, если не найден шаблон"""
    agreement_re = settings.FITNESSHOUSE_AGREEMENT_RE
    agreement_match = agreement_re.match(card_number)
    if agreement_match:
        #Номер совпал с шаблоном договора, получаем id клуба и ищем cоответствуйщий клуб
        club_id = agreement_match.groups()[0]
        club = PartnerAddress.objects.filter(fitnesshouse_id=club_id)
        if club.count():
            return club
        else:
            return None
    else:
        #С шаблоном договора номер не совпадает. Проверяем, может это номер карты.
        card_template = None
        card_templates = ClubCardNumbers.objects.filter(Q(total_chars=len(card_number), total_chars_sign='=') | Q(total_chars_sign='>=', total_chars__lte=len(card_number)))
        for template in card_templates:
            if template.first_chars == card_number[0:len(template.first_chars)]:
                card_template = template
                break
        if card_template is None:
            return None
        else:
            if card_template.clubs.count():
                return card_template.clubs.all()
            else:
                return None


class OffersForm(forms.ModelForm):

    categories = forms.ModelMultipleChoiceField(queryset=Categories.objects.all(), label='Категории', widget=CategoriesCheckboxSelectMultiple)
    initial_price = forms.CharField(required=False, label='Цена без скидки')

    def __init__(self, *args, **kwargs):
        partner_user = kwargs.get('partner_user')
        if partner_user:
            self.partner_user = partner_user
            del(kwargs['partner_user'])
        result = super(OffersForm, self).__init__(*args, **kwargs)
        if partner_user:
            del(self.fields['is_published'])
            del(self.fields['type'])
            self.fields['partner'] = forms.ModelChoiceField(queryset=Partner.objects.filter(admin_user=partner_user), label='Партнер')
            self.fields['addresses'] = forms.ModelMultipleChoiceField(widget=forms.CheckboxSelectMultiple(),queryset=PartnerAddress.objects.filter(partner__admin_user=partner_user),label='Заведения')
        if self.instance.pk and self.fields.has_key('type'):
            self.fields['type'].widget = forms.HiddenInput()
        return result

    def save(self, commit=True):
        is_new = False
        if not self.instance.pk:
            is_new = True
        result = super(OffersForm, self).save(commit)
        for photo in self.instance.get_photos_list():
            weight = self.data.get('weight-%s' % (photo.pk))
            if weight is not None and weight.isdigit() and weight != photo.weight:
                photo.weight = weight
                photo.save()
        important_model_change.send(sender=self.instance, created=is_new)
        return result

    def clean_abonements_term(self):
        type = self.cleaned_data.get('type')
        term  = self.cleaned_data.get('abonements_term')
        if type == 2 and not term:
            raise forms.ValidationError('Не задан срок действия договора')
        return term

    def clean_additional_services_term(self):
        type = self.cleaned_data.get('type')
        term  = self.cleaned_data.get('additional_services_term')
        if type == 3 and not term:
            raise forms.ValidationError('Не задан срок действия абонемента')
        return term

    def clean_fh_inner_title(self):
        type = self.cleaned_data.get('type')
        value = self.cleaned_data.get('fh_inner_title')
        if (type == 2 or type == 3) and not value:
            raise forms.ValidationError('Вы не указали внутренний заголовок для базы FH')
        return value

    def clean_initial_price(self):
        data = self.cleaned_data['initial_price']
        if not self.cleaned_data['initial_price']:
            self.cleaned_data['initial_price'] = None
            data = None
        return data

    class Meta:
        model = Offers
        widgets = {
            'title': forms.TextInput(attrs={'class': 'text'}),
            'addresses': forms.CheckboxSelectMultiple(),
            'short_description': forms.Textarea(attrs={'class':'textarea', 'rows':10, 'cols':30}),
            'description': forms.Textarea(attrs={'class':'textarea', 'rows':10, 'cols':30}),
            'terms': forms.Textarea(attrs={'class':'textarea', 'rows':10, 'cols':30}),
            'quantity': forms.TextInput(attrs={'class': 'text'}),
            'coupon_price_money': forms.TextInput(attrs={'class': 'text'}),
            'coupon_price_bonuses': forms.TextInput(attrs={'class': 'text'}),
            'money_bonuses_count': forms.TextInput(attrs={'class': 'text'}),
            'start_date': forms.DateTimeInput(attrs={'class':'datetimepicker text'}, format='%d.%m.%Y %H:%M'),
            'end_date': forms.DateTimeInput(attrs={'class':'datetimepicker text'}, format='%d.%m.%Y %H:%M'),
            'additional_services_term': forms.TextInput(attrs={'class':'text float_left', 'style':'width:60px;margin-right:20px;'}),
            'abonements_term': forms.TextInput(attrs={'class':'text float_left', 'style':'width:60px;margin-right:20px;'}),
            'fh_inner_title': forms.TextInput(attrs={'class': 'text'}),

        }

PAYMENT_TYPE_CHOICES = (
    (1, 'Депозит'),
    (2, 'Бонусы'),
    (3, 'Другие'),
)

class BuyOfferForm(forms.Form):
    quantity = forms.IntegerField(min_value=1, label='Количество', initial=1)
    payment_type = forms.ChoiceField(choices=PAYMENT_TYPE_CHOICES, widget=forms.HiddenInput(), label='Способ оплаты')

    def __init__(self, *args, **kwargs):
        user = kwargs.get('user')
        offer = kwargs.get('offer')
        if user is None:
            raise Exception('User is not set')
        if offer is None:
            raise Exception('Offer is not set')
        is_gift = kwargs.get('is_gift')
        if is_gift:
            self.is_gift = True
            del(kwargs['is_gift'])
        else:
            self.is_gift = False
        del(kwargs['user'])
        del(kwargs['offer'])
        self.offer = offer
        self.user = user
        super(BuyOfferForm, self).__init__(*args, **kwargs)
        if self.offer.is_abonement() or self.offer.is_additional_service() or self.is_gift:
            del(self.fields['quantity'])

    def clean_quantity(self):
        quantity = int(self.cleaned_data.get('quantity'))
        if self.offer.coupons_left() < quantity:
            raise forms.ValidationError("Вы можете купить не более %s купонов" % (self.offer.coupons_left(),))
        return quantity

    def clean_payment_type(self):
        payment_type = int(self.cleaned_data['payment_type'])
        if self.offer.is_abonement() or self.offer.is_additional_service() or self.is_gift:
            quantity = 1
        else:
            quantity = self.cleaned_data['quantity']
        if self.offer.can_buy_for_money():
            price_money = self.offer.coupon_price_money * quantity
        else:
            price_money = None
        if self.offer.can_buy_for_bonuses():
            price_bonuses = self.offer.coupon_price_bonuses * quantity
        else:
            price_bonuses = None
        user = self.user
        if payment_type == 1:
            if not self.offer.can_buy_for_money():
                raise forms.ValidationError('Данный купон можно купить только за бонусы')
            if user.get_profile().get_money_ballance() < price_money:
                raise forms.ValidationError('На вашем счету в Бонус Хаус недостаточно средств. Пополните счет, либо выберите другой способ')
        elif payment_type == 2:
            if not self.offer.can_buy_for_bonuses():
                raise forms.ValidationError('Данный купон нельзя купить за бонусы')
            if user.get_profile().get_bonuses_ballance() < price_bonuses:
                raise forms.ValidationError('У вас недостаточно бонусов на счету')
        elif payment_type == 3:
            if price_money is None:
                raise forms.ValidationError('Данный купон можно купить только за бонусы')
        else:
            raise forms.ValidationError('Выбран неправильный способ оплаты')
        return payment_type


class AbonementsAdditionalInfoForm(forms.ModelForm):
    agree_club_rules = forms.BooleanField(label=mark_safe(u'Я прочитал и согласен с <a href="%s" target="_blank">правилами клубов</a>' % (settings.MEDIA_URL+'misc/'+get_settings_value('CLUB_RULES_FILE'),)))

    def __init__(self, *args, **kwargs):
        offer = kwargs.get('offer')
        if offer:
            self.offer = offer
            del(kwargs['offer'])
        else:
            raise Exception('Offer is not set')
        result = super(AbonementsAdditionalInfoForm, self).__init__(*args, **kwargs)
        self.fields['address'] = forms.ModelChoiceField(queryset=self.offer.addresses, label='Выберите клуб')
        if offer.abonements_is_multicard:
            self.fields['address'].label = 'Выберите основной клуб'
        return result

    def clean_birth_date(self):
        birth_date = self.cleaned_data.get('birth_date')
        cur_date = now().date()
        birth_delta = cur_date - birth_date
        years = total_seconds(birth_delta) / (365.25*24*60*60)
        if years < 18:
            raise forms.ValidationError('Вам еще не исполнилось 18 лет.')
        if years > 90:
            raise forms.ValidationError('Вы правда старше 90 лет? Проверьте правильность даты рождения')
        return birth_date

    def clean_address(self):
        address = self.cleaned_data.get('address')
        if not address:
            raise forms.ValidationError('Вы не выбрали клуб')
        return address

    class Meta:
        model = AbonementsAdditionalInfo
        widgets = {
            'first_name': forms.TextInput(attrs={'class':'text'}),
            'last_name': forms.TextInput(attrs={'class':'text'}),
            'father_name': forms.TextInput(attrs={'class':'text'}),
            'passport_code': forms.TextInput(attrs={'class':'text'}),
            'passport_number': forms.TextInput(attrs={'class':'text'}),
            'birth_date': forms.DateInput(attrs={'class':'text mask_date', 'placeholder':'дд.мм.гггг'}),
            'phone': forms.TextInput(attrs={'class':'text mask_phone'}),
            'email': forms.TextInput(attrs={'class':'text'}),
        }


class SimpleActionAdditionalInfoForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        offer = kwargs.get('offer')
        if offer:
            self.offer = offer
            del(kwargs['offer'])
        else:
            raise Exception('Offer is not set')
        result = super(AbonementsAdditionalInfoForm, self).__init__(*args, **kwargs)
        return result

    def clean_birth_date(self):
        birth_date = self.cleaned_data.get('birth_date')
        cur_date = now().date()
        birth_delta = cur_date - birth_date
        years = total_seconds(birth_delta) / (365.25*24*60*60)
        if years < 18:
            raise forms.ValidationError('Вам еще не исполнилось 18 лет.')
        if years > 90:
            raise forms.ValidationError('Вы правда старше 90 лет? Проверьте правильность даты рождения')
        return birth_date

    class Meta:
        model = AbonementsAdditionalInfo
        exclude = ('passport_code', 'passport_number')
        widgets = {
            'first_name': forms.TextInput(attrs={'class':'text'}),
            'last_name': forms.TextInput(attrs={'class':'text'}),
            'father_name': forms.TextInput(attrs={'class':'text'}),
            'birth_date': forms.DateInput(attrs={'class':'text mask_date', 'placeholder':'дд.мм.гггг'}),
            'phone': forms.TextInput(attrs={'class':'text mask_phone'}),
            'email': forms.TextInput(attrs={'class':'text'}),
            }



class AdditionalServicesAddressSelect(forms.Select):
    def render(self, name, value, attrs=None, choices=()):
        if value is None: value = ''
        final_attrs = self.build_attrs(attrs, name=name)
        output = [u'<select%s>' % flatatt(final_attrs)]
        options = u'<option value="">Сначала введите номер карты или договора</option>'
        output.append(options)
        output.append(u'</select>')
        return mark_safe(u'\n'.join(output))


class AbonementsClubCardForm(forms.ModelForm):
    card_number = ClubCardOrAgreementField(widget=forms.TextInput(attrs={'class':'text'}), label='Номер карты или договора')
    address = forms.ModelChoiceField(label='Выберите один из доступных клубов', queryset=PartnerAddress.objects, widget=AdditionalServicesAddressSelect())
    agree_club_rules = forms.BooleanField(label=mark_safe(u'Я прочитал и согласен с <a href="%s" target="_blank">правилами клубов</a>' % (settings.MEDIA_URL+'misc/'+get_settings_value('CLUB_RULES_FILE'),)))

    def __init__(self, *args, **kwargs):
        offer = kwargs.get('offer')
        if offer:
            self.offer = offer
            del(kwargs['offer'])
        else:
            raise Exception('Offer is not set')
        result = super(AbonementsClubCardForm, self).__init__(*args, **kwargs)
        return result

    def clean_card_number(self):
        card_number = self.cleaned_data.get('card_number')
        clubs = get_clubs_by_card_number(card_number)
        if clubs:
            common_clubs = []
            for club in clubs:
                if club in self.offer.addresses.all():
                    common_clubs.append(club)
            if not len(clubs):
                raise forms.ValidationError('Данная акция не распространяется на ваш клуб.')
        else:
            raise forms.ValidationError('Данная акция не распространяется на ваш клуб.')
        return card_number

    def clean_address(self):
        address = self.cleaned_data.get('address')
        card_number = self.cleaned_data.get('card_number')
        if not address:
            raise forms.ValidationError('Вы не выбрали клуб')
        if address not in self.offer.addresses.all():
            raise forms.ValidationError('Акция не распространяется на выбранный клуб')
        card_clubs = get_clubs_by_card_number(card_number)
        if address not in card_clubs:
            raise forms.ValidationError('Выбранный клуб не соответствует вашей карте. Проверьте правильность ввода.')
        return address

    def clean_first_visit_date(self):
        first_visit_date = self.cleaned_data.get('first_visit_date')
        cur_date = now().date()
        if first_visit_date < cur_date:
            raise forms.ValidationError('Вы не можете указать дату раньше сегодняшнего дня')
        return first_visit_date

    def save(self, commit=True):
        result = super(AbonementsClubCardForm, self).save(commit)
        return result

    class Meta:
        model = AdditionalServicesInfo
        widgets = {
            'card_number': forms.TextInput(attrs={'class':'text'}),
            'first_visit_date': forms.DateInput(attrs={'class':'text mask_date', 'placeholder':'дд.мм.гггг'}),
            'first_name': forms.TextInput(attrs={'class':'text'}),
            'last_name': forms.TextInput(attrs={'class':'text'}),
            'father_name': forms.TextInput(attrs={'class':'text'}),
            'passport_code': forms.TextInput(attrs={'class':'text'}),
            'passport_number': forms.TextInput(attrs={'class':'text'}),
            'birth_date': forms.DateInput(attrs={'class':'text mask_date date_picker', 'placeholder':'дд.мм.гггг'}),
            'phone': forms.TextInput(attrs={'class':'text mask_phone'}),
            'email': forms.TextInput(attrs={'class':'text'}),
        }


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
            'first_chars': forms.TextInput(attrs={'class':'text'}),
            'total_chars': forms.TextInput(attrs={'class':'text', 'style':'width:120px;'}),
        }


class GiftOfferForm(forms.Form):
    to_who = forms.CharField(label='Кому', help_text='Введите имя вашего друга, например Иван или Сергей Петров', widget=forms.TextInput(attrs={'class':'text'}))
    from_who = forms.CharField(label='От кого', help_text='Введите свое имя', widget=forms.TextInput(attrs={'class':'text'}))
    delivery_type = forms.ChoiceField(choices=DELIVERY_CHOICES, label='Способ доставки')
    delivery_email = forms.EmailField(label='Адрес E-mail друга', required=False, widget=forms.TextInput(attrs={'class':'text'}))
    message = forms.CharField(widget=forms.Textarea(attrs={'class':'textarea'}), label='Сообщение')

    def clean_delivery_email(self):
        email = self.cleaned_data.get('delivery_email')
        delivery_type = self.cleaned_data.get('delivery_type')
        if delivery_type == 'email':
            if email is None or email == '':
                raise forms.ValidationError('Введите E-mail вашего друга для отправки подарка.')
        return email


class GiftCodeForm(forms.Form):
    code = forms.CharField(label='Введите код купона', widget=forms.TextInput(attrs={'class':'text'}))

    def clean_code(self):
        code = self.cleaned_data.get('code')
        try:
            gift_order = GiftOrder.objects.get(gift_code=code, gift_code_used=False, is_completed=True)
            # if now() - datetime.timedelta(days=3) > gift_order.get_meta_order().get_payment_date():
            #     raise forms.ValidationError('К сожалению, срок действия этого купона истек')
            #if now() > gift_order.offer.end_date:
                #raise forms.ValidationError('К сожалению, эта акция уже закончилась.')
            self.gift_order = gift_order
        except GiftOrder.DoesNotExist:
            raise forms.ValidationError('Неверный код купона')
        return code