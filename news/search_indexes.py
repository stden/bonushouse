from haystack import indexes
from news.models import News

class PostIndex(indexes.RealTimeSearchIndex, indexes.Indexable):
    text = indexes.EdgeNgramField(document=True, use_template=True)
    def get_model(self):
        return News

    def index_queryset(self):
        """Used when the entire index for model is updated."""
        return News.objects.all()