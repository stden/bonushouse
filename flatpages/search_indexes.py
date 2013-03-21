from haystack import indexes
from flatpages.models import FlatPage

class PostIndex(indexes.RealTimeSearchIndex, indexes.Indexable):
    text = indexes.EdgeNgramField(document=True, use_template=True)
    def get_model(self):
        return FlatPage

    def index_queryset(self):
        """Used when the entire index for model is updated."""
        return FlatPage.objects.all()