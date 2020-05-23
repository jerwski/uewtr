"""
Django settings for uniwork project.

Generated by 'django-admin startproject' using Django 2.1.7.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.1/ref/settings/
"""
# standard library
import json
import socket
from pathlib import Path

# django core
from django.contrib import admin
from pytz import country_timezones
from django.core.exceptions import ImproperlyConfigured


# read enviroment settings
def get_setting(setting):
    try:
        with Path('mysetting.json').open('r') as file:
            data = json.loads(file.read())
        return data[setting]
    except KeyError:
        error_msg = f'{setting} - set as an environment variable'
        raise ImproperlyConfigured(error_msg)

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = get_setting('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
if socket.gethostname() in get_setting('home_hosts'):
    DEBUG = True
elif socket.gethostname() in get_setting('office_hosts'):
    DEBUG = True
else:
    DEBUG = False

ALLOWED_HOSTS = ['127.0.0.1', 'localhost']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'account.apps.AccountConfig',
    'employee.apps.EmployeeConfig',
    'evidence.apps.EvidenceConfig',
    'accountancy.apps.AccountancyConfig',
    'cashregister.apps.CashregisterConfig',
    'bootstrap4',
    'tempus_dominus',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.contrib.admindocs.middleware.XViewMiddleware',
]

ROOT_URLCONF = 'uniwork.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
		'DIRS': [BASE_DIR.joinpath('templates')],
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

WSGI_APPLICATION = 'uniwork.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

if socket.gethostname() in get_setting('home_hosts'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': get_setting('NAME'),
            'USER': get_setting('USER_HL'),
            'PASSWORD': get_setting('PASSWORD_HL'),
            'HOST': '127.0.0.1',
            'PORT': '5432',
        }
    }
elif socket.gethostname() in get_setting('office_hosts'):
        DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': get_setting('NAME'),
            'USER': get_setting('USER_OL'),
            'PASSWORD': get_setting('PASSWORD_OL'),
            'HOST': '127.0.0.1',
            'PORT': '5432',
        }
    }
else:
    raise ConnectionError


# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

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


DJANGO_WATCHMAN_TIMEOUT = 1

# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/
LANGUAGE_CODE = get_setting('LANGUAGE_CODE')
TIME_ZONE = country_timezones['PL'][0]
USE_I18N = get_setting('USE_I18N')
USE_L10N = get_setting('USE_L10N')
USE_TZ = get_setting('USE_TZ')

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/
STATIC_URL = get_setting('STATIC_URL')
STATICFILES_DIRS = [Path.joinpath(BASE_DIR, Path(STATIC_URL).name),]
CSS_FILE = [Path.joinpath(BASE_DIR, get_setting('css_style')),]
LOGIN_URL = get_setting('LOGIN_URL')
LOGIN_REDIRECT_URL = 'account:admin_site'
LOGOUT_REDIRECT_URL = 'login'

# e-mail settings
DEFAULT_FROM_EMAIL = get_setting('DEFAULT_FROM_EMAIL')
EMAIL_HOST_USER = get_setting('EMAIL_HOST_USER')
EMAIL_HOST = get_setting('EMAIL_HOST')
EMAIL_HOST_PASSWORD = get_setting('EMAIL_HOST_PASSWORD')
EMAIL_USE_TLS = get_setting('EMAIL_USE_TLS')
EMAIL_PORT = get_setting('EMAIL_PORT')
ADMIN_EMAIL = get_setting('ADMIN_EMAIL')

# archives and invoices paths
ARCH_DIR = Path(get_setting('arch_dir'))
ARCHIVE_ROOT = Path(get_setting('archive_root'))
ARCHIVE_FILE = Path(get_setting('archive_file'))
ARCHIVE_NAME = Path(get_setting('archive_name'))
ROOT_BACKUP = Path(get_setting('root_backup'))
INVOICE_ZIP = Path(get_setting('invoice_zip'))
INVOICE_BACKUP = Path(get_setting('invoice_backup'))
FTP_INVOICE_DIR = Path(get_setting('ftp_invoice_dir'))
FTP_INVOICE_FILE = Path(get_setting('ftp_invoice_file'))
FTP_BACKUP_DIR = get_setting('ftp_backup_dir')
INVOICE_WORKPATH = Path(get_setting('invoice_workpath'))
ACCOUNTANT_MAIL = get_setting('accountant_mail')
CC_MAIL = get_setting('cc_mail')
ADMIN_SERIALIZE = Path(get_setting('admin_serialize'))
TEMP_SERIALIZE = Path(get_setting('temp_serialize'))
BACKUP_ERASE_WORKER = get_setting('backup_erase_worker')
FIXTURES_APPS = get_setting('fixtures_apps')
HOME_HOSTS = get_setting('home_hosts')
OFFICE_HOSTS = get_setting('office_hosts')
SERIALIZE_HOST = get_setting('serialize_host')
GARBAGE_PATTERNS = get_setting('garbage_patterns')

# FTP
FTP = get_setting('FTP')
FTP_DIR = get_setting('FTP_DIR')
FTP_USER = get_setting('FTP_USER')
FTP_LOGIN = get_setting('FTP_LOGIN')
FTP_SERIALIZE = get_setting('FTP_SERIALIZE')

# GitHub
# USER_GITHUB = get_setting('USER_GITHUB')
# PASSWORD_HL = get_setting('PASSWORD_HL')
