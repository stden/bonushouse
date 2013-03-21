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

    def add_item(self, new_item, quantity=1, force_new_item=False, additional_info=None, is_gift=False):
        contents = self.get_contents()
        added = False
        if not force_new_item:
            for item in contents:
                if item['item'] == new_item:
                    item['quantity'] += quantity
                    added = True
                    break
        if not added:
            id = self.get_new_id()
            contents.append({'item': new_item, 'quantity': quantity, 'id': id, 'additional_info':additional_info, 'is_gift':is_gift})
        self.request.session['shopping_cart'] = contents
        return id

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