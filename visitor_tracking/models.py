# -*- coding: utf-8 -*-
from django.db import models

# Create your models here.

class VisitorInfo(models.Model):
    ip = models.IPAddressField(verbose_name='IP-адрес')
    referer = models.CharField(max_length=255, verbose_name='HTTP Referrer', blank=True, null=True)
    add_date = models.DateTimeField(verbose_name='Дата добавления', editable=False, auto_now_add=True)