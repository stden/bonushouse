from offers.cart import ShoppingCart
from offers.models import Offers

def get_last_viewed_offers(request):
    result = {}
    last_viewed_offers = request.session.get('last_viewed_offers', [])
    result['last_viewed_offers'] = []
    for offer in last_viewed_offers:
        try:
            offer = Offers.objects.get(pk=offer.pk)
            if offer.can_buy():
                result['last_viewed_offers'].append(offer)
        except Offers.DoesNotExist:
            pass
    result['shopping_cart'] = ShoppingCart(request)
    return result