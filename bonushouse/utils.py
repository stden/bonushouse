# -*- coding: utf-8 -*-
from bonushouse.models import AUTO_BONUS_COUNTS
from dbsettings.utils import get_settings_value
import math

def total_seconds(td):
    return (td.microseconds + (td.seconds + td.days * 24.0 * 3600.0) * 10**6) / 10.0**6.0

def get_auto_bonus_count(price):
    """Автоматический расчет количества бонусов на основе цены"""
    bonus_value = float(get_settings_value('BONUS_PRICE'))
    try:
        price = int(price)
    except ValueError:
        price = 0
    for treshold in AUTO_BONUS_COUNTS:
        if price <= treshold[0]:
            result = float(price) * (1.0-treshold[1]) / bonus_value
            result = round(result, 0)
            return math.floor(result)
    result = price * AUTO_BONUS_COUNTS[-1][1] / bonus_value
    return int(result)


def dict_urlencode(dict):
    result = ''
    for key in dict.keys():
        result += '&' + key + '=' + dict[key]
    if len(result):
        result = result[1:]
    return result

def get_object_or_none(model, **kwargs):
    try:
        return model.objects.get(**kwargs)
    except model.DoesNotExist:
        return None