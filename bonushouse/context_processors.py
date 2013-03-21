from django.conf import settings
from bonushouse.forms import LoginForm, RegisterForm, CallMeForm, ShareLinkForm
from django.utils.timezone import now


def process_request(request):
    result = {}
    result['VK_APP_ID'] = settings.VK_APP_ID
    result['VK_COMPLETE_URL'] = 'http://bonus-house.ru/complete/vkontakte/'
    result['fb_app_id'] = settings.FACEBOOK_APP_ID
    if not request.user.is_authenticated() and request.method != 'POST':
        result['login_form'] = LoginForm()
        result['register_form'] = RegisterForm()
    if request.path == '/oferta/' or request.path.startswith('/accounts/password'):
        result['hide_login_overlay'] = True
    result['DOL_PROJECT_ID'] = settings.DOL_PROJECT_ID
    if request.method == 'POST' and request.POST.get('call_me'):
        call_me_form = CallMeForm(request.POST)
        call_me_form.is_valid()
        result['show_call_me_form'] = True
    else:
        call_me_form = CallMeForm()
    result['call_me_form'] = call_me_form
    result['cur_date'] = now()
    result['BASE_URL'] = settings.BASE_URL
    result['CURRENT_URL'] = request.path

    result['share_link_form'] = ShareLinkForm()
    return result