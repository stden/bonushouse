from django import forms
from dbsettings.models import Settings
from django.forms.util import flatatt, ErrorDict, ErrorList
from django.utils.datastructures import SortedDict
from model_changelog.signals import important_model_change
from django.core.files.uploadedfile import UploadedFile
import os
from django.conf import settings
from django.core.files.storage import default_storage

class SettingsForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(SettingsForm, self).__init__(*args, **kwargs)
        settings_list = Settings.objects.all()
        for setting in settings_list:
            is_required = setting.is_required
            help_text = setting.get_type_display()
            if setting.type == 1:
                self.fields[setting.key] = forms.IntegerField(required=is_required, label=setting.description, initial=setting.value, widget=forms.TextInput(attrs={'class':'text'}), help_text=help_text)
            if setting.type == 4:
                self.fields[setting.key] = forms.FloatField(required=is_required, label=setting.description, initial=setting.value, widget=forms.TextInput(attrs={'class':'text'}), help_text=help_text)
            elif setting.type == 2:
                self.fields[setting.key] = forms.CharField(required=is_required, widget=forms.TextInput(attrs={'class':'text'}), label=setting.description, initial=setting.value, help_text=help_text)
            elif setting.type == 3:
                self.fields[setting.key] = forms.CharField(required=is_required, widget=forms.Textarea(attrs={'class':'textarea'}), label=setting.description, initial=setting.value, help_text=help_text)
            elif setting.type == 5:
                self.fields[setting.key] = forms.EmailField(required=is_required, widget=forms.TextInput(attrs={'class':'text'}), label=setting.description, initial=setting.value, help_text=help_text)
            elif setting.type == 6:
                self.fields[setting.key] = forms.CharField(required=is_required, widget=forms.Textarea(attrs={'class':'textarea'}), label=setting.description, initial=setting.value, help_text=help_text)
            elif setting.type == 10:
                if setting.value:
                    initial = setting.value
                else:
                    initial = None
                self.fields[setting.key] = forms.FileField(required=is_required, label=setting.description, initial=initial, help_text=help_text)

    def save(self):
        settings_list = Settings.objects.all()
        for setting in settings_list:
            if unicode(setting.value) != unicode(self.cleaned_data.get(setting.key)) or isinstance(self.cleaned_data.get(setting.key), UploadedFile):
                if isinstance(self.cleaned_data.get(setting.key), UploadedFile):
                    new_value = self.cleaned_data.get(setting.key)
                    file_path = default_storage.save(settings.MEDIA_ROOT+'misc/'+new_value._get_name(), new_value)
                    setting.value = os.path.basename(file_path)
                    setting.save()
                else:
                    setting.value = self.cleaned_data.get(setting.key)
                    setting.save()
                is_new = False
                important_model_change.send(sender=setting, created=is_new)