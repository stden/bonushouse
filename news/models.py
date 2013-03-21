# -*- coding: utf-8 -*-
from django.db import models
from seo.models import ModelWithSeo
from ckeditor.fields import RichTextField

# Create your models here.

class News(ModelWithSeo):
    title = models.CharField(max_length=255, verbose_name='Заголовок')
    image = models.ImageField(upload_to='news/', verbose_name='Картинка')
    intro_text = models.TextField(verbose_name='Краткое содержание')
    text = RichTextField(verbose_name='Полный текст новости')
    add_date = models.DateTimeField(verbose_name='Дата добавления', editable=False, auto_now_add=True)
    def __unicode__(self):
        return self.title
    class Meta:
        verbose_name = 'Новость'
        verbose_name_plural = 'Новости'
        ordering = ('-add_date', )
    def get_absolute_url(self):
        return self.get_url()

    @models.permalink
    def get_administration_edit_url(self):
        return ('administration.views.news_edit', (), {'post_id':self.pk})

    @models.permalink
    def get_administration_delete_url(self):
        return ('administration.views.news_delete', (), {'post_id':self.pk})

    def get_view_for_model(self):
        from news.views import view_post
        return view_post