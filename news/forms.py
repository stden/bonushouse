from django import forms
from news.models import News

class NewsForm(forms.ModelForm):
    class Meta:
        model = News
        widgets = {
            'title': forms.TextInput(attrs={'class':'text'}),
            'intro_text': forms.Textarea(attrs={'class':'textarea'}),
        }