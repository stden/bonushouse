from dbsettings.models import Settings

def get_settings_value(key):
    try:
        setting = Settings.objects.get(key=key)
        result = setting.value
        if setting.type == 6:
            temp = result.split('\n')
            result = []
            for item in temp:
                result.append(item.strip())
        return result
    except Settings.DoesNotExist:
        return None