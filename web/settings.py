##
# @file web/settings.py
# @brief Django settings file

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)

import version.models
import initlog
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'kw$@=pa)zdjmjx^6z65-+x3c5j+^ydyj1!t!@_q+z2qw06&1*i'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False
TEMPLATE_DEBUG = False

MAX_BOREHOLE_HEIGHT = 5000

#MEASUREMENT_IMAGE_WIDTH_PX = 180
#MEASUREMENT_IMAGE_HEIGHT_PX = 1059
# Big images size
MEASUREMENT_IMAGE_WIDTH_PX = 760
MEASUREMENT_IMAGE_HEIGHT_PX = 4472
MEASUREMENT_IMAGE_HEIGHT_CM = 100
MAX_DUMP_FILES = 10

ALLOWED_HOSTS = ['127.0.0.1', 'localhost']

# Application definition
INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    #    'django.contrib.staticfiles',
    'version',
    'current',
    'gunicorn',
    'boreholes',
    'users',
    'images',
    'measurements',
    'meanings',
    'values',
    'dictionaries',
    'similarities',
    'charts',
    'data',
    'stratigraphy',
    'log',
    'reset',
)

MIDDLEWARE_CLASSES = (
    'views.CustomMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'urls'

WSGI_APPLICATION = 'wsgi.application'


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': version.models.getDBName(),
        'HOST': '127.0.0.1',
        'PORT': '5432',
        'USER': version.models.getDBUser(),
        'PASSWORD': version.models.getDBPassword()
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

# FILE_UPLOAD_HANDLERS = (
#    'django.core.files.uploadhandler.TemporaryFileUploadHandler',
# )

#FILE_UPLOAD_TEMP_DIR = '/data'
