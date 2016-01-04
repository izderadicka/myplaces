# Django settings for mapy project.

import os
curr_dir=os.path.split(__file__)[0]

DEBUG = True
TEMPLATE_DEBUG = DEBUG
INTERNAL_IPS= ('127.0.0.1',)
ADMINS = (
     ('Ivan', 'admin@my-places.eu'),
)

#Port for socketio server
SIO_PORT=8008

def get_env(default, *args):
    for name in args:
        if os.environ.get(name):
            return os.environ[name]
    return default
    

if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST='localhost'
    EMAIL_PORT=25

DEFAULT_FROM_EMAIL = 'registration@my-places.eu'

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': get_env('maps', 'DB_MAPS_NAME', 'PGDATABASE'),                      # Or path to database file if using sqlite3.
        'USER': get_env('maps', 'DB_MAPS_USER', 'OPENSHIFT_POSTGRESQL_DB_USERNAME'),                      # Not used with sqlite3.
        'PASSWORD': get_env('maps', 'DB_MAPS_PASSWORD', 'OPENSHIFT_POSTGRESQL_DB_PASSWORD'),                  # Not used with sqlite3.
        'HOST': get_env('127.0.0.1', 'DB_PORT_5432_TCP_ADDR', 'OPENSHIFT_POSTGRESQL_DB_HOST'),                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT':  get_env('', 'DB_PORT_5432_TCP_PORT', 'OPENSHIFT_POSTGRESQL_DB_PORT'),                     # Set to empty string for default. Not used with sqlite3.
        
    }
}

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/{{ docs_version }}/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ['*']

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/Prague'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
if 'OPENSHIFT_REPO_DIR' in os.environ:
    STATIC_ROOT=os.path.join(curr_dir, 'wsgi', 'static')
else:
    STATIC_ROOT = '/var/www/static'

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# URL prefix for admin static files -- CSS, JavaScript and images.
# Make sure to use a trailing slash.
# Examples: "http://foo.com/static/admin/", "/static/admin/".
ADMIN_MEDIA_PREFIX = '/static/admin/'

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
SECRET_KEY = 'n1q@fvz7@s82@qs4x#_2hbf&@5(jao5-o1g0er&!@a@)5)a@_f'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django_mobile.loader.Loader',
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

TEMPLATE_CONTEXT_PROCESSORS=("django.contrib.auth.context_processors.auth",
"django.core.context_processors.debug",
"django.core.context_processors.i18n",
"django.core.context_processors.media",
"django.core.context_processors.static",
"django.core.context_processors.tz",
"django.contrib.messages.context_processors.messages",
'django_mobile.context_processors.flavour',
 'django.core.context_processors.request',
 )



MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'lockout.middleware.LockoutMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django_mobile.middleware.MobileDetectionMiddleware',
    'django_mobile.middleware.SetFlavourMiddleware',
    #'debug_toolbar.middleware.DebugToolbarMiddleware',  # remove if not using debug_toolbar
)

ROOT_URLCONF = 'urls'

LOGIN_REDIRECT_URL= '/mp/'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

INSTALLED_APPS = (
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
    'django.contrib.gis',
    'myplaces',
    'tagging',
#    'debug_toolbar', # remove if not using debug_toolbar
    'socketio_app',
    'rest_framework',
    'django_mobile',
    'rest2backbone',
    'registration',
    'captcha'
)

LOGIN_URL='/accounts/login/'
LOGOUT_URL='/accounts/logout/'

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly',
    ),
    'PAGINATE_BY': 20,
    'PAGINATE_BY_PARAM':'page_size',
    
    'DEFAULT_FILTER_BACKENDS': ('rest_framework.filters.DjangoFilterBackend','rest_framework.filters.OrderingFilter')
}

#remote workers
local_ip=get_env('127.0.0.1', '$OPENSHIFT_INTERNAL_IP', '$OPENSHIFT_PYTHON_IP')
REMOTE_ADDR_IMPORT='tcp://%s:19999'%local_ip
REMOTE_ADDR_IMPORT_PROXY='ipc:///tmp/test_workers'
REMOTE_ADDR_IMPORT_BROADCAST='tcp://%s:19998' % local_ip

REMOTE_ADDR_GEOCODE='tcp://%s:20009' % local_ip
REMOTE_ADDR_CALC='tcp://%s:20011' % local_ip


#registration
REGISTRATION_OPEN= True
ACCOUNT_ACTIVATION_DAYS = 7
PASSWORD_MIN_LENGTH = 6
PASSWORD_MAX_LENGTH = 32

CAPTCHA_FLITE_PATH=None#'/usr/bin/flite'

#proxy settings - disable if not behind reverse proxy
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {'simple': {
            'format': '%(levelname)s:%(name)s:%(message)s',
            },
            'with_date': {
                'format': '%(asctime)s:%(levelname)s:%(name)s:%(message)s',
                }
                   },
           
    'filters': {
        'require_debug_false': {
        '()': 'django.utils.log.RequireDebugFalse'
        }
    },
           # A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error.
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'filters': ['require_debug_false'],
        },
         'console':{
            'level':'DEBUG',
            'class':'logging.StreamHandler',
            'formatter': 'simple'
        },
                 
        'file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'with_date',
            'filename': '/tmp/myplaces_log.txt', #'/var/log/myplaces/log.txt',
            'maxBytes': 10485760,
            'backupCount':3,
        },
    },
    'loggers': {
         'django.request': {
             'handlers': ['mail_admins'],
             'level': 'ERROR',
             'propagate': True,
         },
                
#      'django' : {
#                  'handlers':['console',],
#           'level':'WARN',
#           'propagate': False
#                  },

#     'mp':{'handlers':['console',],
#           'level':'WARN',
#           'propagate': True,
#           }
                
    },
    
           
 'root':{'handlers':['file',],
        'level':'WARN',
          
          }  
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'quick-cache'
    }
}
