# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

# Create your models here.
class Likes(models.Model):
    user = models.ForeignKey(User)
    content_type = models.ForeignKey(ContentType, editable=False)
    content_id = models.PositiveIntegerField(editable=False)
    content_object = generic.GenericForeignKey("content_type", "content_id")
    add_date = models.DateTimeField(auto_now_add=True, editable=False)