# -*- coding: utf-8 -*-

from django.db import models
from django.utils.timezone import now
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic



TYPE_CHOICES = ((1, 'Переоформление на другого человека'), (2, 'Переход в другой клуб'), (3, 'Продление договора'))


class ContractTransaction(models.Model):

    user = models.ForeignKey(User)
    amount = models.IntegerField(verbose_name='Сумма')
    operation_type = models.IntegerField(choices=TYPE_CHOICES, verbose_name='Тип операции')
    is_completed = models.BooleanField(verbose_name='Оплата завершена', default=False)
    payment_date = models.DateTimeField(verbose_name='Дата оплаты', blank=True, null=True)
    payment_type = models.ForeignKey(ContentType, editable=False, blank=True, null=True)
    payment_id = models.PositiveIntegerField(editable=False, blank=True, null=True)
    payment_object = generic.GenericForeignKey("payment_type", "payment_id")
    comment = models.TextField(verbose_name='Комментарий', blank=True, null=True)
    add_date = models.DateTimeField(verbose_name='Дата добавления', editable=False, auto_now=True)

    def complete(self, payment_info):
        self.payment_object = payment_info
        self.is_completed = True
        self.payment_date = now()
        self.save()

