import os
import sys
print sys.path
path = '/var/www/disaers/data/www/bonus-house.ru/'
path2 = '/var/www/disaers/data/www/bonus-house.ru/bonushouse/'
if path not in sys.path:
    sys.path.append(path)
if path2 not in sys.path:
    sys.path.append(path2)

os.environ['DJANGO_SETTINGS_MODULE'] = 'bonushouse.settings_production'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
