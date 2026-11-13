# -*- coding: utf-8 -*-
from django.db import models
from visitor_tracking.models import VisitorInfo
from django.db.models import F
from ckeditor.fields import RichTextField

REGION_CHOICES = (
    ('BENEATH_HEADER', 'Под хедером'),
    ('HOME_PAGE_TOP', 'Главная страница(вверху)'),
)

class BannersManager(models.Manager):
    def get_query_set(self):
        query_set = super(BannersManager, self).get_query_set().filter(is_published=True, impressions__lt=F('show_max_count'), clicks__lt=F('click_max_count'))
        return query_set


# Create your models here.
class Banner(models.Model):
    title = models.CharField(max_length=255, verbose_name='Название', unique=True)
    region = models.CharField(max_length=255, verbose_name='Место', choices=REGION_CHOICES)
    code = RichTextField(verbose_name='Код банера', help_text='Используйте {{ LINK }} в месте, где хотите разместить ссылку. Например <a href="{{ LINK }}">Банер</a>')
    url = models.URLField(verbose_name='Ссылка')
    show_start_date = models.DateField(verbose_name='Дата начала показов')
    show_end_date = models.DateField(verbose_name='Дата окончания показов', blank=True, null=True)
    show_max_count = models.PositiveIntegerField(verbose_name='Кол-во показов')
    click_max_count = models.PositiveIntegerField('Кол-во кликов')
    is_published = models.BooleanField(verbose_name='Опубликовано', default=True)
    add_date = models.DateTimeField(editable=False, auto_now_add=True, verbose_name='Дата добавления')
    clicks = models.IntegerField(editable=False, default=0)
    impressions = models.IntegerField(editable=False, default=0)
    objects = BannersManager()
    admin_objects = models.Manager()
    def get_impressions_count(self):
        #Возвращает количество показов данного банера
        return self.impressions
    def get_clicks_count(self):
        #Возвращает количество кликов данного банера
        return self.clicks
    @models.permalink
    def get_administration_edit_url(self):
        return ('administration.views.advertising_banner_edit', (), {'banner_id':self.pk})
    @models.permalink
    def get_administration_delete_url(self):
        return ('administration.views.advertising_banner_delete', (), {'banner_id':self.pk})
    @models.permalink
    def get_click_url(self):
        return ('advertising.views.banner_click', (), {'banner_id': self.pk})

class BannerImpressions(models.Model):
    banner = models.ForeignKey('Banner', verbose_name='Баннер')
    visitor_info = models.ForeignKey(VisitorInfo)
    add_date = models.DateTimeField(editable=False, auto_now_add=True, verbose_name='Дата показа')

class BannerClicks(models.Model):
    banner = models.ForeignKey('Banner', verbose_name='Баннер')
    visitor_info = models.ForeignKey(VisitorInfo)
    add_date = models.DateTimeField(editable=False, auto_now_add=True, verbose_name='Дата клика')