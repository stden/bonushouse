# -*- coding: utf-8 -*-
from django.contrib import messages

class ShoppingCart(object):

    def __init__(self, request):
        self.request = request

    def get_contents(self):
        cart_contents = self.request.session.get('shopping_cart', [])
        if not len(cart_contents):
            return []
        else:
            return cart_contents

    def clear(self):
        if len(self.get_contents()):
            self.request.session['shopping_cart'] = []

    def add_item(self, request, new_item, quantity=1, force_new_item=False, additional_info=None, is_gift=False):
        """Добавление в корзину. Нельзя отложить или подарить, если купоны закончились"""
        #@TODO: Сделать по-человечески, не Indian-style
        if new_item.quantity >=quantity:
            contents = self.get_contents()
            added = False
            id = None
            total_quantity = 0  # Накопитель одинаковых необъединённых элементов в корзине. Прости меня, Гвидо(
            for item in contents:
                if item['item'] == new_item:
                    total_quantity += item['quantity']
                    if quantity + total_quantity <= new_item.quantity:
                        if not force_new_item:
                            item['quantity'] += quantity
                            added = True
                            break
                    else:
                        if not is_gift:
                            messages.info(request, 'Купоны по этой акции закончились. Их больше нельзя купить.')
                        return None
            if not added:
                id = self.get_new_id()
                contents.append({'item': new_item, 'quantity': quantity, 'id': id, 'additional_info':additional_info, 'is_gift':is_gift})
            self.request.session['shopping_cart'] = contents
            return id
        else:
            if not is_gift:
                messages.info(request, 'Купоны по этой акции закончились. Их больше нельзя купить.')
            return None

    def set_contents(self, contents):
        self.request.session['shopping_cart'] = contents

    def get_item(self, item_id):
        item_id = int(item_id)
        contents = self.get_contents()
        for idx, item in enumerate(contents):
            if item['id'] == item_id:
                return item
        return None

    def remove_item(self, item_id):
        item_id = int(item_id)
        contents = self.get_contents()
        for idx, item in enumerate(contents):
            if item['id'] == item_id:
                del(contents[idx])
        self.request.session['shopping_cart'] = contents

    def get_new_id(self):
        contents = self.get_contents()
        if not len(contents):
            id = 1
        else:
            id = contents[-1]['id']+1
        return id
    def get_total_bonuses(self):
        total = 0
        contents = self.get_contents()
        for item in contents:
            total += item['item'].coupon_price_bonuses * item['quantity']
        return total
    def get_total_money(self):
        total = 0
        contents = self.get_contents()
        for item in contents:
            total += item['item'].coupon_price_money * item['quantity']
        return total
    def is_empty(self):
        contents = self.get_contents()
        if not len(contents):
            return True
        else:
            return False