# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse_lazy

ADMIN_MENU = [
    {
        'id': 'OFFERS',
        'title': 'Акции',
        'url':reverse_lazy('administration_offers_index'),
    },
    {
        'id': 'CATEGORIES',
        'title': 'Категории',
        'url':reverse_lazy('administration_categories_index')
    },
    {
        'id': 'PARTNERS',
        'title': 'Партнеры',
        'url':reverse_lazy('administration_partners_index')
    },
    {
        'id': 'AUCTIONS',
        'title': 'Аукционы',
        'url':reverse_lazy('administration_auctions_index')
    },
    {
        'id': 'PAGES',
        'title': 'Страницы',
        'url':reverse_lazy('administration_pages_index')
    },
    {
        'id': 'ADVERTISING',
        'title': 'Реклама',
        'url':reverse_lazy('administration_advertising_index')
    },
    {
        'id': 'NEWSLETTERS',
        'title': 'Рассылка',
        'url':reverse_lazy('administration_emails_index')
    },
    {
        'id': 'BUSINESS_IDEAS',
        'title': 'Бизнес-идеи',
        'url':reverse_lazy('administration_ideas')
    },
    {
        'id': 'REPORTS',
        'title': 'Отчетность',
        'url':reverse_lazy('administration_reports_index')
    },
    {
        'id': 'SETTINGS',
        'title': 'Настройки',
        'url':reverse_lazy('administration_settings')
    },
    ]
ADMIN_MENU2 = [
    {
        'id': 'MODERATION',
        'title': 'Модерация',
        'url':reverse_lazy('administration_moderator')
    },
    {
        'id': 'ADMINISTRATORS',
        'title': 'Администраторы',
        'url':reverse_lazy('administration_users_administrators')
    },
    {
        'id': 'USERS',
        'title': 'Пользователи',
        'url':reverse_lazy('administration_users')
    },
    {
        'id': 'CLUB_CARD_TEMPLATES',
        'title': 'Шаблоны номеров клубных карт',
        'url':reverse_lazy('administration_club_card_numbers_index')
    },
    {
        'id': 'MODEL_CHANGELOG',
        'title': 'Журнал изменений',
        'url':reverse_lazy('administration_model_changelog')
    },
    ]
ADMIN_MENU3 = [
]
OPERATOR_MENU = [
    {
        'id': 'OFFERS',
        'title': 'Акции',
        'url':reverse_lazy('administration_offers_index'),
    },
    {
        'id': 'PARTNERS',
        'title': 'Партнеры',
        'url':reverse_lazy('administration_partners_index')
    },
    {
        'id': 'PAGES',
        'title': 'Страницы',
        'url':reverse_lazy('administration_pages_index')
    },
    {
        'id': 'AUCTIONS',
        'title': 'Аукционы',
        'url':reverse_lazy('administration_auctions_index')
    },
    {
        'id': 'NEWSLETTERS',
        'title': 'Рассылка',
        'url':reverse_lazy('administration_emails_index')
    },
    {
        'id': 'MODERATION',
        'title': 'Модерация',
        'url':reverse_lazy('administration_moderator')
    },
    {
        'id': 'BUSINESS_IDEAS',
        'title': 'Бизнес-идеи',
        'url':reverse_lazy('administration_ideas')
    },
]

def load_menu_context(context, request=None, show_secondary_menu=True):
    if request is not None and request.user.is_superuser:
        context['ADMIN_MENU'] = ADMIN_MENU
        if show_secondary_menu:
            context['ADMIN_MENU2'] = ADMIN_MENU2
    else:
        context['ADMIN_MENU'] = OPERATOR_MENU
    return context