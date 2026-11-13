# -*- coding: utf-8 -*-
from django import forms
from common.models import Categories, Photo
from django.forms.models import modelformset_factory
from django.utils.encoding import force_unicode
from itertools import chain
from django.forms import CheckboxInput
from django.utils.html import conditional_escape, escape
from django.utils.safestring import mark_safe
from sorl.thumbnail import get_thumbnail

class CategoriesCheckboxSelectMultiple(forms.CheckboxSelectMultiple):
    def render(self, name, value, attrs=None, choices=()):
        if value is None: value = []
        has_id = attrs and 'id' in attrs
        final_attrs = self.build_attrs(attrs, name=name)
        output = [u'<div class="check-holder"><div class="check-row">']
        # Normalize to strings
        str_values = set([force_unicode(v) for v in value])
        for i, (option_value, option_label) in enumerate(chain(self.choices, choices)):
            # If an ID attribute was given, add a numeric index as a suffix,
            # so that the checkboxes don't all have the same ID attribute.
            if has_id:
                final_attrs = dict(final_attrs, id='%s_%s' % (attrs['id'], i))
                label_for = u' for="%s"' % final_attrs['id']
            else:
                label_for = ''

            cb = CheckboxInput(final_attrs, check_test=lambda value: value in str_values)
            option_value = force_unicode(option_value)
            rendered_cb = cb.render(name, option_value)
            option_label = conditional_escape(force_unicode(option_label))
            output.append(u'<label%s>%s<span class="label-text">%s</span></label>' % (label_for, rendered_cb, option_label))
        output.append(u'</div></div>')
        return mark_safe(u'\n'.join(output))

class PhotosWidget(forms.ClearableFileInput):
    template_with_initial = u"""Сейчас: <img src="%(initial)s" width="215" height="147" alt="">
%(input)s"""
    #u'%(initial_text)s: %(initial)s %(clear_template)s<br />%(input_text)s: %(input)s'
    def render(self, name, value, attrs=None):
        substitutions = {
            'initial_text': self.initial_text,
            'input_text': self.input_text,
            'clear_template': '',
            'clear_checkbox_label': self.clear_checkbox_label,
            }
        template = u"""%(input)s"""
        substitutions['input'] = super(forms.ClearableFileInput, self).render(name, value, attrs)

        if value and hasattr(value, "url"):
            template = self.template_with_initial
            thumbnail = get_thumbnail(value, '215x147', crop='center')
            substitutions['initial'] = (thumbnail.url)
            if not self.is_required:
                checkbox_name = self.clear_checkbox_name(name)
                checkbox_id = self.clear_checkbox_id(checkbox_name)
                substitutions['clear_checkbox_name'] = conditional_escape(checkbox_name)
                substitutions['clear_checkbox_id'] = conditional_escape(checkbox_id)
                substitutions['clear'] = CheckboxInput().render(checkbox_name, False, attrs={'id': checkbox_id})
                substitutions['clear_template'] = self.template_with_clear % substitutions

        return mark_safe(template % substitutions)


class CategoriesForm(forms.ModelForm):
    def clean_title(self):
        title = self.cleaned_data.get('title')
        if title != self.instance.title:
            if title:
                try:
                    Categories.all_objects.get(title=title)
                    raise forms.ValidationError('Категория с таким названием уже существует')
                except Categories.DoesNotExist:
                    pass
        return title
    class Meta:
        model = Categories
        widgets = {
            'title': forms.TextInput(attrs={'class':'text'}),
            'description': forms.Textarea(attrs={'class':'textarea','cols':30,'rows':10})
        }

class PhotoForm(forms.ModelForm):
    class Meta:
        model = Photo
        widgets  = {
            'photo': PhotosWidget(),
        }

PhotoFormFactory = modelformset_factory(Photo, extra=3, form=PhotoForm)