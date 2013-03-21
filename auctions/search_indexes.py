from haystack import indexes
from auctions.models import Auction

class PostIndex(indexes.RealTimeSearchIndex, indexes.Indexable):
    text = indexes.EdgeNgramField(document=True, use_template=True)
    def get_model(self):
        return Auction

    def index_queryset(self):
        """Used when the entire index for model is updated."""
        return Auction.objects.all()