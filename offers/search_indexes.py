from haystack import indexes
from offers.models import Offers

class PostIndex(indexes.RealTimeSearchIndex, indexes.Indexable):
    text = indexes.EdgeNgramField(document=True, use_template=True)
    categories = indexes.MultiValueField()
    coupon_price_money = indexes.IntegerField()
    partner = indexes.IntegerField()
    discount = indexes.IntegerField()
    metro = indexes.MultiValueField()
    def prepare_coupon_price_money(self, obj):
        return obj.coupon_price_money
    def prepare_partner(self, obj):
        return obj.partner.pk
    def prepare_discount(self, obj):
        discount = obj.get_discount_percent()
        if discount < 50:
            return 1
        elif discount < 60:
            return 2
        elif discount < 70:
            return 3
        elif discount < 90:
            return 4
        else:
            return 5
    def prepare_categories(self, obj):
        return [category.pk for category in obj.categories.all()]
    def prepare_metro(self, obj):
        result = []
        for address in obj.addresses.all():
            if address.metro:
                result.append(address.metro.pk)
        return result
    def get_model(self):
        return Offers

    def index_queryset(self):
        """Used when the entire index for model is updated."""
        return Offers.objects.all()