from django.contrib import admin
from flatpages.models import FlatPage
from django.utils.translation import ugettext_lazy as _
from flatpages.forms import FlatPageForm

class FlatPageAdmin(admin.ModelAdmin):
    form = FlatPageForm
    fieldsets = (
        (None, {'fields': ('title', 'content')}),
        (_('Advanced options'), {'classes': ('collapse',), 'fields': ('template_name',)}),
    )
    list_display = ('title',)
    search_fields = ('title',)

admin.site.register(FlatPage, FlatPageAdmin)
