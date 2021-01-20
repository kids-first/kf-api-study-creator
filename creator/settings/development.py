"""
Django settings for creator project.

Generated by 'django-admin startproject' using Django 2.1.7.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.1/ref/settings/
"""

import os

from creator.settings.features import *

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "q$ol+cu=#pp=bgni6d7rn$+$07(!q8g_=aep0w_n+rkhy5q060"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Adds development endpoints to the application.
# This should never be enabled in actual deployments
DEVELOPMENT_ENDPOINTS = os.environ.get("DEVELOPMENT_ENDPOINTS", False)

STAGE = "dev"

ALLOWED_HOSTS = ["*"]
CORS_ORIGIN_ALLOW_ALL = True

DEVELOP = True

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "graphene_django",
    "django_s3_storage",
    "django_rq",
    "creator.analyses",
    "creator.dev",
    "creator.files",
    "creator.status",
    "creator.studies",
    "creator.users",
    "creator.projects",
    "creator.buckets",
    "creator.email",
    "creator.referral_tokens",
    "creator.extract_configs",
    "creator.jobs",
    "creator.releases",
    "creator.events.apps.EventsConfig",
    "creator",
    "corsheaders",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "creator.middleware.Auth0AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "creator.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]

WSGI_APPLICATION = "creator.wsgi.application"

GRAPHENE = {"SCHEMA": "creator.schema.schema"}


# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("PG_NAME", "postgres"),
        "USER": os.environ.get("PG_USER", "postgres"),
        "PASSWORD": os.environ.get("PG_PASS", "postgres"),
        "HOST": os.environ.get("PG_HOST", "127.0.0.1"),
        "PORT": os.environ.get("PG_PORT", "5432"),
    }
}


CACHES = {
    "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}
}

# Redis for RQ
redis_host = os.environ.get("REDIS_HOST", "localhost")
redis_port = os.environ.get("REDIS_PORT", 6379)
redis_pass = os.environ.get("REDIS_PASS", False)
redis_ssl = os.environ.get("REDIS_SSL", "False") == "True"
RQ_DEFAULT_TTL = int(os.environ.get("RQ_DEFAULT_TTL", "60"))
RQ_QUEUES = {
    "default": {
        "HOST": redis_host,
        "PORT": redis_port,
        "DB": 0,
        "DEFAULT_TIMEOUT": 30,
        "SSL": redis_ssl,
    },
    "cavatica": {
        "HOST": redis_host,
        "PORT": redis_port,
        "DB": 0,
        "DEFAULT_TIMEOUT": 30,
        "SSL": redis_ssl,
    },
    "dataservice": {
        "HOST": redis_host,
        "PORT": redis_port,
        "DB": 0,
        "DEFAULT_TIMEOUT": 30,
        "SSL": redis_ssl,
    },
    "releases": {
        "HOST": redis_host,
        "PORT": redis_port,
        "DB": 0,
        "DEFAULT_TIMEOUT": 30,
        "SSL": redis_ssl,
    },
    "aws": {
        "HOST": redis_host,
        "PORT": redis_port,
        "DB": 0,
        "DEFAULT_TIMEOUT": 30,
        "SSL": redis_ssl,
    },
    "slack": {
        "HOST": redis_host,
        "PORT": redis_port,
        "DB": 0,
        "DEFAULT_TIMEOUT": 30,
        "SSL": redis_ssl,
    },
}
if redis_pass:
    RQ_QUEUES["default"]["PASSWORD"] = redis_pass
    RQ_QUEUES["cavatica"]["PASSWORD"] = redis_pass

# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"
    },
]

AUTH_USER_MODEL = "creator.User"

# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Logging Configuration
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "worker": {
            "format": "[{asctime}] {levelname} {module}: {message}",
            "datefmt": "%H:%M:%S",
            "style": "{",
        }
    },
    "handlers": {
        "command": {
            "level": "INFO",
            "class": "rq.utils.ColorizingStreamHandler",
            "formatter": "worker",
        },
        "rq_console": {
            "level": "ERROR",
            "class": "rq.utils.ColorizingStreamHandler",
            "formatter": "worker",
        },
        "task": {
            "level": "INFO",
            "class": "rq.utils.ColorizingStreamHandler",
            "formatter": "worker",
        },
    },
    "loggers": {
        "TaskLogger": {},
        "creator.management": {"handlers": ["command"], "level": "INFO"},
        "rq.worker": {"handlers": ["rq_console"], "level": "ERROR"},
        "creator.tasks": {"handlers": ["task"], "level": "INFO"},
        "creator.slack": {"handlers": ["task"], "level": "INFO"},
        "creator.studies.dataservice": {"handlers": ["task"], "level": "INFO"},
        "creator.studies.buckets": {"handlers": ["task"], "level": "INFO"},
        "creator.studies.schema": {"handlers": ["task"], "level": "INFO"},
    },
}

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "static")


## Email
EMAIL_BACKEND = os.environ.get(
    "EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend"
)
EMAIL_HOST = os.environ.get("EMAIL_HOST")
EMAIL_PORT = os.environ.get("EMAIL_PORT")
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS")
EMAIL_USE_SSL = os.environ.get("EMAIL_USE_SSL", False)
DEFAULT_FROM_EMAIL = os.environ.get(
    "DEFAULT_FROM_EMAIL", "admin@kidsfirstdrc.org"
)


# Sets the file storage backend
# Supports file system storage and s3 storage
DEFAULT_FILE_STORAGE = os.environ.get(
    "DEFAULT_FILE_STORAGE", "django.core.files.storage.FileSystemStorage"
)
FILE_MAX_SIZE = 2 ** 29

# Maximum time in s allowed before a token may no longer be used to download
DOWNLOAD_TOKEN_TTL = 30

# The relative path directory to upload files to when using file system storage
# The object prefix to upload under when using S3 storage
UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "uploads/")

# Bucket in s3 to keep logs at
LOG_BUCKET = os.environ.get("LOG_BUCKET", "kf-study-creator-logging")
# The relative path to the directory where job logs will be stored
LOG_DIR = os.environ.get("LOG_DIR", "logs/")

AWS_S3_BUCKET_NAME = "kf-study-us-east-1-dev-sd-me0owme0w"

# Auth0 settings
AUTH0_DOMAIN = os.environ.get("AUTH0_DOMAIN", "https://kids-first.auth0.com")
AUTH0_JWKS = os.environ.get(
    "AUTH0_JWKS", "https://kids-first.auth0.com/.well-known/jwks.json"
)
AUTH0_AUD = os.environ.get(
    "AUTH0_AUD", "https://kf-study-creator.kidsfirstdrc.org"
)
# Service auth credentials
AUTH0_SERVICE_AUD = os.environ.get(
    "AUTH0_SERIVCE_AUD", "https://kf-study-creator.kidsfirstdrc.org"
)
AUTH0_CLIENT = os.environ.get("AUTH0_CLIENT")
AUTH0_SECRET = os.environ.get("AUTH0_SECRET")

CACHE_AUTH0_KEY = os.environ.get("CACHE_AUTH0_KEY", "AUTH0_PUBLIC_KEY")
CACHE_AUTH0_SERVICE_KEY = os.environ.get(
    "CACHE_AUTH0_SERVICE_KEY", "AUTH0_SERVICE_KEY"
)
CACHE_AUTH0_TIMEOUT = os.environ.get("CACHE_AUTH0_TIMEOUT", 86400)

CLIENT_ADMIN_SCOPE = "role:admin"

# User roles and groups overrides applied during auth
USER_ROLES = os.environ.get("USER_ROLES", "")
USER_ROLES = None if USER_ROLES == "" else USER_ROLES.split(",")
USER_GROUPS = os.environ.get("USER_GROUPS", "")
USER_GROUPS = None if USER_GROUPS == "" else USER_GROUPS.split(",")

# Number of seconds after which to timeout any outgoing requests
REQUESTS_TIMEOUT = os.environ.get("REQUESTS_TIMEOUT", 30)
REQUESTS_HEADERS = {"User-Agent": "StudyCreator/development (python-requests)"}
