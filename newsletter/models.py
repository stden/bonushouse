# -*- coding: utf-8 -*-
from django.db import models
from ckeditor.fields import RichTextField
from django.contrib.auth.models import User
from django.db.models import Q
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from newsletter.sms_gate import Gate

# Create your models here.

GENDER_CHOICES = (
    (0, 'Женский'),
    (1, 'Мужской'),
    (2, 'Любой')
)
OFFER_PARTICIPATION_CHOICES = (
    (0, 'Не имеет значения'),
    (1, 'Только покупавшие купоны'),
    (2, 'Только не совершавшие покупок купонов'),
)
AUCTION_PARTICIPATION_CHOICES = (
    (0, 'Не имеет значения'),
    (1, 'Только выигравшие хотя бы 1 аукцион'),
    (2, 'Только не выигрывавшие аукционов'),
)

class NewsletterCampaign(models.Model):
    title = models.CharField(max_length=255, unique=True, verbose_name='Название')
    gender = models.IntegerField(choices=GENDER_CHOICES, verbose_name='Пол')
    min_age = models.PositiveIntegerField(verbose_name='Возраст от')
    max_age = models.PositiveIntegerField(verbose_name='Возраст до')
    include_users_with_no_age = models.BooleanField(verbose_name='Включать пользователей не указавших возраст', default=True)
    min_bonuses_ballance = models.PositiveIntegerField(verbose_name='Количество бонусов от')
    offer_participation = models.IntegerField(choices=OFFER_PARTICIPATION_CHOICES, verbose_name='Участие в акциях')
    auction_participation = models.IntegerField(choices=AUCTION_PARTICIPATION_CHOICES, verbose_name='Участие в аукционах')
    def __unicode__(self):
        return self.title
    def get_subscribers_queryset(self):
        queryset = User.objects.all()
        queryset = queryset.filter(is_active=True)
        queryset.exclude(subscribe_hash__isnull=True)
        #Возраст
        if self.include_users_with_no_age:
            queryset = queryset.filter(Q(userprofile__age__gte=self.min_age, userprofile__age__lte=self.max_age)|Q(userprofile__age=None))
        else:
            queryset = queryset.filter(userprofile__age__gte=self.min_age, userprofile__age__lte=self.max_age)
        #Пол
        if self.gender == 0:
            queryset = queryset.filter(userprofile__gender=0)
        elif self.gender == 1:
            queryset = queryset.filter(userprofile__gender=1)
        #Бонусы
        queryset = queryset.filter(userprofile__bonuses_ballance__gte=self.min_bonuses_ballance)
        #Участие в акциях
        if self.offer_participation == 1:
            queryset = queryset.filter(userprofile__coupons_bought__gt=0)
        elif self.offer_participation == 2:
            queryset = queryset.filter(userprofile__coupons_bought=0)
        #Участие в аукционах
        if self.auction_participation == 1:
            queryset = queryset.filter(userprofile__auctions_won__gt=0)
        elif self.auction_participation == 2:
            queryset = queryset.filter(userprofile__auctions_won=0)
        return queryset
    def get_subscribers_count(self):
        queryset = self.get_subscribers_queryset()
        return queryset.count()
    def get_subscriber_emails_list(self):
        result = []
        queryset = self.get_subscribers_queryset()
        for subscriber in queryset:
            result.append(subscriber.email)
        return result
    def get_subscriber_phones_list(self):
        result = []
        queryset = self.get_subscribers_queryset()
        for subscriber in queryset:
            if subscriber.get_profile().phone:
                result.append(subscriber.get_profile().phone)
        return result
    @models.permalink
    def get_administration_edit_url(self):
        return ('administration.views.emails_campaigns_edit', (), {'campaign_id':self.pk})

    @models.permalink
    def get_administration_delete_url(self):
        return ('administration.views.emails_campaigns_delete', (), {'campaign_id':self.pk})

class NewsletterEmail(models.Model):
    campaigns = models.ManyToManyField('NewsletterCampaign', verbose_name='Кампании')
    subject = models.CharField(max_length=255, verbose_name='Тема письма')
    text = RichTextField(verbose_name='Текст')
    send_date = models.DateTimeField(verbose_name='Дата отправки')
    is_sent = models.BooleanField(default=False)
    def send(self, email):
        subject = self.subject
        from_email = settings.DEFAULT_FROM_EMAIL
        to = email
        text_content = 'Пожалуйста, включите поддержку HTML для просмотра письма'
        html_content = self.text
        msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
        msg.attach_alternative(html_content, "text/html")
        msg.send()

    @models.permalink
    def get_administration_edit_url(self):
        return ('administration.views.emails_edit', (), {'email_id':self.pk})

    @models.permalink
    def get_administration_delete_url(self):
        return ('administration.views.emails_delete', (), {'email_id':self.pk})


class NewsletterSms(models.Model):
    campaigns = models.ManyToManyField('NewsletterCampaign', verbose_name='Кампании')
    text = models.TextField(verbose_name='Текст', max_length=140)
    send_date = models.DateTimeField(verbose_name='Дата отправки')
    is_sent = models.BooleanField(default=False)
    def send(self, phone):
        phone = phone.replace('(','').replace(')','')
        if phone.startswith('8'):
            phone = '7'+phone[1:]
        if not phone.startswith('7'):
            phone = '7'+phone
        smsbliss_gate = Gate(settings.SMSBLISS_LOGIN, settings.SMSBLISS_PASSWORD)
        smsbliss_gate.send(phone, self.text, settings.SMSBLISS_DEFAULT_SENDER)

    @models.permalink
    def get_administration_edit_url(self):
        return ('administration.views.sms_edit', (), {'sms_id':self.pk})

    @models.permalink
    def get_administration_delete_url(self):
        return ('administration.views.sms_delete', (), {'sms_id':self.pk})