# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse_lazy

ADMIN_MENU = [
    {
        'title': 'Акции',
        'url':reverse_lazy('partner_menu_offers_index')
    },
    {
        'title': 'Модерация',
        'url':reverse_lazy('partner_menu_moderator')
    },
    {
        'title': 'Проверка пин-кодов',
        'url':reverse_lazy('partner_menu_pin_codes')
    },
    {
        'title': 'Отчеты',
        'url':reverse_lazy('partner_menu_reports')
    },
    ]


def load_menu_context(context):
    context['ADMIN_MENU'] = ADMIN_MENU
    return context