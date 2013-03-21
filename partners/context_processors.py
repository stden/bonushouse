from partners.forms import ForPartnersPageForm

def process_request(request):
    result = {}
    if request.method == 'POST' and request.POST.get('form_id') == 'for_partners_form':
        result['for_partners_form'] = ForPartnersPageForm(request.POST)
        result['for_partners_form'].is_valid()
    else:
        result['for_partners_form'] = ForPartnersPageForm()
    return result