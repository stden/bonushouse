from django.conf import settings
def print_data(backend, details, response, user, is_new=False, *args,
                        **kwargs):
    print details
    print response
    print user

