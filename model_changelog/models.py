# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from threadlocals_user.utils import get_current_user
from auctions.models import Auction
from offers.models import Offers
from partners.models import Partner, PartnerAddress
from dbsettings.models import Settings
from model_changelog.signals import important_model_change

# Create your models here.
TYPE_CHOICES = (
    ('create','Создано'),
    ('update','Обновлено'),
    ('delete','Удалено'),
)
class LogMessage(models.Model):
    user = models.ForeignKey(User, blank=True, null=True)
    content_type = models.ForeignKey(ContentType)
    content_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey("content_type", "content_id")
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    additional_info = models.TextField(blank=True, null=True, verbose_name='Дополнительная информация')
    add_date = models.DateTimeField(auto_now_add=True, editable=False)
    def get_user_display(self):
        if self.user:
            if self.user.first_name and self.user.last_name:
                return self.user.first_name+' '+self.user.last_name
            else:
                return self.user.username
        else:
            return 'Система'
    def get_content_type_display(self):
        return self.content_object._meta.verbose_name.title()
    def get_content_title(self):
        return str(self.content_object)
    class Meta:
        ordering = ('-add_date',)


LOGGED_MODELS = (
    Auction,
    Offers,
    Partner,
    PartnerAddress,
    Settings,
)

@receiver(important_model_change)
def log_existing_model_changes(sender, created, **kwargs):
    if type(sender) in LOGGED_MODELS:
        log_message = LogMessage()
        log_message.content_object = sender
        if created:
            log_message.type = 'create'
        else:
            log_message.type = 'update'
        user = get_current_user()
        if user and user.is_authenticated():
            log_message.user = user
        log_message.save()