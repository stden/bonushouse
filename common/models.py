# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from seo.models import ModelWithSeo
from django.db.models.signals import pre_delete
from django.dispatch import receiver

# Create your models here.
class MetroStations(models.Model):
    name = models.CharField(max_length=255, unique=True, verbose_name='Название станции')
    def __unicode__(self):
        return self.name
    class Meta:
        verbose_name = 'Станция метро'
        verbose_name_plural = 'Станции метро'
        ordering = ('name', )


class CategoriesManager(models.Manager):
    def get_query_set(self):
        qs = super(CategoriesManager, self).get_query_set().filter(is_published=True)
        return qs

class Categories(ModelWithSeo):
    title = models.CharField(max_length=255, verbose_name='Название', unique=True)
    description = models.TextField(verbose_name='Описание', blank=True, null=True)
    is_published = models.BooleanField(verbose_name='Опубликовано', default=True)
    objects = CategoriesManager()
    all_objects = models.Manager()
    def __unicode__(self):
        return self.title
    @models.permalink
    def get_administration_edit_url(self):
        return ('administration.views.categories_edit', (), {'category_id':self.pk})
    @models.permalink
    def get_administration_delete_url(self):
        return ('administration.views.categories_delete', (), {'category_id':self.pk})
    def get_photo_object(self):
        content_type = ContentType.objects.get_for_model(self)
        try:
            photo = Photo.objects.get(content_type=content_type, object_id=self.pk)
            return photo
        except Photo.DoesNotExist:
            return None
    def get_view_for_model(self):
        from common.views import view_category
        return view_category
    def get_absolute_url(self):
        url = self.get_friendly_url()
        if url:
            return url
    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

class Photo(models.Model):
    content_type = models.ForeignKey(ContentType, editable=False)
    object_id = models.PositiveIntegerField(editable=False)
    content_object = generic.GenericForeignKey("content_type", "object_id")
    photo = models.ImageField(verbose_name='Фото', upload_to='photos/')
    class Meta:
        verbose_name = 'Фото'
        verbose_name_plural = 'Фото'

class UploadedFile(models.Model):
    file = models.FileField(upload_to='uploads/')
    weight = models.IntegerField(blank=True, null=True)
    add_date = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ('weight',)

@receiver(pre_delete)
def delete_seo_data(sender, instance, **kwargs):
    content_type = ContentType.objects.get_for_model(instance)
    if instance.pk is int:
        Photo.objects.filter(content_type=content_type, object_id=instance.pk).delete()