# -*- coding: utf-8 -*-

from django.db import models
from django.utils.timezone import now
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic


TYPE_CHOICES = ((1, 'Переоформление на другого человека'), (2, 'Переход в другой клуб'), (3, 'Продление договора'))


class ContractTransaction(models.Model):

    user = models.ForeignKey(User)
    amount = models.IntegerField(verbose_name='Сумма', default=0)
    operation_type = models.IntegerField(choices=TYPE_CHOICES, verbose_name='Тип операции')
    is_completed = models.BooleanField(verbose_name='Перевод завершён', default=False)
    transaction_date = models.DateTimeField(verbose_name='Дата оплаты', blank=True, null=True)
    transaction_type = models.ForeignKey(ContentType, editable=False, blank=True, null=True)
    transaction_id = models.PositiveIntegerField(editable=False, blank=True, null=True)
    transaction_object = generic.GenericForeignKey("transaction_type", "transaction_id")
    comment = models.TextField(verbose_name='Комментарий', blank=True, null=True)
    add_date = models.DateTimeField(verbose_name='Дата добавления', editable=False, auto_now_add=True)
    complete_date = models.DateTimeField(verbose_name='Дата закрытия транзакции', editable=False, blank=True, null=True)

    def complete(self):
        self.is_completed = True
        self.complete_date = now()
        self.save()


class ContractTransactionInfo(models.Model):
    """Нужен просто для создания связи в generic.GenericForeignKey"""
    add_date = models.DateTimeField(auto_now_add=True)

