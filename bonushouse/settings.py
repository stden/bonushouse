# -*- coding: utf-8 -*-
# Django settings for bonushouse project.
import os
import re


def rel(*x):
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), *x)

DEBUG = True
TEMPLATE_DEBUG = DEBUG

OFERTA_PAGE_ID = 4

#Обратный адрес для имейлов по умолчанию
DEFAULT_FROM_EMAIL = 'do-not-reply@bonus-house.ru'

#Строка символов для генерации кодов купонов
COUPON_CODE_CHARS = 'ABCDEFGHIJKLMNPQRSTUVWXYZ123456789'
#Длина генерируемых кодов
COUPON_CODE_LENGTH = 10

#Параметры Деньги.Онлайн
DOL_PROJECT_ID = 2612
DOL_SECRET_KEY = 'dolPWD9965x98'

ADMINS = (
    ('Dan', 'dangusev92@gmail.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'bonushouse',                      # Or path to database file if using sqlite3.
        'USER': 'root',                      # Not used with sqlite3.
        'PASSWORD': '123',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/Moscow'

# Language code for this installation. Allchoices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'ru-ru'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = rel('../media/')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = rel('../static/')

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = '_kwqs1_kcr1x+i_!cea0mj)lynw9*ukjhw*r9brsuny#zopuy9'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    # 'bonushouse.middleware.ExceptionMiddleware', # Нужно для получения трейсов при DEBUG=False
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'threadlocals_user.utils.LocalUserMiddleware',
    'bonushouse.middleware.CheckUserDataMiddleware',
    'visitor_tracking.middleware.VisitorTrackingMiddleware',
    'bonushouse.middleware.CallMeMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'seo.middleware.FriendlyUrlFallbackMiddleware',
    'partners.middleware.ForPartnersPageFormMiddleware',
    'django_sorting.middleware.SortingMiddleware',
    'pagination.middleware.PaginationMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'bonushouse.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'bonushouse.wsgi.application'

TEMPLATE_DIRS = (rel('../templates'),)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'sorl.thumbnail',
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
    'haystack','bonushouse',
    'offers',
    'seo',
    'common',
    'flatpages',
    'news',
    'contact',
    'administration',
    'partners',
    'contracts',
    'rating',
    'newsletter',
    'ckeditor',
    'dbsettings',
    'advertising',
    'visitor_tracking',
    'auctions',
    'social_auth',
    'payment_gateways',
    'south',
    'debug_toolbar',
    'likes',
    'model_changelog',
    'threadlocals_user',
    'django_sorting',
    'pagination',
)
AUTHENTICATION_BACKENDS = (
    'social_auth.backends.twitter.TwitterBackend',
    'social_auth.backends.facebook.FacebookBackend',
    'social_auth.backends.contrib.vkontakte.VKontakteBackend',
    'social_auth.backends.contrib.vkontakte.VKontakteOAuth2Backend',
    'social_auth.backends.contrib.odnoklassniki.OdnoklassnikiBackend',
    'django.contrib.auth.backends.ModelBackend',
)
AUTH_PROFILE_MODULE = 'bonushouse.UserProfile'
TWITTER_CONSUMER_KEY         = '78ShOnu6wchh4JO7LvR9JQ'
TWITTER_CONSUMER_SECRET      = 'V7ZXP6O1rUFY7ZRFZTjD31SMJ6Lq5AhWa6X4X1tdI'
FACEBOOK_APP_ID              = '259131294209220'
FACEBOOK_API_SECRET          = 'c39ec2a802983381584cc4121f21231a'
FACEBOOK_EXTENDED_PERMISSIONS = ['email',]
VK_APP_ID                    = '3180084'
VKONTAKTE_APP_ID             = VK_APP_ID
VK_API_SECRET                = 'V7YYoc5B3yutn0vPwp8M'
VKONTAKTE_APP_SECRET         = VK_API_SECRET
ODNOKLASSNIKI_OAUTH2_CLIENT_KEY = '93481728'
ODNOKLASSNIKI_OAUTH2_APP_KEY = 'CBAMGDJGABABABABA'
ODNOKLASSNIKI_OAUTH2_CLIENT_SECRET = '864280166FD9DBB2D130978B'
LOGIN_URL          = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGIN_ERROR_URL    = '/login-error/'

SOCIAL_AUTH_RAISE_EXCEPTIONS = True
SOCIAL_AUTH_SESSION_EXPIRATION = False
SOCIAL_AUTH_PIPELINE_RESUME_ENTRY = 'social_auth.backends.pipeline.misc.save_status_to_session'
SOCIAL_AUTH_PIPELINE = (
    'social_auth.backends.pipeline.social.social_auth_user',
    #'social_auth.backends.pipeline.associate.associate_by_email',
    'social_auth.backends.pipeline.user.get_username',
    'social_auth.backends.pipeline.misc.save_status_to_session',
    'pipeline.print_data',
    'social_auth.backends.pipeline.user.create_user',
    'social_auth.backends.pipeline.social.associate_user',
    'social_auth.backends.pipeline.social.load_extra_data',
    'social_auth.backends.pipeline.user.update_user_details'
)

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'WARNING',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}
CKEDITOR_UPLOAD_PATH = rel('../media/upload/')
CKEDITOR_CONFIGS = {
    'default' : {
        'skin' : 'kama',
        'width': 700,
        'height': 300,
        'toolbar': 'Full'
    }
}
TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    'django.core.context_processors.request',
    "django.core.context_processors.static",
    "django.core.context_processors.tz",
    "django.contrib.messages.context_processors.messages",
    "visitor_tracking.context_processors.process_request",
    "bonushouse.context_processors.process_request",
    "dbsettings.context_processors.process_request",
    "offers.context_processors.get_last_viewed_offers",
    'partners.context_processors.process_request',
)
HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.whoosh_backend.WhooshEngine',
        'PATH': rel('../search_index.db'),
    },
}
REQEST_LOG_PATH = rel('../requests.log')
HOME_PAGE_ID = 5

#Параметры для отправки уведомлений в базу FH
FITNESSHOUSE_SID_MONEY =120
FITNESSHOUSE_SID_BONUSES =121
ADDITIONAL_SERVICES_SID_MONEY =130
ADDITIONAL_SERVICES_SID_BONUSES =131
FITNESSHOUSE_NOTIFY_URL_DEBUG = 'https://80.247.186.195/'
FITNESSHOUSE_NOTIFY_URL = 'https://80.247.186.193/'
BH_PASSWORD = 'bh37cYT4eic77'
FH_SALT = 'Zm4cBBauXXW9uoSOQsq'
#Django Debug Toolbar
INTERNAL_IPS = ('127.0.0.1',)
#SMSBLISS
SMSBLISS_LOGIN = 'fithouse'
SMSBLISS_PASSWORD = 'fithouse'
SMSBLISS_DEFAULT_SENDER = 'BONUS-HOUSE'
FITNESSHOUSE_AGREEMENT_RE = re.compile('^M[A-Z]?(\d+)/\d{6}\d+$')

BASE_URL = 'http://bonus-house.ru'
ORDER_COMPLETE_SUBJECT = u'Покупка на сайте Бонус Хаус'
CONTRACT_RESTRUCT_SUBJECT = u'Переоформление договора на сайте Бонус Хаус'
FITNESSHOUSE_PARTNER_IDS = (
    3,
)

DEBUG_TOOLBAR_CONFIG = {'INTERCEPT_REDIRECTS': False}