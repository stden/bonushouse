
from django.conf.urls import patterns, include, url
from contracts.views import prolongate_contract, person_restruct_contract, club_restruct_contract, calculate_dates

# Uncomment the next two lines to enable the admin:

urlpatterns = patterns('',
    url(r'^prolongate/$',  prolongate_contract, name='prolongate_contract'),
    url(r'^person_restruct/$',  person_restruct_contract, name='person_restruct_contract'),
    url(r'^club_restruct/$', club_restruct_contract, name='club_restruct_contract'),
    url(r'^prolongate/calculate/$', calculate_dates, name='prolongate_calculate_dates'),
    )