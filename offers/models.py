# -*- coding: utf-8 -*-
from django.db import models
from common.models import Categories
from seo.models import ModelWithSeo
from django.contrib.contenttypes.models import ContentType
from common.models import Photo
import datetime
from django.utils.timezone import now
from django.utils.html import mark_safe
from common.models import UploadedFile
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.conf import settings
from random import choice
from django.contrib.auth.models import User
from visitor_tracking.models import VisitorInfo
from django.db.models.signals import post_save
from django.dispatch import receiver
from bonushouse.models import UserFeedbacks, BonusTransactions, AccountDepositTransactions
from bonushouse.utils import total_seconds
from bonushouse.abonnement_functions import get_abonements_order_num, get_additional_services_order_num
from bonushouse.models import GENDER_CHOICES
from dbsettings.utils import get_settings_value
from reportlab.graphics.barcode import createBarcodeDrawing
from reportlab.lib.units import mm
from django.core.files.base import ContentFile
import urllib, urllib2, base64, md5
import requests
import random
from bonushouse.models import schedule_fitnesshouse_notification
from ckeditor.fields import RichTextField
from bonushouse.utils import dict_urlencode
from django.template import Template, Context
from django.core.mail import send_mail
from likes.functions import get_likes_count as likes_get_likes_count
from django.core.urlresolvers import reverse_lazy
from payment_gateways.models import PaymentRequest, DolPaymentInfo
from django.utils import timezone
from bonushouse.models import CronFitnesshouseNotifications
from partners.models import Partner, PartnerAddress
from contracts.models import ContractTransaction

TOTAL_CHARS_SIGN_CHOICES = (
    ('>=', '>='),
    ('=', '='),
)


class ActiveOffersManager(models.Manager):
    """Менеджер фильтрующий только опубликованные акции, которые уже начались и еще не кончились"""
    def get_query_set(self):
        cur_time = now()
        return super(ActiveOffersManager, self).get_query_set().filter(is_published=True, is_deleted=False, start_date__lte=cur_time, end_date__gte=cur_time)


class ActiveProlongationOffersManager(models.Manager):
    """Такой же менеджер, только для акций продления"""
    def get_query_set(self):
        cur_time=now()
        return super(ActiveProlongationOffersManager, self).get_query_set().filter(is_published=True, is_deleted=False)


class AllOffersManager(models.Manager):
    def get_query_set(self):
        return super(AllOffersManager, self).get_query_set().filter(is_deleted=False)

OFFER_TYPE_CHOICES = (
    (1, 'Обычная акция'),
    (2, 'Договор FH'),
    (3, 'Дополнительные услуги FH'),
)


class Offers(ModelWithSeo):

    title = models.CharField(max_length=255, verbose_name='Заголовок')
    categories = models.ManyToManyField(Categories, verbose_name='Категории')
    photos = models.ManyToManyField(UploadedFile, verbose_name='Фотографии')
    partner = models.ForeignKey(Partner, verbose_name='Партнер', blank=True, null=True)
    addresses = models.ManyToManyField(PartnerAddress, verbose_name='Заведения')
    quantity = models.PositiveIntegerField(verbose_name='Количество купонов', default=100)
    initial_price = models.PositiveIntegerField(verbose_name='Цена товара/услуги без купона', blank=True, null=True, default=0)
    discount_price = models.PositiveIntegerField(verbose_name='Цена товара/услуги с купоном')
    show_initial_price = models.BooleanField(verbose_name='Отображать цену без скидки?', default=False)
    coupon_price_money = models.PositiveIntegerField(verbose_name='Цена купона в рублях', help_text='Не заполняйте, если купон можно купить только за бонусы', blank=True, null=True)
    coupon_price_bonuses = models.PositiveIntegerField(verbose_name='Цена купона в бонусах', help_text='Не заполняйте, если купон можно купить только за деньги', blank=True, null=True)
    money_bonuses_count = models.PositiveIntegerField(verbose_name='Количество бонусов, начисляемое пользователю при покупке за рубли', default=0)
    short_description = models.TextField(verbose_name='Краткое описание')
    description = RichTextField(verbose_name='Описание акции')
    terms = RichTextField(verbose_name='Условия акции')
    #metro = models.ForeignKey(MetroStations, verbose_name='Станция метро')
    type = models.IntegerField(verbose_name='Тип', choices=OFFER_TYPE_CHOICES, default=1)
    fh_inner_title = models.CharField(max_length=255, verbose_name='Внутренний заголовок для FH', blank=True, null=True)
    abonements_is_multicard = models.BooleanField(verbose_name='Мультикарта', default=False)
    abonements_term = models.IntegerField(blank=True, null=True, verbose_name='Срок действия')
    additional_services_term = models.IntegerField(blank=True, null=True, verbose_name='Срок действия')
    start_date = models.DateTimeField(verbose_name='Дата начала акции')
    end_date = models.DateTimeField(verbose_name='Дата окончания акции')
    is_published = models.BooleanField(verbose_name='Опубликовано', default=True)
    is_deleted = models.BooleanField(editable=False, default=False)
    can_buy_credit = models.BooleanField(default=False, verbose_name='Можно купить в кредит')
    feedbacks = generic.GenericRelation(UserFeedbacks, object_id_field='content_id', content_type_field='content_type')
    add_date = models.DateTimeField(editable=False, verbose_name='Дата добавления', auto_now_add=True)
    views_count = models.PositiveIntegerField(default=0, editable=False)

    #Менеджеры
    objects = ActiveOffersManager()
    all_objects = AllOffersManager()

    def __unicode__(self):
        return self.title

    def get_views_count(self):
        return self.views_count

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

    def delete(self, using=None):
        self.is_deleted = True
        self.save()

    def publish(self):
        self.is_published = True
        self.save()

    def can_buy(self):
        """Проверяет, можно ли купить эту акцию(она началась, она не закончилась, она опубликована)"""
        cur_time = now()
        if self.start_date > cur_time:
            return False
        elif self.end_date < cur_time:
            return False
        elif not self.is_published:
            return False
        elif self.get_bought_count() >= self.quantity:
            return False
        else:
            return True

    def can_buy_for_money(self):
        if self.coupon_price_money:
            return True
        else:
            return False

    def can_buy_for_bonuses(self):
        if self.coupon_price_bonuses:
            return True
        else:
            return False

    def get_photos_list(self):
        """Возвращает список фото прикрепленных к этой акции"""
        return self.photos.all()

    def get_bought_count(self):
        result = 0
        if self.is_abonement():
            count = AbonementOrder.objects.filter(is_completed=True, offer=self).count()
            return count
        elif self.is_additional_service():
            count = AdditionalServicesOrder.objects.filter(is_completed=True, offer=self).count()
            return count
        else:
            quantity_sum = Order.objects.filter(is_completed=True, offer=self).aggregate(models.Sum('quantity'))
        if quantity_sum['quantity__sum']:
            result = quantity_sum['quantity__sum']
        return result

    def get_coupons_used_count(self):
        result = CouponCodes.objects.filter(order__offer=self, is_used=True).count()
        return result

    def get_likes_count(self):
        """
        Возвращает количество лайков данного оффера
        """
        #@TODO: Заглушка. Доделать
        return likes_get_likes_count(self)

    def get_discount_percent(self):
        """Вычисляет процент скидки на основе начальной стоимости товара и стоимости со скидкой"""
        if self.initial_price:
            initial_price = float(self.initial_price)
            discount_price = float(self.discount_price)
            discount_absolute = initial_price - discount_price
            discount_percent = discount_absolute / (initial_price / 100)
            discount_percent = round(discount_percent)
            return int(discount_percent)

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
        total_duration = end_date-start_date
        total_duration = float(total_seconds(total_duration))
        time_passed = cur_time - start_date
        time_passed = float(total_seconds(time_passed))
        time_passed_percent = time_passed / (total_duration/100)
        time_passed_percent = int(round(time_passed_percent))
        return time_passed_percent

    def get_time_left_percent(self):
        return 100 - self.get_time_passed_percent()

    def get_rating(self):
        #@TODO: Доделать
        return 4

    def get_time_left_string(self):
        delta = self.end_date - now()
        #Если акция закончилась, возвращаем нули
        if total_seconds(delta) < 0:
            days = 0
            hours = 0
            minutes = 0
            seconds = 0
        else:
            delta_no_days = total_seconds(delta) - delta.days*3600*24
            hours, remainder = divmod(delta_no_days, 3600)
            minutes, seconds = divmod(remainder, 60)
            days = delta.days
        return mark_safe('<div class="countdown"><span class="days">%d</span> дней и <strong><span class="hours">%02d</span>:<span class="minutes">%02d</span>:<span class="seconds">%02d</span> час.</strong></div>' % (days, hours, minutes, seconds))

    def coupons_left(self):
        """Возвращает количество оставшихся купонов"""
        result = self.quantity
        result -= self.get_bought_count()
        return result

    @models.permalink
    def get_administration_edit_url(self):
        return ('administration.views.offers_edit', (), {'offer_id':self.pk})

    @models.permalink
    def get_partner_edit_url(self):
        return ('partners.views.menu_offers_edit', (), {'offer_id':self.pk})

    @models.permalink
    def get_administration_delete_url(self):
        return ('administration.views.offers_delete', (), {'offer_id':self.pk})

    def get_absolute_url(self):
        return self.get_url()

    def get_view_for_model(self):
        from offers.views import view
        return view

    class Meta:
        verbose_name = 'Акция'
        verbose_name_plural = 'Акции'


PRICE_TYPE_CHOICES = (
    (1, 'Рубли'),
    (2, 'Бонусы'),
)


class AbonementOrder(models.Model):
    """Заказы на покупку договоров в фитнесс-клубы"""
    user = models.ForeignKey(User)
    visitor_info = models.ForeignKey(VisitorInfo, blank=True, null=True)
    offer = models.ForeignKey('Offers')
    additional_info = models.ForeignKey('AbonementsAdditionalInfo')
    price = models.PositiveIntegerField()
    price_type = models.PositiveIntegerField(choices=PRICE_TYPE_CHOICES)
    is_completed = models.BooleanField(default=False)
    transaction_type = models.ForeignKey(ContentType, editable=False, blank=True, null=True)
    transaction_id = models.PositiveIntegerField(editable=False, blank=True, null=True)
    transaction_object = generic.GenericForeignKey("transaction_type", "transaction_id")
    add_date = models.DateTimeField(editable=False, verbose_name='Дата добавления', auto_now_add=True)
    barcode = models.ImageField(upload_to='barcodes/', blank=True, null=True)
    agreement_id = models.CharField(max_length=30, blank=True, null=True)

    def get_meta_order(self):
        return get_meta_order(self)

    def get_start_date(self):
        if self.is_completed:
            return self.get_meta_order().get_payment_date()+datetime.timedelta(days=1)

    def get_end_date(self):
        if self.is_completed:
            start_date = self.get_start_date()
            duration_days = self.offer.abonements_term
            result = start_date + datetime.timedelta(days=duration_days)
            return result

    def complete(self, payment_transaction, is_gift=False):
        """Помечает заказ, как завершенный и генерирует код купона. Ожидает на входе транзакцию оплаты"""
        self.transaction_object = payment_transaction
        if self.price_type == 1 and self.offer.money_bonuses_count and not is_gift:
            self.user.get_profile().deposit_bonuses(self.offer.money_bonuses_count, u"Бонусы за заказ #%s (%s)" % (self.pk, self.offer.title,))
            #Проверяем, если это первая покупка у пользователя и его привел другой пользователь, начисляем бонусы
        if self.user.get_profile().coupons_bought == 0 and self.user.get_profile().refered_by and int(get_settings_value('REFER_FRIEND_BONUSES_COUNT')) and not is_gift:
            self.user.get_profile().refered_by.get_profile().deposit_bonuses(int(get_settings_value('REFER_FRIEND_BONUSES_COUNT')), 'Вознаграждение за приглашенного друга.')
            #Помечаем заказ, как завершенный
        self.is_completed = True
        self.save()
        #Пересчитываем количество купленных купонов и обновляем профиль пользователя
        self.user.get_profile().coupons_bought = get_user_coupons_bought_count(self.user)
        self.user.get_profile().save()
        self.agreement_id = self.get_agreement_id()
        self.barcode.save('barcode.png', self.gen_barcode())
        self.save()

        self.send_notification()

        schedule_fitnesshouse_notification(self)

    def send_notification(self):
        notification_template = Template(get_settings_value('NOTIFICATIONS_COMPLETE_ABONEMENTORDER'))
        notification_context = Context({'LINK':settings.BASE_URL+str(reverse_lazy('cabinet_abonements'))})
        message = notification_template.render(notification_context)
        subject = settings.ORDER_COMPLETE_SUBJECT
        to = [self.user.email, ]
        if self.additional_info.email not in to:
            to.append(self.additional_info.email)
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, to, True)

    def get_agreement_id(self):
        if self.is_completed:
            if self.agreement_id:
                return self.agreement_id
            else:
                sid = self.additional_info.address.fitnesshouse_id
                sid = str(sid)
                order_date = timezone.localtime(self.add_date).strftime('%y%m%d')
                order_num = get_abonements_order_num(self.add_date.date())
                id = 'MB'+sid+'/'+order_date+str(order_num)
                self.agreement_id = id
                self.save()
                return id

    def gen_barcode(self):
        bar_code = createBarcodeDrawing('Standard39', value=self.agreement_id, checksum=False, humanReadable=True, barHeight=10*mm, width=400, height=200, isoScale=1)
        bar_code = ContentFile(bar_code.asString(format='png'))
        return bar_code

    def get_barcode(self):
        if self.barcode:
            return self.barcode
        else:
            self.barcode.save('barcode.png', self.gen_barcode())
            return self.barcode

    def get_price_display(self):
        if self.price_type == 1:
            suffix = ' руб.'
        else:
            suffix = ' бонусов'
        return str(self.price)+suffix

    def notify_fitnesshouse(self):
        """Отправляет уведомление о заказе на обработчик FH"""
        request_params = {}
        request_params['amount'] = str(self.price)+'.00'
        request_params['userid'] = str(self.user.pk)
        request_params['userid_extra'] = u''
        request_params['paymentid'] = str(self.transaction_id)
        request_params['paymode'] = self.price_type
        request_params['orderid'] = self.pk

        if self.price_type == 1:
            sid = settings.FITNESSHOUSE_SID_MONEY
            metaorder = get_meta_order(self)
            if metaorder.paid_via_dol():
                request_params['paymentid'] = 'DOL' + request_params['paymentid']
            else:
                request_params['paymentid'] = 'DEP' + request_params['paymentid']
        else:
            sid = settings.FITNESSHOUSE_SID_BONUSES
        other_info = {}
        other_info['sid'] = sid
        other_info['cid'] = self.get_agreement_id()
        other_info['price'] = unicode(self.price)+u'.00'
        if self.offer.fh_inner_title:
            other_info['type'] = self.offer.fh_inner_title
        else:
            other_info['type'] = self.offer.title
        other_info['sdate'] = timezone.localtime((self.transaction_object.add_date+datetime.timedelta(days=1))).strftime('%Y.%m.%d')
        #self.offer.abonements_term+1 - срок действия договора плюс 1 день, так как абонемент начинается с дня следующего после оплаты
        other_info['edate'] = timezone.localtime((self.transaction_object.add_date + datetime.timedelta(days=self.offer.abonements_term+1))).strftime('%Y.%m.%d')
        other_info['lname'] = self.additional_info.last_name
        other_info['fname'] = self.additional_info.first_name
        if self.additional_info.father_name:
            other_info['sname'] = self.additional_info.father_name
        else:
            other_info['sname'] = u''
        other_info['pserial'] = self.additional_info.passport_code
        other_info['pnumber'] = self.additional_info.passport_number
        other_info['bd'] = timezone.localtime(self.additional_info.birth_date).strftime('%Y.%m.%d')
        other_info['sex'] = self.additional_info.get_gender_display()
        #Смотри http://support.disaers.ru/issues/268
        #other_info['adv'] = self.additional_info.get_how_do_you_know_display()
        other_info['phone'] = self.additional_info.phone
        other_info['email'] = self.additional_info.email
        other_info['cname'] = self.additional_info.address.title

        #Переводим все в cp1251
        for key in request_params.keys():
            request_params[key] = unicode(request_params[key]).encode('cp1251')
        for key in other_info.keys():
            other_info[key] = unicode(other_info[key]).encode('cp1251')
        hash_string = request_params['amount']+other_info['cid']+other_info['cname']+other_info['type']+settings.FH_SALT
        other_info['shash'] = md5.new(hash_string).hexdigest()
        #Урлкодируем и переводим в base64
        other_info_encoded = '&'+urllib.urlencode(dict([k, v] for k, v in other_info.items()))
        other_info_encoded = base64.b64encode(urllib2.unquote(other_info_encoded).replace('+',' '))
        request_params['bh_key'] = md5.new(request_params['amount']+request_params['userid']+request_params['paymentid']+settings.BH_PASSWORD).hexdigest()
        request_params['other_info'] = other_info_encoded
        #Шлем запрос
        if settings.DEBUG:
            fh_url = settings.FITNESSHOUSE_NOTIFY_URL_DEBUG
        else:
            fh_url = settings.FITNESSHOUSE_NOTIFY_URL
        response = requests.get(fh_url, params=request_params, verify=False)
        return response.text


class AdditionalServicesOrder(models.Model):
    """Заказы на покупку дополнительных услуг в фитнесс-клубы"""
    user = models.ForeignKey(User)
    visitor_info = models.ForeignKey(VisitorInfo, blank=True, null=True)
    offer = models.ForeignKey('Offers')
    additional_info = models.ForeignKey('AdditionalServicesInfo')
    price = models.PositiveIntegerField()
    price_type = models.PositiveIntegerField(choices=PRICE_TYPE_CHOICES)
    is_completed = models.BooleanField(default=False)
    transaction_type = models.ForeignKey(ContentType, editable=False, blank=True, null=True)
    transaction_id = models.PositiveIntegerField(editable=False, blank=True, null=True)
    transaction_object = generic.GenericForeignKey("transaction_type", "transaction_id")
    add_date = models.DateTimeField(editable=False, verbose_name='Дата добавления', auto_now_add=True)
    agreement_id = models.CharField(max_length=30, verbose_name='Номер абонемента', editable=False, blank=True, null=True)

    def get_meta_order(self):
        return get_meta_order(self)

    def get_start_date(self):
        if self.is_completed:
            return self.get_meta_order().get_payment_date()+datetime.timedelta(days=1)

    def get_end_date(self):
        if self.is_completed:
            start_date = self.get_start_date()
            duration_days = self.offer.additional_services_term
            result = start_date + datetime.timedelta(days=duration_days)
            return result

    def get_agreement_id(self):
        if self.agreement_id:
            return self.agreement_id
        else:
            order_date = timezone.localtime(self.add_date).strftime('%y%m%d')
            order_num = get_additional_services_order_num(self.add_date.date())
            id = 'BH' + order_date + str(order_num)
            self.agreement_id = id
            self.save()
            return id

    def complete(self, payment_transaction, is_gift=False):
        """Помечает заказ, как завершенный и генерирует код купона. Ожидает на входе транзакцию оплаты"""
        self.transaction_object = payment_transaction
        if self.price_type == 1 and self.offer.money_bonuses_count and not is_gift:
            self.user.get_profile().deposit_bonuses(self.offer.money_bonuses_count, u"Бонусы за заказ #%s (%s)" % (self.pk, self.offer.title,))
            #Проверяем, если это первая покупка у пользователя и его привел другой пользователь, начисляем бонусы
        if self.user.get_profile().coupons_bought == 0 and self.user.get_profile().refered_by and int(get_settings_value('REFER_FRIEND_BONUSES_COUNT')) and not is_gift:
            self.user.get_profile().refered_by.get_profile().deposit_bonuses(int(get_settings_value('REFER_FRIEND_BONUSES_COUNT')), 'Вознаграждение за приглашенного друга.')
        #Помечаем заказ, как завершенный
        self.is_completed = True
        self.save()
        #Пересчитываем количество купленных купонов и обновляем профиль пользователя
        self.user.get_profile().coupons_bought = get_user_coupons_bought_count(self.user)
        self.user.get_profile().save()
        self.agreement_id = self.get_agreement_id()
        self.save()
        self.send_notification()

        schedule_fitnesshouse_notification(self)

    def send_notification(self):
        notification_template = Template(get_settings_value('NOTIFICATIONS_COMPLETE_ADDITIONALSERVICES_ORDER'))
        notification_context = Context({'LINK':settings.BASE_URL+str(reverse_lazy('cabinet_additional_services'))})
        message = notification_template.render(notification_context)
        subject = settings.ORDER_COMPLETE_SUBJECT
        to = [self.user.email, ]
        if self.additional_info.email not in to:
            to.append(self.additional_info.email)
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, to, True)

    def get_price_display(self):
        if self.price_type == 1:
            suffix = ' руб.'
        else:
            suffix = ' бонусов'
        return str(self.price)+suffix

    def notify_fitnesshouse(self):
        """Отправляет уведомление о заказе на обработчик FH"""
        request_params = {}
        request_params['amount'] = str(self.price)+'.00'
        request_params['userid'] = str(self.user.pk)
        request_params['userid_extra'] = u''
        request_params['paymentid'] = str(self.transaction_id)
        request_params['paymode'] = self.price_type
        request_params['orderid'] = self.pk

        if self.price_type == 1:
            sid = settings.ADDITIONAL_SERVICES_SID_MONEY
            metaorder = get_meta_order(self)
            if metaorder.paid_via_dol():
                request_params['paymentid'] = 'DOL' + request_params['paymentid']
            else:
                request_params['paymentid'] = 'DEP' + request_params['paymentid']
        else:
            sid = settings.ADDITIONAL_SERVICES_SID_MONEY
        other_info = {}
        other_info['sid'] = sid
        other_info['cid'] = self.get_agreement_id()
        if self.additional_info.card_number_is_agreement():
            other_info['dognumber'] = self.additional_info.card_number
        else:
            other_info['cardnumber'] = self.additional_info.card_number
        other_info['price'] = unicode(self.price)+u'.00'
        if self.offer.fh_inner_title:
            other_info['type'] = self.offer.fh_inner_title
        else:
            other_info['type'] = self.offer.title
        #other_info['sdate'] = timezone.localtime(self.additional_info.first_visit_date).strftime('%Y.%m.%d')
        #other_info['edate'] = timezone.localtime((self.additional_info.first_visit_date + datetime.timedelta(days=self.offer.additional_services_term))).strftime('%Y.%m.%d')
        other_info['sdate'] = timezone.localtime((self.transaction_object.add_date+datetime.timedelta(days=1))).strftime('%Y.%m.%d')
        #self.offer.abonements_term+1 - срок действия договора плюс 1 день, так как абонемент начинается с дня следующего после оплаты
        other_info['edate'] = timezone.localtime((self.transaction_object.add_date + datetime.timedelta(days=self.offer.additional_services_term+1))).strftime('%Y.%m.%d')
        other_info['lname'] = self.additional_info.last_name
        other_info['fname'] = self.additional_info.first_name
        if self.additional_info.father_name:
            other_info['sname'] = self.additional_info.father_name
        else:
            other_info['sname'] = u''
        other_info['pserial'] = ''
        other_info['pnumber'] = ''
        other_info['bd'] = timezone.localtime(self.additional_info.birth_date).strftime('%Y.%m.%d')
        other_info['sex'] = ''
        other_info['adv'] = ''
        other_info['phone'] = self.additional_info.phone
        other_info['email'] = self.additional_info.email
        other_info['cname'] = self.additional_info.address.title

        #Переводим все в cp1251
        for key in request_params.keys():
            request_params[key] = unicode(request_params[key]).encode('cp1251')
        for key in other_info.keys():
            other_info[key] = unicode(other_info[key]).encode('cp1251')
        hash_string = request_params['amount']+other_info['cid']+other_info['cname']+other_info['type']+settings.FH_SALT
        other_info['shash'] = md5.new(hash_string).hexdigest()
        #Урлкодируем и переводим в base64
        #other_info_encoded = '&'+urllib.urlencode(dict([k, v] for k, v in other_info.items()))
        #other_info_encoded = base64.b64encode(urllib2.unquote(other_info_encoded).replace('+',' '))
        other_info_encoded = '&' + dict_urlencode(other_info)
        other_info_encoded = base64.b64encode(other_info_encoded)
        request_params['bh_key'] = md5.new(request_params['amount']+request_params['userid']+request_params['paymentid']+settings.BH_PASSWORD).hexdigest()
        request_params['other_info'] = other_info_encoded
        #Шлем запрос
        if settings.DEBUG:
            fh_url = settings.FITNESSHOUSE_NOTIFY_URL_DEBUG
        else:
            fh_url = settings.FITNESSHOUSE_NOTIFY_URL
        response = requests.get(fh_url, params=request_params, verify=False)
        return response.text


class Order(models.Model):
    user = models.ForeignKey(User)
    visitor_info = models.ForeignKey(VisitorInfo, blank=True, null=True)
    offer = models.ForeignKey('Offers')
    quantity = models.PositiveIntegerField()
    price = models.PositiveIntegerField()
    price_type = models.PositiveIntegerField(choices=PRICE_TYPE_CHOICES)
    is_completed = models.BooleanField(default=False)
    coupon_codes = models.ManyToManyField('CouponCodes')
    transaction_type = models.ForeignKey(ContentType, editable=False, blank=True, null=True)
    transaction_id = models.PositiveIntegerField(editable=False, blank=True, null=True)
    transaction_object = generic.GenericForeignKey("transaction_type", "transaction_id")
    add_date = models.DateTimeField(editable=False, verbose_name='Дата добавления', auto_now_add=True)
    users_share = models.ManyToManyField(User, related_name='users_share' ,verbose_name='Поделившиеся пользователи')

    def complete(self, payment_transaction, is_gift=False):
        """Помечает заказ, как завершенный и генерирует код купона. Ожидает на входе транзакцию оплаты"""
        self.transaction_object = payment_transaction
        #Генерируем коды купонов и связываем с заказом
        for i in range(0, self.quantity):
            code = CouponCodes(code=generate_code(partner=self.offer.partner), partner=self.offer.partner, is_gift=is_gift)
            code.save()
            self.coupon_codes.add(code)
        #Если оплачивали деньгами и положены бонусы, начисляем пользователю бонусы
        if self.price_type == 1 and self.offer.money_bonuses_count and not is_gift:
            self.user.get_profile().deposit_bonuses(self.offer.money_bonuses_count*self.quantity, u"Бонусы за заказ #%s (%s)" % (self.pk, self.offer.title,))
        #Проверяем, если это первая покупка у пользователя и его привел другой пользователь, начисляем бонусы
        if not is_gift and self.user.get_profile().coupons_bought == 0 and self.user.get_profile().refered_by and int(get_settings_value('REFER_FRIEND_BONUSES_COUNT')) and not is_gift:
            self.user.get_profile().refered_by.get_profile().deposit_bonuses(int(get_settings_value('REFER_FRIEND_BONUSES_COUNT')), 'Вознаграждение за приглашенного друга.')
        #Помечаем заказ, как завершенный
        self.is_completed = True
        self.save()
        if not is_gift:
            notification_template = Template(get_settings_value('NOTIFICATIONS_COMPLETE_ORDER'))
            notification_context = Context({'LINK':settings.BASE_URL+str(reverse_lazy('cabinet'))})
            message = notification_template.render(notification_context)
            subject = settings.ORDER_COMPLETE_SUBJECT
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [self.user.email,], True)
        #Пересчитываем количество купленных купонов и обновляем профиль пользователя
        self.user.get_profile().coupons_bought = get_user_coupons_bought_count(self.user)
        self.user.get_profile().save()


class ContractOrder(models.Model):
    """Заказы на переоформление, продление, перевод в другие клубы.
       Другая модель, т.к. offers не хранятся в бх"""
    user = models.ForeignKey(User)
    old_user = models.ForeignKey(User, related_name='old_user')
    old_contract_number = models.CharField(max_length=255)
    new_contract_number = models.CharField(max_length=255)
    offer_name = models.CharField(max_length=255)
    club_name = models.CharField(max_length=255)
    user_passport_series = models.CharField(max_length=20)
    user_passport_number = models.CharField(max_length=20)
    price = models.PositiveIntegerField(blank=True, null=True, default=0)
    is_completed = models.BooleanField(default=False)
    # coupon_codes = models.ManyToManyField('CouponCodes')
    transaction_object = models.ForeignKey(ContractTransaction)
    add_date = models.DateTimeField(editable=False, verbose_name='Дата добавления', auto_now_add=True)
    old_start_date = models.DateTimeField(editable=False, verbose_name='Дата начала договора')
    end_date = models.DateTimeField(editable=False, verbose_name='Дата окончания')

    def get_start_date(self):
        if self.is_completed:
            return self.transaction_object.complete_date + datetime.timedelta(days=1)

    def complete(self):
        self.is_completed = True
        self.save()

DELIVERY_CHOICES = (
    ('email', 'По Email'),
    ('print', 'Я распечатаю и отдам сам'),
)


class GiftOrder(models.Model):
    user = models.ForeignKey(User)
    visitor_info = models.ForeignKey(VisitorInfo, blank=True, null=True)
    offer = models.ForeignKey('Offers')
    price = models.PositiveIntegerField()
    price_type = models.PositiveIntegerField(choices=PRICE_TYPE_CHOICES)
    is_completed = models.BooleanField(default=False)
    transaction_type = models.ForeignKey(ContentType, editable=False, blank=True, null=True)
    transaction_id = models.PositiveIntegerField(editable=False, blank=True, null=True)
    transaction_object = generic.GenericForeignKey("transaction_type", "transaction_id")
    add_date = models.DateTimeField(editable=False, verbose_name='Дата добавления', auto_now_add=True)
    gift_code = models.CharField(max_length=255, blank=True, null=True)
    gift_code_used = models.BooleanField(default=False)
    gift_from_name = models.CharField(max_length=255)
    gift_to_name = models.CharField(max_length=255)
    gift_delivery_type = models.CharField(max_length=255, choices=DELIVERY_CHOICES)
    gift_delivery_email = models.EmailField(blank=True, null=True)
    gift_message = models.TextField(blank=True, null=True)
    real_order_type = models.ForeignKey(ContentType, editable=False, blank=True, null=True, related_name='+')
    real_order_id = models.PositiveIntegerField(editable=False, blank=True, null=True)
    real_order = generic.GenericForeignKey("real_order_type", "real_order_id")

    def complete(self, payment_transaction):
        """Помечает заказ, как завершенный и генерирует код купона. Ожидает на входе транзакцию оплаты"""
        self.transaction_object = payment_transaction
        #Генерируем подарочный код
        self.gift_code = generate_gift_code()
        #Если оплачивали деньгами и положены бонусы, начисляем пользователю бонусы
        if self.price_type == 1 and self.offer.money_bonuses_count:
            self.user.get_profile().deposit_bonuses(self.offer.money_bonuses_count, u"Бонусы за заказ #%s (%s)" % (self.pk, self.offer.title,))
        #Проверяем, если это первая покупка у пользователя и его привел другой пользователь, начисляем бонусы
        if self.user.get_profile().coupons_bought == 0 and self.user.get_profile().refered_by and int(get_settings_value('REFER_FRIEND_BONUSES_COUNT')):
            self.user.get_profile().refered_by.get_profile().deposit_bonuses(int(get_settings_value('REFER_FRIEND_BONUSES_COUNT')), 'Вознаграждение за приглашенного друга.')
        #Помечаем заказ, как завершенный
        self.is_completed = True
        self.save()
        #Отправляем письмо получателю подарка, если нужно
        if self.gift_delivery_type == 'email':
            context = {}
            context['FROM'] = self.gift_from_name
            context['TO'] = self.gift_to_name
            context['MESSAGE'] = self.gift_message
            context['CODE'] = self.gift_code
            context = Context(context)
            template = Template(get_settings_value('GIFT_EMAIL_TEMPLATE'))
            message = template.render(context)
            subject = get_settings_value('GIFT_EMAIL_SUBJECT')
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [self.gift_delivery_email,], True)
        #Уведомляем покупателя
        self.send_notification()
        #Пересчитываем количество купленных купонов и обновляем профиль пользователя
        self.user.get_profile().coupons_bought = get_user_coupons_bought_count(self.user)
        self.user.get_profile().save()

    def create_real_order(self, user, visitor_info, additional_info=None):
        """Создает реальный заказ, когда юзер использует код подарочного купона, и деактивирует подарочный код"""
        if self.offer.is_abonement():
            if additional_info is None:
                raise Exception('Additional info is missing')
            order = AbonementOrder(user=user, visitor_info=visitor_info, offer=self.offer, additional_info=additional_info, price=self.price, price_type=self.price_type)
            order.save()
            order.complete(self.transaction_object, is_gift=True)
        elif self.offer.is_additional_service():
            if additional_info is None:
                raise Exception('Additional info is missing')
            order = AdditionalServicesOrder(user=user, visitor_info=visitor_info, offer=self.offer, additional_info=additional_info, price=self.price, price_type=self.price_type)
            order.save()
            order.complete(self.transaction_object, is_gift=True)
        else:
            order = Order(user=user, visitor_info=visitor_info, offer=self.offer, quantity=1, price=self.price, price_type=self.price_type)
            order.save()
            order.complete(self.transaction_object, is_gift=True)
        self.gift_code_used = True
        self.real_order = order
        self.save()

    def send_notification(self):
        notification_template = Template(get_settings_value('NOTIFICATIONS_COMPLETE_ORDER'))
        notification_context = Context({'LINK':settings.BASE_URL+str(reverse_lazy('cabinet_gifts'))})
        message = notification_template.render(notification_context)
        subject = settings.ORDER_COMPLETE_SUBJECT
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [self.user.email,], True)

    def get_meta_order(self):
        return get_meta_order(self)

    def get_real_order(self):
        if self.gift_code_used:
            if self.real_order:
                return self.real_order
            else:
                try:
                    order = Order.objects.get(transaction_type=self.transaction_type, transaction_id=self.transaction_id)
                except Order.DoesNotExist:
                    try:
                        order = AbonementOrder.objects.get(transaction_type=self.transaction_type, transaction_id=self.transaction_id)
                    except AbonementOrder.DoesNotExist:
                            order = AdditionalServicesOrder.objects.get(transaction_type=self.transaction_type, transaction_id=self.transaction_id)
                self.real_order = order
                self.save()
                return self.real_order
        else:
            return None


PERIOD_TYPE_CHOICES = (('1', 'До 2 лет'), ('2', 'От 2 до 3 лет'), ('3', 'Больше 3 лет'))


class ProlongationOffers(ModelWithSeo):
    """Акции доступные только для продления, только FH"""
    title = models.CharField(max_length=255, verbose_name='Заголовок')
    partner = models.ForeignKey(Partner, verbose_name='Партнер', blank=True, null=True)
    addresses = models.ManyToManyField(PartnerAddress, verbose_name='Заведения')
    period_type = models.CharField(max_length=1, choices=PERIOD_TYPE_CHOICES, verbose_name='Категории продления')
    price = models.PositiveIntegerField(verbose_name='Цена')
    money_bonuses_count = models.PositiveIntegerField(verbose_name='Количество бонусов, начисляемое пользователю при покупке за рубли', default=0)
    terms = RichTextField(verbose_name='Условия акции')
    fh_inner_title = models.CharField(max_length=255, verbose_name='Внутренний заголовок для FH', blank=True, null=True)
    is_published = models.BooleanField(verbose_name='Опубликовано', default=True)
    is_deleted = models.BooleanField(editable=False, default=False)
    feedbacks = generic.GenericRelation(UserFeedbacks, object_id_field='content_id', content_type_field='content_type')
    add_date = models.DateTimeField(editable=False, verbose_name='Дата добавления', auto_now_add=True)
    views_count = models.PositiveIntegerField(default=0, editable=False)

    objects = ActiveProlongationOffersManager()
    all_objects = AllOffersManager()

    def __unicode__(self):
        return self.title

    def get_views_count(self):
        return self.views_count

    def delete(self, using=None):
        self.is_deleted = True
        self.save()

    def publish(self):
        self.is_published = True
        self.save()

    def get_bought_count(self):
        result = 0
        quantity_sum = Order.objects.filter(is_completed=True, offer=self).aggregate(models.Sum('quantity'))
        if quantity_sum['quantity__sum']:
            result = quantity_sum['quantity__sum']
        return result

    @models.permalink
    def get_administration_edit_url(self):
        return ('administration.views.offers_prolongation_edit', (), {'offer_id':int(self.pk)})

    @models.permalink
    def get_partner_edit_url(self):
        return ('partners.views.menu_offers_edit', (), {'offer_id':self.pk})

    @models.permalink
    def get_administration_delete_url(self):
        return ('administration.views.offers_prolongation_delete', (), {'offer_id':self.pk})

    def get_absolute_url(self):
        return self.get_url()

    def get_view_for_model(self):
        from offers.views import view
        return view

    class Meta:
        verbose_name = 'Акция продления'
        verbose_name_plural = 'Акции продления'


class CouponCodes(models.Model):
    from partners.models import Partner, PartnerAddress
    code = models.CharField(max_length=255)
    partner = models.ForeignKey(Partner)
    is_used = models.BooleanField(default=False)
    used_date = models.DateTimeField(blank=True, null=True)
    barcode = models.ImageField(upload_to='barcodes/', blank=True, null=True)
    is_gift = models.BooleanField(default=False) #  Подарочные купоны не должны выводиться как истекшие, т.к. они не имеют срока действия

    def get_order(self):
        return self.order_set.all()[0]

    def get_barcode(self):
        if self.barcode:
            return self.barcode
        else:
            barcode = self.gen_barcode()
            self.barcode.save('barcode.png', barcode)
            self.save()
            return self.barcode

    def gen_barcode(self):
        bar_code = createBarcodeDrawing('Standard39', value=self.code, checksum=False, humanReadable=True, barHeight=10*mm, width=400, height=200, isoScale=1)
        bar_code = ContentFile(bar_code.asString(format='png'))
        return bar_code

    def set_used(self):
        """Помечает пин-код, как использованный"""
        self.is_used = True
        self.used_date = now()
        self.save()


HOW_YOU_KNOW_CHOICES = (
    (1, u'Интернет'),
    (2, u'Наружная реклама, щиты'),
    (3, u'Рекомендации членов клуба'),
    (4, u'Другое'),
)


class AbonementsAdditionalInfo(models.Model):
    from partners.models import Partner, PartnerAddress
    address = models.ForeignKey(PartnerAddress, verbose_name='Выберите клуб')
    last_name = models.CharField(max_length=255, verbose_name='Фамилия')
    first_name = models.CharField(max_length=255, verbose_name='Имя')
    father_name = models.CharField(max_length=255, verbose_name='Отчество', blank=True, null=True)
    gender = models.IntegerField(choices=GENDER_CHOICES, verbose_name='Пол')
    passport_code = models.CharField(max_length=30, verbose_name='Серия паспорта')
    passport_number = models.CharField(max_length=30, verbose_name='Номер паспорта')
    birth_date = models.DateField(verbose_name='Дата рождения')
    phone = models.CharField(max_length=20, verbose_name='Контактный телефон')
    email = models.EmailField(verbose_name='Электронный адрес', help_text='на данный электронный адрес Вы получите подтверждение')


class AdditionalServicesInfo(models.Model):
    from partners.models import Partner, PartnerAddress
    card_number = models.CharField(max_length=255, verbose_name='Номер карты или договора')
    address = models.ForeignKey(PartnerAddress, blank=True, null=True)
    #first_visit_date = models.DateField(verbose_name='Дата первого визита')
    last_name = models.CharField(max_length=255, verbose_name='Фамилия')
    first_name = models.CharField(max_length=255, verbose_name='Имя')
    father_name = models.CharField(max_length=255, verbose_name='Отчество', blank=True, null=True)
    birth_date = models.DateField(verbose_name='Дата рождения')
    phone = models.CharField(max_length=20, verbose_name='Контактный телефон')
    email = models.EmailField(verbose_name='Электронный адрес', help_text='на данный электронный адрес Вы получите подтверждение')

    def card_number_is_agreement(self):
        if self.card_number[0] == 'M':
            return True
        else:
            return False


def generate_code(partner=None):
    code_length = settings.COUPON_CODE_LENGTH
    code_chars = list(settings.COUPON_CODE_CHARS)
    code = ''
    while(code == '' or CouponCodes.objects.filter(code=code, partner=partner).count()):
        code = ''
        while len(code)<code_length:
            code += choice(code_chars)
    return code

def generate_gift_code():
    code_length = settings.COUPON_CODE_LENGTH
    code_chars = list(settings.COUPON_CODE_CHARS)
    code = ''
    while(code == '' or GiftOrder.objects.filter(gift_code=code, gift_code_used=False).count()):
        code = ''
        while len(code)<code_length:
            code += choice(code_chars)
    return code


def get_user_coupons_bought_count(user):
    result = 0
    bought_sum = Order.objects.filter(user=user, is_completed=True).aggregate(models.Sum('quantity'))
    if bought_sum['quantity__sum']:
        result = bought_sum['quantity__sum']
    bought_sum = AbonementOrder.objects.filter(user=user, is_completed=True).count()
    if bought_sum:
        result += bought_sum
    bought_sum = AdditionalServicesOrder.objects.filter(user=user, is_completed=True).count()
    if bought_sum:
        result += bought_sum
    return result


class MetaOrder(models.Model):
    """Класс, обобщающий информацию о заказах при выборках по разным типам заказов, например, в отчетах"""
    order_type = models.ForeignKey(ContentType, editable=False, blank=True, null=True)
    order_id = models.PositiveIntegerField(editable=False, blank=True, null=True)
    order_object = generic.GenericForeignKey("order_type", "order_id")
    quantity = models.PositiveIntegerField(default=1)
    user = models.ForeignKey(User)
    add_date = models.DateTimeField()
    is_completed = models.BooleanField(default=False)

    def get_type_display(self):
        if type(self.order_object) is Order:
            return 'Простая акция'
        elif type(self.order_object) is AbonementOrder:
            return 'Договор'
        elif type(self.order_object) is AdditionalServicesOrder:
            return 'Абонемент'
        elif type(self.order_object) is GiftOrder:
            return 'Подарок'

    def paid_via_dol(self):
        if type(self.order_object.transaction_object) is PaymentRequest and type(self.order_object.transaction_object.payment_object) is DolPaymentInfo:
            return True
        else:
            return False

    def get_dol_payment_info(self):
        if self.paid_via_dol():
            return self.order_object.transaction_object.payment_object
        else:
            return False

    def get_paid_amount_display(self):
        result = str(self.order_object.transaction_object.amount)
        if type(self.order_object.transaction_object) is BonusTransactions:
            result += ' бонусов'
        else:
            result += ' руб.'
        return result

    def get_paid_source_display(self):
        if type(self.order_object.transaction_object) is BonusTransactions:
            return 'Бонусный счет'
        elif type(self.order_object.transaction_object) is AccountDepositTransactions:
            return 'Денежный депозит'
        elif self.paid_via_dol():
            return 'Деньги Онлайн'
        else:
            return 'Другое'

    def get_payment_id(self):
        if self.is_completed:
            return self.order_object.transaction_object.pk
    def get_payment_date(self):
        if self.is_completed:
            if self.paid_via_dol():
                return self.get_dol_payment_info().add_date
            else:
                return self.order_object.transaction_object.add_date

    def is_gift_order(self):
        if type(self.order_object) is GiftOrder:
            return True
        else:
            return False

    def is_gift_suborder(self):
        if not self.is_completed:
            return None
        if self.is_gift_order():
            return False
        payment_transaction = self.order_object.transaction_object
        try:
            gift_order = GiftOrder.objects.get(transaction_type=ContentType.objects.get_for_model(payment_transaction), transaction_id=payment_transaction.pk)
            return True
        except GiftOrder.DoesNotExist:
            return False

    def get_fitnesshouse_notifications(self):
        return CronFitnesshouseNotifications.objects.filter(content_type=self.order_type, content_id=self.order_id)


def get_meta_order(model_instance):
    try:
        content_type = ContentType.objects.get_for_model(model_instance)
        metaorder = MetaOrder.objects.get(order_type=content_type, order_id=model_instance.pk)
        return metaorder
    except MetaOrder.DoesNotExist:
        order_create_meta_order(None, model_instance, False, None, None)
        return get_meta_order(model_instance)
        return None



@receiver(post_save, sender=Order)
@receiver(post_save, sender=AbonementOrder)
@receiver(post_save, sender=AdditionalServicesOrder)
@receiver(post_save, sender=GiftOrder)
def order_create_meta_order(sender, instance, created, raw, using, **kwargs):
    need_create = False
    if created:
        need_create = True
    else:
        content_type = ContentType.objects.get_for_model(instance)
        try:
            metaorder = MetaOrder.objects.get(order_type=content_type, order_id=instance.pk)
        except MetaOrder.DoesNotExist:
            need_create = True
    if need_create:
        if instance is Order:
            quantity = instance.quantity
        else:
            quantity = 1
        metaorder = MetaOrder(order_object=instance, is_completed=instance.is_completed, add_date=instance.add_date, user=instance.user, quantity=quantity)
        metaorder.add_date = instance.add_date
        metaorder.save()
    need_update = False
    if (instance is Order and instance.quantity != metaorder.quantity) or instance.is_completed != metaorder.is_completed or instance.user != metaorder.user:
        need_update = True
    if need_update:
        if instance is Order:
            quantity = instance.quantity
        else:
            quantity = 1
        metaorder.quantity = quantity
        metaorder.user = instance.user
        metaorder.is_completed = instance.is_completed
        metaorder.add_date = instance.add_date
        metaorder.save()

