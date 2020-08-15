import os
import json
from django.core.exceptions import ImproperlyConfigured

# Paths

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
BASE_DIR = os.path.join(PROJECT_DIR, 'finance')

# Secret settings

with open(os.path.join(PROJECT_DIR, 'secrets.json')) as f:
    secrets_json = json.loads(f.read())


def get_secret(setting, secrets=secrets_json):
    try:
        return secrets[setting]
    except KeyError:
        error_msg = 'Set the {} environment variable.'.format(setting)
        raise ImproperlyConfigured(error_msg)


SECRET_KEY = get_secret('SECRET_KEY')

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'background_task',
    'apps.users.apps.UsersConfig',
    'apps.banking.apps.BankingConfig',
    'apps.crypto.apps.CryptoConfig',
    'apps.alternative.apps.AlternativeConfig',
    'apps.stocks.apps.StocksConfig'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.jinja2.Jinja2',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'environment': 'config.jinja2.environment',
            'context_processors': [
                'django.template.context_processors.request',
            ]

        },
    },
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# User

LOGIN_URL = 'users:signin'

LOGIN_REDIRECT_URL = 'users:redirect'

LOGOUT_REDIRECT_URL = 'users:redirect'

AUTH_USER_MODEL = 'users.StandardUser'

# Password validation

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Europe/Berlin'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)

STATIC_URL = '/static/'

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static/app'),
]

STATIC_ROOT = os.path.join(PROJECT_DIR, 'static')

MEDIA_URL = '/media/'

MEDIA_ROOT = os.path.join(PROJECT_DIR, 'media')

STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

# E-Mail

EMAIL_USE_TLS = True
EMAIL_HOST = 'smtp.strato.de'
EMAIL_HOST_USER = 'projekte@tortuga-webdesign.de'
EMAIL_HOST_PASSWORD = get_secret('EMAIL_PWD')
EMAIL_PORT = 587

# Rest Framework

REST_FRAMEWORK = {
    'DATETIME_FORMAT': '%Y-%m-%dT%H:%M',
    'DATETIME_INPUT_FORMATS': ['%Y-%m-%dT%H:%M']
}

# Alphavantage API

ALPHAVANTAGE_API_KEY = 'DCVHUFGLL4SL14LP'

# Marketstack API

MARKETSTACK_API_KEY = '60c5a1022060333009f6ccb37b394622'
