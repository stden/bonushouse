# -*- coding: utf-8 -*-
from django import forms
from seo.models import ModelMetaTags, ModelFriendlyUrl
from django.conf import settings
from django.utils.translation import ugettext, ugettext_lazy as _


class SeoModelMetaForm(forms.ModelForm):
    class Meta:
        model = ModelMetaTags
        widgets = {
            'meta_title': forms.TextInput(attrs={'class':'text'}),
            'meta_keywords': forms.TextInput(attrs={'class':'text'}),
            'meta_description': forms.TextInput(attrs={'class':'text'}),
        }

class SeoModelUrlForm(forms.ModelForm):
    def clean_friendly_url(self):
        friendly_url = self.cleaned_data['friendly_url']
        if not friendly_url.startswith('/'):
            raise forms.ValidationError("Вы не указали / в начале пути")
        if (settings.APPEND_SLASH and
            'django.middleware.common.CommonMiddleware' in settings.MIDDLEWARE_CLASSES and
            not friendly_url.endswith('/')):
            raise forms.ValidationError("Вы не указали замыкающий /")
        try:
            db_friendly_url = ModelFriendlyUrl.objects.get(friendly_url=friendly_url)
            if db_friendly_url.content_object is None:
                db_friendly_url.delete()
        except ModelFriendlyUrl.DoesNotExist:
            pass
        return friendly_url
    class Meta:
        model = ModelFriendlyUrl
        widgets = {
            'friendly_url': forms.TextInput(attrs={'class':'text'}),
        }