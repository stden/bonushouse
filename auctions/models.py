# -*- coding: utf-8 -*-
import datetime
from random import choice
import md5
import base64
from datetime import timedelta

from django.db import models
from django.utils.timezone import now
from django.utils.html import mark_safe
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from reportlab.graphics.barcode import createBarcodeDrawing
from reportlab.lib.units import mm
from django.core.files.base import ContentFile
import requests
from django.template import Template, Context
from django.core.mail import send_mail
from django.core.urlresolvers import reverse_lazy
from django.utils import timezone

from common.models import UploadedFile
from seo.models import ModelWithSeo
from bonushouse.utils import total_seconds
from offers.models import AbonementsAdditionalInfo, AdditionalServicesInfo
from bonushouse.abonnement_functions import get_abonements_order_num, get_additional_services_order_num
from bonushouse.utils import dict_urlencode
from dbsettings.utils import get_settings_value


# Create your models here.

class ActiveAuctionsManager(models.Manager):
    """Менеджер фильтрующий только опубликованные акции, которые уже начались и еще не кончились"""

    def get_query_set(self):
        cur_time = now()
        return super(ActiveAuctionsManager, self).get_query_set().filter(is_published=True, is_completed=False,
                                                                         start_date__lte=cur_time,
                                                                         end_date__gte=cur_time)


AUCTION_TYPE_CHOICES = (
    (1, 'Обычная акция'),
    (2, 'Договор FH'),
    (3, 'Дополнительные услуги FH'),
)


class Auction(ModelWithSeo):
    from partners.models import Partner, PartnerAddress

    title = models.CharField(max_length=255, verbose_name='Название')
    description = models.TextField(verbose_name='Описание')
    photos = models.ManyToManyField(UploadedFile, verbose_name='Фотографии')
    type = models.IntegerField(verbose_name='Тип', choices=AUCTION_TYPE_CHOICES, default=1)
    fh_inner_title = models.CharField(max_length=255, verbose_name='Внутренний заголовок для FH', blank=True, null=True)
    abonements_is_multicard = models.BooleanField(verbose_name='Мультикарта', default=False)
    partner = models.ForeignKey(Partner, verbose_name='Партнер', blank=True, null=True)
    addresses = models.ManyToManyField(PartnerAddress, verbose_name='Заведения')
    initial_bid = models.PositiveIntegerField(verbose_name='Начальная ставка')
    bid_step = models.PositiveIntegerField(verbose_name='Шаг аукциона')
    buyout_price = models.PositiveIntegerField(verbose_name='Цена выкупа')
    start_date = models.DateTimeField(verbose_name='Дата начала')
    end_date = models.DateTimeField(verbose_name='Дата окончания')
    is_published = models.BooleanField(verbose_name='Опубликовано', default=True)
    is_completed = models.BooleanField(default=False, verbose_name='Аукцион завершился', editable=False)
    winner = models.ForeignKey(User, verbose_name='Победитель', blank=True, null=True, editable=False)
    coupon_code = models.CharField(max_length=255, verbose_name='Код купона', blank=True, null=True, editable=False)
    coupon_code_used = models.BooleanField(default=False, verbose_name='Код использован', editable=False)
    add_date = models.DateTimeField(editable=False, verbose_name='Дата добавления', auto_now_add=True)
    completed_date = models.DateTimeField(editable=False, verbose_name='Дата фактического окончания', blank=True,
                                          null=True)
    abonements_additional_info = models.ForeignKey(AbonementsAdditionalInfo, blank=True, null=True, editable=False)
    additional_services_additional_info = models.ForeignKey(AdditionalServicesInfo, blank=True, null=True,
                                                            editable=False)
    abonements_term = models.IntegerField(blank=True, null=True, verbose_name='Срок действия')
    additional_services_term = models.IntegerField(blank=True, null=True, verbose_name='Срок действия')
    barcode = models.ImageField(upload_to='barcodes/', blank=True, null=True)
    agreement_id = models.CharField(max_length=255, verbose_name='Номер договора', blank=True, null=True,
                                    editable=False)
    #Менеджеры
    objects = ActiveAuctionsManager()
    all_objects = models.Manager()

    class Meta:
        verbose_name = 'Аукцион'
        verbose_name_plural = 'Аукционы'

    def __unicode__(self):
        return self.title

    def is_abonement(self):
        if self.type == 2:
            return True
        else:
            return False

    def is_additional_service(self):
        if self.type == 3:
            return True
        else:
            return False

    def additional_services_get_user_card_number(self, user):
        try:
            card_number = AdditionalServicesCardNumbers.objects.get(auction=self, user=user)
            return card_number.card_number
        except AdditionalServicesCardNumbers.DoesNotExist:
            return None

    def additional_services_add_user_card_number(self, user, card_number):
        card_number = AdditionalServicesCardNumbers(auction=self, user=user, card_number=card_number)
        card_number.save()

    def additional_info_needed(self):
        if self.is_abonement() and not self.abonements_additional_info:
            return True
        elif self.is_additional_service() and not self.additional_services_additional_info:
            return True
        else:
            return False

    def can_bid(self):
        """Проверяет, можно ли делать ставки на этот аукцион(он начался, она не закончился, он опубликован)"""
        cur_time = now()
        if self.start_date > cur_time:
            return False
        elif self.end_date < cur_time:
            return False
        elif not self.is_published:
            return False
        elif self.is_completed:
            return False
        else:
            return True

    def can_print(self):
        if self.is_completed and not self.additional_info_needed():
            return True
        else:
            return False

    def get_winner_bid(self):
        return self.get_latest_bid()

        #@TODO: Доделать завершение аукциона. Сделать обновление счетчика auctions_won в профиле юзера
    def complete(self):
        """Вызывается, когда аукцион истек или достигнута цена выкупа"""
        winner_bid = self.get_latest_bid()
        self.completed_date = now()
        self.is_completed = True
        if winner_bid:
            winner_user = winner_bid.user
            if self.is_abonement():
                self.agreement_id = self.get_agreement_id()
                self.barcode.save('barcode.png', self.gen_barcode())
            elif self.is_additional_service():
                self.agreement_id = self.get_agreement_id()
            else:
                code = generate_code()
                self.coupon_code = code
            self.winner = winner_user
            notification_template = Template(get_settings_value('NOTIFICATIONS_COMPLETE_AUCTION'))
            notification_context = Context(
                {'LINK': settings.BASE_URL + str(reverse_lazy('cabinet_auctions')), 'AUCTION': self})
            message = notification_template.render(notification_context)
            subject = settings.ORDER_COMPLETE_SUBJECT
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [self.winner.email, ], True)
        self.is_completed = True
        self.save()

    def get_barcode(self):
        if not self.barcode:
            self.barcode.save('barcode.png', self.gen_barcode())
            self.save()
        return self.barcode

    def gen_barcode(self):
        bar_code = createBarcodeDrawing('Standard39', value=self.get_agreement_id(), checksum=False, humanReadable=True,
                                        barHeight=10 * mm, width=400, height=200, isoScale=1)
        bar_code = ContentFile(bar_code.asString(format='png'))
        return bar_code

    def get_photos_list(self):
        return self.photos.all()

    def get_bids_list(self):
        return self.auctionbid_set.all()

    def get_bids_count(self):
        """
        Возвращает количество ставок на данный лот
        """
        return self.auctionbid_set.count()

    def get_latest_bid(self):
        """Возвращает самую последнюю ставку на лот"""
        try:
            return self.auctionbid_set.latest('add_date')
        except AuctionBid.DoesNotExist:
            return None

    def get_latest_user_bid(self, user):
        """Возвращает самую последнюю ставку пользователя на лот"""
        try:
            return self.auctionbid_set.filter(user=user).latest('add_date')
        except AuctionBid.DoesNotExist:
            return None

    def get_actual_price(self):
        if self.get_bids_count():
            price = self.get_latest_bid().amount
        else:
            #Если ставок нет, возвращаем начальную ставку указанную при создании аукциона
            return self.initial_bid
        if price + self.bid_step >= self.buyout_price:
            #Если сумма последней ставки и шага превышает цену выкупа, считаем, что новая ставка будет выкупом и возвращаем цену выкупа
            return self.buyout_price
        else:
            return price + self.bid_step

    def unlock_beaten_bids(self):
        """Разблокирует перебитые ставки на счетах пользователей"""
        latest_bid = self.get_latest_bid()
        if latest_bid:
            beaten_bids = self.auctionbid_set.exclude(pk=latest_bid.pk)
            for bid in beaten_bids:
                if bid.transaction:
                    bid.transaction.delete()

    def get_time_passed_percent(self):
        """
           Возвращает в процентах, какой период акции уже прошел
        """
        start_date = self.start_date
        end_date = self.end_date
        cur_time = now()
        if cur_time < start_date:
            #Акция еще даже не начиналась. Возвращаем 0
            return 0
        if cur_time > end_date:
            #Акция уже закончилась. Возвращаем 100
            return 100
        total_duration = end_date - start_date
        total_duration = float(total_seconds(total_duration))
        time_passed = cur_time - start_date
        time_passed = float(total_seconds(time_passed))
        time_passed_percent = time_passed / (total_duration / 100)
        time_passed_percent = int(round(time_passed_percent))
        return time_passed_percent

    def get_time_left_percent(self):
        return 100 - self.get_time_passed_percent()

    def get_time_left_string(self):
        delta = self.end_date - now()
        #Если аукцион закончился, возвращаем нули
        if total_seconds(delta) < 0:
            days = 0
            hours = 0
            minutes = 0
            seconds = 0
        else:
            delta_no_days = total_seconds(delta) - delta.days * 3600 * 24
            hours, remainder = divmod(delta_no_days, 3600)
            minutes, seconds = divmod(remainder, 60)
            days = delta.days
        return mark_safe(
            '<div class="countdown"><span class="days">%d</span> дней и <strong><span class="hours">%02d</span>:<span class="minutes">%02d</span>:<span class="seconds">%02d</span> час.</strong></div>' % (
            days, hours, minutes, seconds))

    def get_agreement_id(self):
        if self.is_completed:
            if self.is_abonement():
                if self.agreement_id:
                    return self.agreement_id
                else:
                    sid = self.abonements_additional_info.address.fitnesshouse_id
                    sid = str(sid)
                    order_date = timezone.localtime(self.completed_date).strftime('%y%m%d')
                    order_num = get_abonements_order_num(self.completed_date.date())
                    id = 'MB' + sid + '/' + order_date + str(order_num)
                    self.agreement_id = id
                    self.save()
                    return id
            elif self.is_additional_service():
                if self.agreement_id:
                    return self.agreement_id
                else:
                    order_date = timezone.localtime(self.add_date).strftime('%y%m%d')
                    order_num = get_additional_services_order_num(self.add_date.date())
                    id = 'BH' + order_date + str(order_num)
                    self.agreement_id = id
                    self.save()
                    return id
            else:
                return self.coupon_code

    def get_coupon_code(self):
        if self.is_completed:
            if self.is_abonement() or self.is_additional_service():
                return self.get_agreement_id()
            else:
                if not self.coupon_code:
                    self.coupon_code = generate_code()
                    self.save()
                return self.coupon_code


    def notify_fitnesshouse(self):
        """Отправляет уведомление о заказе на обработчик FH"""
        if not self.is_completed:
            raise Exception('Subject is not completed')
        if self.is_abonement():
            request_params = {'amount': str(self.get_winner_bid().amount) + '.00',
                              'userid': str(self.winner.pk),
                              'userid_extra': u'',
                              'paymentid': str(self.get_winner_bid().transaction_id),
                              'paymode': 1,
                              'orderid': self.pk}

            sid = settings.FITNESSHOUSE_SID_MONEY
            other_info = {}
            other_info['sid'] = sid
            other_info['cid'] = self.get_agreement_id()
            other_info['price'] = request_params['amount']
            if self.fh_inner_title:
                other_info['type'] = self.fh_inner_title
            else:
                other_info['type'] = self.title
            other_info['sdate'] = timezone.localtime((self.completed_date + timedelta(days=1))).strftime('%Y.%m.%d')
            #self.abonements_term+1 - срок действия договора плюс 1 день, так как абонемент начинается с для следующего после оплаты
            other_info['edate'] = timezone.localtime(
                (self.completed_date + datetime.timedelta(days=self.abonements_term + 1))).strftime('%Y.%m.%d')
            other_info['lname'] = self.abonements_additional_info.last_name
            other_info['fname'] = self.abonements_additional_info.first_name
            if self.abonements_additional_info.father_name:
                other_info['sname'] = self.abonements_additional_info.father_name
            else:
                other_info['sname'] = u''
            other_info['pserial'] = self.abonements_additional_info.passport_code
            other_info['pnumber'] = self.abonements_additional_info.passport_number
            other_info['bd'] = timezone.localtime(self.abonements_additional_info.birth_date).strftime('%Y.%m.%d')
            other_info['sex'] = self.abonements_additional_info.get_gender_display()
            #Смотри http://support.disaers.ru/issues/268
            #other_info['adv'] = self.abonements_additional_info.get_how_do_you_know_display()
            other_info['phone'] = self.abonements_additional_info.phone
            other_info['email'] = self.abonements_additional_info.email
            other_info['cname'] = self.abonements_additional_info.address.title

            #Переводим все в cp1251
            for key in request_params.keys():
                request_params[key] = unicode(request_params[key]).encode('cp1251')
            for key in other_info.keys():
                other_info[key] = unicode(other_info[key]).encode('cp1251')
            hash_string = request_params['amount'] + other_info['cid'] + other_info['cname'] + other_info[
                'type'] + settings.FH_SALT
            other_info['shash'] = md5.new(hash_string).hexdigest()
            #Урлкодируем и переводим в base64
            other_info_encoded = '&' + dict_urlencode(other_info)
            other_info_encoded = base64.b64encode(other_info_encoded)
            request_params['bh_key'] = md5.new(request_params['amount'] + request_params['userid'] + request_params[
                'paymentid'] + settings.BH_PASSWORD).hexdigest()
            request_params['other_info'] = other_info_encoded
            #Шлем запрос
            if settings.DEBUG:
                fh_url = settings.FITNESSHOUSE_NOTIFY_URL_DEBUG
            else:
                fh_url = settings.FITNESSHOUSE_NOTIFY_URL
            response = requests.get(fh_url, params=request_params, verify=False)
            return response.text
        elif self.is_additional_service():
            request_params = {}
            request_params['amount'] = str(self.get_winner_bid().amount) + '.00'
            request_params['userid'] = str(self.winner.pk)
            request_params['userid_extra'] = u''
            request_params['paymentid'] = str(self.get_winner_bid().transaction_id)
            request_params['paymode'] = 1
            request_params['orderid'] = self.pk

            sid = settings.ADDITIONAL_SERVICES_SID_MONEY
            other_info = {}
            other_info['sid'] = sid
            other_info['cid'] = self.get_agreement_id()
            if self.additional_services_additional_info.card_number_is_agreement():
                other_info['dognumber'] = self.additional_services_additional_info.card_number
            else:
                other_info['cardnumber'] = self.additional_services_additional_info.card_number
            other_info['price'] = request_params['amount']
            other_info['type'] = self.title
            #other_info['sdate'] = timezone.localtime(self.additional_services_additional_info.first_visit_date).strftime('%Y.%m.%d')
            #other_info['edate'] = timezone.localtime((self.additional_services_additional_info.first_visit_date + datetime.timedelta(days=self.additional_services_term))).strftime('%Y.%m.%d')
            other_info['sdate'] = timezone.localtime((self.completed_date + timedelta(days=1))).strftime('%Y.%m.%d')
            other_info['edate'] = timezone.localtime(((self.completed_date + timedelta(days=1)) + datetime.timedelta(
                days=self.additional_services_term))).strftime('%Y.%m.%d')
            other_info['lname'] = self.additional_services_additional_info.last_name
            other_info['fname'] = self.additional_services_additional_info.first_name
            if self.additional_services_additional_info.father_name:
                other_info['sname'] = self.additional_services_additional_info.father_name
            else:
                other_info['sname'] = u''
            other_info['pserial'] = ''
            other_info['pnumber'] = ''
            other_info['bd'] = timezone.localtime(self.additional_services_additional_info.birth_date).strftime(
                '%Y.%m.%d')
            other_info['sex'] = ''
            other_info['adv'] = ''
            other_info['phone'] = self.additional_services_additional_info.phone
            other_info['email'] = self.additional_services_additional_info.email
            other_info['cname'] = self.additional_services_additional_info.address.title

            #Переводим все в cp1251
            for key in request_params.keys():
                request_params[key] = unicode(request_params[key]).encode('cp1251')
            for key in other_info.keys():
                other_info[key] = unicode(other_info[key]).encode('cp1251')
            hash_string = request_params['amount'] + other_info['cid'] + other_info['cname'] + other_info[
                'type'] + settings.FH_SALT
            other_info['shash'] = md5.new(hash_string).hexdigest()
            #Урлкодируем и переводим в base64
            #other_info_encoded = '&'+urllib.urlencode(dict([k, v] for k, v in other_info.items()))
            #other_info_encoded = base64.b64encode(urllib2.unquote(other_info_encoded).replace('+',' '))
            other_info_encoded = '&' + dict_urlencode(other_info)
            other_info_encoded = base64.b64encode(other_info_encoded)
            request_params['bh_key'] = md5.new(request_params['amount'] + request_params['userid'] + request_params[
                'paymentid'] + settings.BH_PASSWORD).hexdigest()
            request_params['other_info'] = other_info_encoded
            #Шлем запрос
            if settings.DEBUG:
                fh_url = settings.FITNESSHOUSE_NOTIFY_URL_DEBUG
            else:
                fh_url = settings.FITNESSHOUSE_NOTIFY_URL
            response = requests.get(fh_url, params=request_params, verify=False)
            return response.text

    @models.permalink
    def get_administration_edit_url(self):
        return ('administration.views.auctions_edit', (), {'auction_id': self.pk})

    @models.permalink
    def get_administration_delete_url(self):
        return ('administration.views.auctions_delete', (), {'auction_id': self.pk})

    @models.permalink
    def get_absolute_url(self):
        return ('auctions.views.view', (), {'auction_id': self.pk})

    @models.permalink
    def get_add_bid_url(self):
        return ('auctions.views.add_bid_form', (), {'auction_id': self.pk})

    def get_view_for_model(self):
        from auctions.views import view

        return view


class AdditionalServicesCardNumbers(models.Model):
    auction = models.ForeignKey('Auction')
    user = models.ForeignKey(User)
    card_number = models.CharField(max_length='255')


class AuctionBid(models.Model):
    auction = models.ForeignKey('Auction', verbose_name='Аукцион')
    amount = models.PositiveIntegerField(verbose_name='Сумма')
    user = models.ForeignKey(User, verbose_name='Пользователь')
    transaction_type = models.ForeignKey(ContentType, editable=False, blank=True, null=True)
    transaction_id = models.PositiveIntegerField(editable=False, blank=True, null=True)
    transaction = generic.GenericForeignKey("transaction_type", "transaction_id")
    add_date = models.DateTimeField(editable=False, verbose_name='Дата добавления', auto_now_add=True)

    class Meta:
        ordering = ('-add_date',)


def generate_code():
    code_length = settings.COUPON_CODE_LENGTH
    code_chars = list(settings.COUPON_CODE_CHARS)
    code = ''
    while (code == '' or Auction.all_objects.filter(coupon_code=code, coupon_code_used=False).count()):
        code = ''
        while len(code) < code_length:
            code += choice(code_chars)
    return code