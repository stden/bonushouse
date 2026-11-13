# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session


class ModelWithSeo(models.Model):
    def get_seo_meta_object(self):
        content_type = ContentType.objects.get_for_model(self)
        try:
            meta = ModelMetaTags.objects.get(content_type=content_type, object_id=self.pk)
            return meta
        except ModelMetaTags.DoesNotExist:
            return None
    def get_seo_url_object(self):
        content_type = ContentType.objects.get_for_model(self)
        try:
            friendly_url = ModelFriendlyUrl.objects.get(content_type=content_type, object_id=self.pk)
            return friendly_url
        except ModelFriendlyUrl.DoesNotExist:
            return None
    def get_url(self):
        url = self.get_friendly_url()
        if url:
            return url
        else:
            return self.get_absolute_url()
    def get_friendly_url(self):
        content_type = ContentType.objects.get_for_model(self)
        try:
            url = ModelFriendlyUrl.objects.get(content_type=content_type, object_id=self.pk)
            return url.friendly_url
        except ModelFriendlyUrl.DoesNotExist:
            return None
    class Meta:
        abstract = True


# Create your models here.
class ModelMetaTags(models.Model):
    meta_title = models.CharField(max_length=255, verbose_name='Title')
    meta_keywords = models.CharField(max_length=255, verbose_name='Meta Keywords')
    meta_description = models.CharField(max_length=255, verbose_name='Meta Description')
    content_type = models.ForeignKey(ContentType, editable=False)
    object_id = models.PositiveIntegerField(editable=False)
    content_object = generic.GenericForeignKey("content_type", "object_id")
    class Meta:
        unique_together = ('content_type','object_id',)
        verbose_name = 'Мета-теги'
        verbose_name_plural = 'Мета-теги'
    def __unicode__(self):
        return self.meta_title

class ModelFriendlyUrl(models.Model):
    friendly_url = models.CharField(max_length=255, unique=True, verbose_name='ЧПУ', help_text='Не забудьте указать ведущий и замыкающий /. Например /news/post/')
    content_type = models.ForeignKey(ContentType, editable=False)
    object_id = models.PositiveIntegerField(editable=False)
    content_object = generic.GenericForeignKey("content_type", "object_id")
    class Meta:
        unique_together = ('content_type','object_id',)
        verbose_name = 'ЧПУ'
        verbose_name_plural = 'ЧПУ'
    def __unicode__(self):
        return self.friendly_url

@receiver(pre_delete)
def delete_seo_data(sender, instance, **kwargs):
    content_type = ContentType.objects.get_for_model(instance)
    if instance.pk is int:
        meta = ModelMetaTags.objects.filter(content_type=content_type, object_id=instance.pk).delete()
        url = ModelFriendlyUrl.objects.filter(content_type=content_type, object_id=instance.pk).delete()
