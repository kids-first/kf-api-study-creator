"""
Django settings for creator project.

Generated by 'django-admin startproject' using Django 2.1.7.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.1/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'q$ol+cu=#pp=bgni6d7rn$+$07(!q8g_=aep0w_n+rkhy5q060'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']
CORS_ORIGIN_ALLOW_ALL = True

DEVELOP = True

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'graphene_django',
    'django_s3_storage',
    'creator.files',
    'creator.studies',
    'creator.users',
    'creator.events.apps.EventsConfig',
    'creator',
    'corsheaders'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'creator.middleware.EgoJWTAuthenticationMiddleware',
    'creator.middleware.Auth0AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'creator.urls'

TEMPLATES = [
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

WSGI_APPLICATION = 'creator.wsgi.application'

GRAPHENE = {
    'SCHEMA': 'creator.schema.schema'
}


# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('PG_NAME', 'postgres'),
        'USER': os.environ.get('PG_USER', 'postgres'),
        'PASSWORD': os.environ.get('PG_PASS', 'postgres'),
        'HOST': os.environ.get('PG_HOST', '127.0.0.1'),
        'PORT': os.environ.get('PG_PORT', '5432'),
    }
}


CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}


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

AUTH_USER_MODEL = 'creator.User'

# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, "static")

# Sets the file storage backend
# Supports file system storage and s3 storage
DEFAULT_FILE_STORAGE = os.environ.get('DEFAULT_FILE_STORAGE',
                          'django.core.files.storage.FileSystemStorage')
FILE_MAX_SIZE = 2**29

# Maximum time in s allowed before a token may no longer be used to download
DOWNLOAD_TOKEN_TTL = 30

# The relative path directory to upload files to when using file system storage
# The object prefix to upload under when using S3 storage
UPLOAD_DIR = os.environ.get('UPLOAD_DIR', 'uploads/')

AWS_S3_BUCKET_NAME = 'kf-study-us-east-1-dev-sd-me0owme0w'

# API for Ego
EGO_API = os.environ.get('EGO_API', 'https://ego')
# Cache key for where to rerieve and store the ego signing key
CACHE_EGO_KEY = 'EGO_PUBLIC_KEY'
# How often the Ego public key should be retrieved from ego, 1 day default
CACHE_EGO_TIMEOUT = 86400

# Auth0 settings
AUTH0_API = 'https://kids-first.auth0.com'
AUTH0_JWKS = 'https://kids-first.auth0.com/.well-known/jwks.json'
AUTH0_AUD = 'https://kf-study-creator.kidsfirstdrc.org'
CACHE_AUTH0_KEY = 'AUTH0_PUBLIC_KEY'
CACHE_AUTH0_TIMEOUT = 86400

CLIENT_ADMIN_SCOPE = 'role:admin'
