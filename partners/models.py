# -*- coding: utf-8 -*-
from django.db import models
from seo.models import ModelWithSeo
from common.models import MetroStations
from django.contrib.contenttypes.models import ContentType
from common.models import Photo
from common.models import UploadedFile
from django.contrib.contenttypes import generic
from bonushouse.models import UserFeedbacks
from django.contrib.auth.models import User
from django.conf import settings

# Create your models here.

class Partner(ModelWithSeo):
    title = models.CharField(max_length=255, unique=True, verbose_name='Название')
    description = models.TextField(verbose_name='Описание', blank=True, null=True)
    photos = models.ManyToManyField(UploadedFile, verbose_name='Фотографии')
    site = models.URLField(verbose_name='Сайт', blank=True, null=True)
    is_published = models.BooleanField(verbose_name='Опубликовано', default=True)
    add_date = models.DateTimeField(editable=False, verbose_name='Дата добавления', auto_now_add=True)
    feedbacks = generic.GenericRelation(UserFeedbacks,object_id_field='content_id',content_type_field='content_type')
    admin_user = models.ForeignKey(User, verbose_name='Пользователь-администратор', blank=True, null=True)
    def get_address_list(self):
        return self.partneraddress_set.all()
    def get_photos_list(self):
        result = self.photos.all()
        return result
    def get_rating(self):
        feedbacks_count = self.feedbacks.count()
        if not feedbacks_count:
            return 0
        ratings_sum = 0.0
        for feedback in self.feedbacks.all():
            ratings_sum += feedback.get_author_rating()
        result = ratings_sum / feedbacks_count
        return int(result)
    @models.permalink
    def get_administration_edit_url(self):
        return ('administration.views.partners_edit', (), {'partner_id':self.pk})
    @models.permalink
    def get_administration_delete_url(self):
        return ('administration.views.partners_delete', (), {'partner_id':self.pk})
    def get_view_for_model(self):
        from partners.views import partner_page
        return partner_page
    def __unicode__(self):
        return self.title
    class Meta:
        ordering = ('title', )
        verbose_name = 'Партнер'
        verbose_name_plural = 'Партнеры'


class PartnerAddress(models.Model):
    partner = models.ForeignKey('Partner', verbose_name='Партнер', editable=False)
    title = models.CharField(max_length=255, verbose_name='Название')
    address = models.CharField(max_length=255, verbose_name='Адрес', default='')
    geocode_latitude = models.FloatField(verbose_name='Широта', blank=True, null=True)
    geocode_longitude = models.FloatField(verbose_name='Долгота', blank=True, null=True)
    metro = models.ForeignKey(MetroStations, verbose_name='Метро', blank=True, null=True)
    schedule = models.TextField(verbose_name='Часы работы', blank=True, null=True)
    phone = models.CharField(max_length=255, verbose_name='Телефон', blank=True, null=True)
    fitnesshouse_id = models.IntegerField(verbose_name='ID в базе FH(если есть)', blank=True, null=True)
    def get_geocode_latitude(self):
        return str(self.geocode_latitude).replace(',','.')
    def get_geocode_longitude(self):
        return str(self.geocode_longitude).replace(',','.')
    def __unicode__(self):
        return self.title+' ('+self.address+')'
    class Meta:
        verbose_name = 'Заведение партнера'
        verbose_name_plural = 'Заведения партнеров'


class PartnersPage(models.Model):
    logo = models.ImageField(upload_to='partners/', verbose_name='Логотип')
    title = models.CharField(max_length=255, verbose_name='Заголовок')
    description = models.TextField(verbose_name='Описание')
    site_url = models.URLField(verbose_name='Ссылка на сайт', blank=True, null=True)
    class Meta:
        verbose_name = 'Страница партнеров'
        verbose_name_plural = 'Страница партнеров'

TOTAL_CHARS_SIGN_CHOICES = (
    ('>=', '>='),
    ('=', '='),
)

class ClubCardNumbers(models.Model):
    title = models.CharField(max_length=255, verbose_name='Название шаблона')
    clubs = models.ManyToManyField('PartnerAddress', verbose_name='Клубы', limit_choices_to={'partner__id__in':settings.FITNESSHOUSE_PARTNER_IDS})
    first_chars = models.CharField(max_length=5, verbose_name='Первые цифры')
    total_chars_sign = models.CharField(max_length=3, verbose_name='Цифр в номере карты всего(знак)', default='=', choices=TOTAL_CHARS_SIGN_CHOICES)
    total_chars = models.IntegerField(verbose_name='Цифр в номере карты всего')
    is_multicard = models.BooleanField(verbose_name='Мультикарта')
    def __unicode__(self):
        return self.title