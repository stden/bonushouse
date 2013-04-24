# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.utils.timezone import now

# Create your models here.
class DummyPaymentInfo(models.Model):
    add_date = models.DateTimeField(verbose_name='Дата добавления', editable=False, auto_now_add=True)

class DolPaymentInfo(models.Model):
    amount = models.CharField(max_length=255)
    userid = models.CharField(max_length=255)
    paymentid = models.CharField(max_length=255)
    key = models.CharField(max_length=255)
    paymode = models.CharField(max_length=255)
    status = models.CharField(max_length=255, blank=True, null=True)
    comment = models.CharField(max_length=255, blank=True, null=True)
    add_date = models.DateTimeField(auto_now_add=True)

class PaymentRequest(models.Model):
    amount = models.PositiveIntegerField(verbose_name='Сумма')
    comment = models.TextField(verbose_name='Комментрарий', blank=True, null=True)
    inner_transaction_type = models.ForeignKey(ContentType, editable=False, blank=True, null=True, related_name='payment_request_type')
    inner_transaction_id = models.PositiveIntegerField(editable=False, blank=True, null=True)
    inner_transaction = generic.GenericForeignKey("inner_transaction_type", "inner_transaction_id")
    is_completed = models.BooleanField(verbose_name='Оплата завершена', default=False)
    payment_type = models.ForeignKey(ContentType, editable=False, blank=True, null=True)
    payment_id = models.PositiveIntegerField(editable=False, blank=True, null=True)
    payment_object = generic.GenericForeignKey("payment_type", "payment_id")
    payment_date = models.DateTimeField(verbose_name='Дата оплаты', blank=True, null=True)
    add_date = models.DateTimeField(verbose_name='Дата добавления', editable=False, auto_now_add=True)

    def complete(self, payment_info):
        self.payment_object = payment_info
        self.is_completed = True
        self.payment_date = now()
        self.save()