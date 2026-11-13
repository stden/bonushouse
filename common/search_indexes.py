from haystack import indexes
from common.models import Categories

class PostIndex(indexes.RealTimeSearchIndex, indexes.Indexable):
    text = indexes.EdgeNgramField(document=True, use_template=True)
    def get_model(self):
        return Categories

    def index_queryset(self):
        """Used when the entire index for model is updated."""
        return Categories.objects.all()