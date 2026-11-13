# -*- coding: utf-8 -*-
from django.db import models

# Create your models here.


class CallMeSubjects(models.Model):
    title = models.CharField(max_length=255, verbose_name='Название')
    email = models.EmailField(verbose_name='Адрес E-mail')
    def __unicode__(self):
        return self.title