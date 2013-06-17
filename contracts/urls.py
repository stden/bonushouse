
from django.conf.urls import patterns, include, url
from contracts.views import prolongate_contract, person_restruct_contract, club_restruct_contract, calculate_dates, back_to_1_step, get_contract_number

# Uncomment the next two lines to enable the admin:

urlpatterns = patterns('',
    url(r'^prolongate/$',  prolongate_contract, name='prolongate_contract'),
    url(r'^person_restruct/$',  person_restruct_contract, name='person_restruct_contract'),
    url(r'^person_restruct/step1/$',  back_to_1_step, name='back_to_1_step'),
    url(r'^club_restruct/$', club_restruct_contract, name='club_restruct_contract'),
    url(r'^prolongate/calculate/$', calculate_dates, name='prolongate_calculate_dates'),
    url(r'^get_number/$', get_contract_number, name='get_contract_number'),

    )