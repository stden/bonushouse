from dbsettings.models import Settings
def process_request(requsest):
    result = {}
    settings_list = Settings.objects.all()
    for setting in settings_list:
        result[setting.key] = setting.value
    return result
