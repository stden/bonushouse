from django import forms
from advertising.models import Banner

class BannerForm(forms.ModelForm):
    class Meta:
        model = Banner
        widgets = {
            'title': forms.TextInput(attrs={'class':'text'}),
            'url': forms.TextInput(attrs={'class':'text'}),
            'show_start_date': forms.TextInput(attrs={'class':'text datepicker'}),
            'show_end_date': forms.TextInput(attrs={'class':'text datepicker'}),
            'show_max_count': forms.TextInput(attrs={'class':'text'}),
            'click_max_count': forms.TextInput(attrs={'class':'text'}),
        }