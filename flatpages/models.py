# -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext_lazy as _
from seo.models import ModelWithSeo
from ckeditor.fields import RichTextField

# Create your models here.
class FlatPage(ModelWithSeo):
    title = models.CharField(verbose_name='Заголовок', max_length=200)
    content = RichTextField(verbose_name='Содержание', blank=True)
    template_name = models.CharField(verbose_name='Название шаблона', max_length=70, blank=True,
        help_text="Пример: 'flatpages/contact_page.html'. Если не указано, будет использован шаблон 'flatpages/default.html'.", default='flatpages/default.html')
    is_published = models.BooleanField(verbose_name='Опубликовано', default=True)
    class Meta:
        verbose_name = 'Cтраница'
        verbose_name_plural = 'Страницы'
        ordering = ('title',)

    def __unicode__(self):
        return u"%s -- %s" % (self.url, self.title)

    def get_absolute_url(self):
        return self.get_url()
    @models.permalink
    def get_administration_edit_url(self):
        return ('administration.views.pages_edit', (), {'page_id':self.pk})

    @models.permalink
    def get_administration_delete_url(self):
        return ('administration.views.pages_delete', (), {'page_id':self.pk})
    def get_view_for_model(self):
        from flatpages.views import render_flatpage
        return render_flatpage