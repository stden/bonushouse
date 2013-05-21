from django.conf import settings
def print_data(backend, details, response, user, is_new=False, *args,
                        **kwargs):
    log = open('/var/www/disaers/data/www/bonus-house.ru/log_social.txt', 'w')
    log.write('response  ' + response)
    log.write(details)
    log.write(user)
    log.close()

