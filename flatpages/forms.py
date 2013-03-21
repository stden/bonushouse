from django import forms
from django.conf import settings
from flatpages.models import FlatPage
from django.utils.translation import ugettext, ugettext_lazy as _

class FlatPageForm(forms.ModelForm):
    class Meta:
        model = FlatPage
        widgets = {
            'title': forms.TextInput(attrs={'class':'text'}),
            'template_name': forms.TextInput(attrs={'class':'text'}),
        }