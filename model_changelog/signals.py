import django.dispatch

important_model_change = django.dispatch.Signal(providing_args=["created"])