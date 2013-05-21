from django.conf import settings
def print_data(backend, details, response, user, is_new=False, *args,
                        **kwargs):
    log = open(settings.rel('log_social.txt'))
    log.write('response   ' + response)
    log.write(details)
    log.write(user)
    log.close()

