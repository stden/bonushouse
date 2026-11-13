# -*- coding: utf-8 -*-

def get_abonements_order_num(order_date):
    """Возвращает порядковый номер заказа за заданный день. (Используется при подстановке в номер договора'"""
    from auctions.models import Auction
    from offers.models import AbonementOrder
    #Ищем заказы
    result = AbonementOrder.objects.filter(is_completed=True, add_date__day=order_date.day, add_date__month=order_date.month, add_date__year=order_date.year).count()
    #Учитываем продажи через аукцион
    result += Auction.objects.filter(is_completed=True, type=2, completed_date__day=order_date.day, completed_date__month=order_date.month, completed_date__year=order_date.year).count()
    result += 1
    return result

def get_additional_services_order_num(order_date):
    """Возвращает порядковый номер заказа на абонемент за заданный день."""
    from offers.models import AdditionalServicesOrder
    from auctions.models import Auction
    #Ищем заказы
    result = AdditionalServicesOrder.objects.filter(is_completed=True, add_date__day=order_date.day, add_date__month=order_date.month, add_date__year=order_date.year).exclude(agreement_id=None).count()
    #Учитываем продажи через аукцион
    result += Auction.objects.filter(is_completed=True, type=3, completed_date__day=order_date.day, completed_date__month=order_date.month, completed_date__year=order_date.year).count()
    print result
    print order_date
    result += 1
    return result