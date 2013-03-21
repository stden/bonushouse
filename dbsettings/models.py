# -*- coding: utf-8 -*-
from django.db import models

# Create your models here.

SETTINGS_TYPE_CHOICES = (
    (1, 'Целое Число'),
    (4, 'Число с плавающей точкой'),
    (2, 'Короткий текст'),
    (3, 'Длинный текст'),
    (5, 'E-mail'),
    (6, 'Список значений(каждое с новой строки)'),
    (10, 'Файл'),
)

class Settings(models.Model):
    key = models.CharField(max_length=255, verbose_name='Ключ', unique=True)
    value = models.TextField(verbose_name='Значение', blank=True, null=True)
    type = models.IntegerField(verbose_name='Тип', choices=SETTINGS_TYPE_CHOICES)
    description = models.CharField(max_length=255, verbose_name='Описание')
    is_required = models.BooleanField(verbose_name='Обязательное', default=True)
    def __unicode__(self):
        return self.description
    class Meta:
        verbose_name = 'Настройки'
        verbose_name_plural = 'Настройки'