# -*- coding: utf-8 -*-
from django import forms
from auctions.models import Auction
from dbsettings.models import Settings
from django.utils.timezone import now
from bonushouse.utils import total_seconds
from offers.forms import ClubCardOrAgreementField, get_clubs_by_card_number
from model_changelog.signals import important_model_change

class AuctionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        result = super(AuctionForm, self).__init__(*args, **kwargs)
        if self.instance.pk and self.fields.has_key('type'):
            self.fields['type'].widget = forms.HiddenInput()
        return result
    def save(self, commit=True):
        is_new = False
        if not self.instance.pk:
            is_new = True
        result = super(AuctionForm, self).save(commit)
        for photo in self.instance.get_photos_list():
            weight = self.data.get('weight-%s' % (photo.pk))
            if weight is not None and weight.isdigit() and weight != photo.weight:
                photo.weight = weight
                photo.save()
        important_model_change.send(sender=self.instance, created=is_new)
        return result
    def clean_buyout_price(self):
        buyout = self.cleaned_data['buyout_price']
        starting = self.cleaned_data['initial_bid']
        if buyout < starting:
            raise forms.ValidationError('Цена выкупа не может быть меньше начальной цены')
        return buyout
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
    class Meta:
        model = Auction
        widgets = {
            'title': forms.TextInput(attrs={'class':'text'}),
            'description': forms.Textarea(attrs={'class':'textarea','cols':30,'rows':10}),
            'addresses': forms.CheckboxSelectMultiple(),
            'initial_bid': forms.TextInput(attrs={'class':'text'}),
            'bid_step': forms.TextInput(attrs={'class':'text'}),
            'buyout_price': forms.TextInput(attrs={'class':'text'}),
            'start_date': forms.DateTimeInput(attrs={'class':'datetimepicker'}, format='%d.%m.%Y %H:%M'),
            'end_date': forms.DateTimeInput(attrs={'class':'datetimepicker'}, format='%d.%m.%Y %H:%M'),
            'additional_services_term': forms.TextInput(attrs={'class':'text float_left', 'style':'width:60px;margin-right:20px;'}),
            'abonements_term': forms.TextInput(attrs={'class':'text float_left', 'style':'width:60px;margin-right:20px;'}),
            'fh_inner_title': forms.TextInput(attrs={'class': 'text'}),
        }

class AddBidForm(forms.Form):
    amount = forms.IntegerField(label='Ставка', widget=forms.HiddenInput(), min_value=1)
    def __init__(self, *args, **kwargs):
        request = kwargs.get('request')
        auction = kwargs.get('auction')
        if request is not None:
            self.request = request
            del(kwargs['request'])
        if auction is not None:
            self.auction = auction
            del(kwargs['auction'])
        super(AddBidForm, self).__init__(*args, **kwargs)
    def clean_amount(self):
        min_bid_interval = Settings.objects.get(key='AUCTIONS_BID_MIN_INTERVAL').value
        amount = self.cleaned_data['amount']
        if amount > self.request.user.get_profile().get_money_ballance():
            raise forms.ValidationError('У вас недостаточно денег на счету')
        if amount < self.auction.get_actual_price():
            raise forms.ValidationError('Сумма ставки не соответствует текущей стоимости лота')
        if self.auction.get_latest_user_bid(self.request.user):
            bid_delta = now() - self.auction.get_latest_user_bid(self.request.user).add_date
            if total_seconds(bid_delta) < int(min_bid_interval):
                raise forms.ValidationError(u'Вы не можете делать ставки чаще, чем раз в %s секунд' % (min_bid_interval, ))
        return amount


class CardNumberForm(forms.Form):
    card_number = ClubCardOrAgreementField(label='Введите номер договора или карты', widget=forms.TextInput(attrs={'class':'text'}))
    def __init__(self, *args, **kwargs):
        auction = kwargs.get('auction')
        if auction is not None:
            self.auction = auction
            del(kwargs['auction'])
        return super(CardNumberForm, self).__init__(*args, **kwargs)
    def clean_card_number(self):
        card_number = self.cleaned_data.get('card_number')
        clubs = get_clubs_by_card_number(card_number)
        if clubs:
            common_clubs = []
            for club in clubs:
                if club in self.auction.addresses.all():
                    common_clubs.append(club)
            if not len(common_clubs):
                raise forms.ValidationError('Данная акция не распространяется на ваш клуб.')
        else:
            raise forms.ValidationError('Данная акция не распространяется на ваш клуб.')
        return card_number