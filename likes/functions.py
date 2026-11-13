# -*- coding: utf-8 -*-
from likes.models import Likes
from django.contrib.contenttypes.models import ContentType

def toggle_like(content_object, user):
    """Если лайк уже есть, функция удаляет его. Если нет, добавляет. Возвращает на выходе новое количество лайков этого объекта"""
    content_type = ContentType.objects.get_for_model(content_object)
    try:
        like = Likes.objects.get(content_type=content_type, content_id=content_object.pk, user=user)
        like.delete()
    except Likes.DoesNotExist:
        like = Likes(content_object=content_object, user=user)
        like.save()
    return get_likes_count(content_object)

def get_likes_count(content_object):
    content_type = ContentType.objects.get_for_model(content_object)
    return Likes.objects.filter(content_type=content_type, content_id=content_object.pk).count()