import os
import sys
from pathlib import Path

from django.utils.csp import CSP

import environ
import sentry_sdk
from botocore.client import Config as BotoConfig
from sentry_sdk.integrations.django import DjangoIntegration

BACKEND_DIR = Path(__file__).resolve().parent.parent
BASE_DIR = BACKEND_DIR.parent

# Environment
env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, ".env"), overwrite=True)


AUTH_USER_MODEL = "users.User"

SECRET_KEY = env("SECRET")
SECURE_SSL_REDIRECT = env("FORCE_HTTPS", cast=bool)
SECURE = env("SECURE", cast=bool)
PROTOCOL = "https" if SECURE else "http"
DEBUG = env("DEBUG", cast=bool)

ALLOWED_HOSTS = [x.strip() for x in env("ALLOWED_HOSTS", cast=list)]

ENVIRONMENT = env("ENVIRONMENT")


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "users",
    "common",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.csp.ContentSecurityPolicyMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "sylvasan.urls"
CSRF_COOKIE_NAME = "csrftoken"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BACKEND_DIR, "common/admin/templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.csp",
            ],
        },
    },
]

WSGI_APPLICATION = "sylvasan.wsgi.application"

ADMIN_URL = os.environ.get("ADMIN_URL", "admin")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "USER": env("DB_USER"),
        "NAME": env("DB_NAME"),
        "PASSWORD": env("DB_PASSWORD"),
        "HOST": env("DB_HOST"),
        "PORT": env("DB_PORT"),
        "CONN_MAX_AGE": 60,
    }
}


# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = "fr-fr"
LANGUAGES = (("fr", "Français"),)
LOCALE_PATHS = [
    os.path.join(BACKEND_DIR, "templates", "locale"),
]

TIME_ZONE = "Europe/Paris"
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BACKEND_DIR, "static/")


default_file_storage = env("DEFAULT_FILE_STORAGE")
STORAGES = {
    "default": {
        "BACKEND": default_file_storage,
    },
    "staticfiles": {
        "BACKEND": env("STATICFILES_STORAGE"),
    },
}
if default_file_storage == "storages.backends.s3.S3Storage":
    AWS_ACCESS_KEY_ID = env("CELLAR_KEY")
    AWS_SECRET_ACCESS_KEY = env("CELLAR_SECRET")
    AWS_S3_ENDPOINT_URL = env("CELLAR_HOST")
    AWS_STORAGE_BUCKET_NAME = env("CELLAR_BUCKET_NAME")
    AWS_LOCATION = "media"
    AWS_QUERYSTRING_AUTH = False
    AWS_S3_CLIENT_CONFIG = BotoConfig(
        request_checksum_calculation="when_required",
        response_checksum_validation="when_required",
    )

MEDIA_ROOT = env("MEDIA_ROOT", default=os.path.join(BACKEND_DIR, "media"))
MEDIA_URL = "/media/"

SESSION_COOKIE_AGE = 31536000
SESSION_COOKIE_SECURE = env("SECURE", cast=bool)
SESSION_COOKIE_HTTPONLY = True

LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"
LOGIN_URL = "/s-identifier"

HOSTNAME = env("HOSTNAME")

# Email
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL")
CONTACT_EMAIL = env("CONTACT_EMAIL")
EMAIL_BACKEND = env("EMAIL_BACKEND")

if DEBUG and EMAIL_BACKEND == "django.core.mail.backends.smtp.EmailBackend":
    EMAIL_HOST = "localhost"
    EMAIL_PORT = 1025

ANYMAIL = {
    "SENDINBLUE_API_KEY": env("BREVO_API_KEY", default=None),
}

# Rest framework

REST_FRAMEWORK = {
    "COERCE_DECIMAL_TO_STRING": False,
    "UPLOADED_FILES_USE_URL": True,
    "DEFAULT_RENDERER_CLASSES": (
        "djangorestframework_camel_case.render.CamelCaseJSONRenderer",
        "djangorestframework_camel_case.render.CamelCaseBrowsableAPIRenderer",
    ),
    "DEFAULT_PARSER_CLASSES": (
        "djangorestframework_camel_case.parser.CamelCaseFormParser",
        "djangorestframework_camel_case.parser.CamelCaseMultiPartParser",
        "djangorestframework_camel_case.parser.CamelCaseJSONParser",
    ),
    "JSON_UNDERSCOREIZE": {
        "no_underscore_before_number": True,
    },
    "DEFAULT_AUTHENTICATION_CLASSES": ("rest_framework.authentication.SessionAuthentication",),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}


# logging

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "stream": sys.stdout,
            "formatter": "verbose",
        },
    },
    "loggers": {
        "": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": True,
        },
    },
}

# Analytics
MATOMO_ID = env("MATOMO_ID", default=None)

# Sentry
SENTRY_DSN = env("SENTRY_DSN", default=None)
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(),
        ],
        traces_sample_rate=1.0,
        send_default_pii=False,
        send_client_reports=False,
    )

# Configuration CSP avec nonces
SECURE_CSP = {
    "default-src": [
        CSP.SELF,
        "*.gouv.fr",
        "*.services.clever-cloud.com",
    ]
    + (["http://127.0.0.1:8080", "http://localhost:8080"] if DEBUG else []),
    "script-src": [
        CSP.SELF,
        CSP.NONCE,
        "*.gouv.fr",
    ]
    + (["http://127.0.0.1:8080", "http://localhost:8080"] if DEBUG else []),
    "style-src": [
        CSP.SELF,
        CSP.NONCE,
    ]
    + (["http://127.0.0.1:8080", "http://localhost:8080"] if DEBUG else []),
    "img-src": [
        CSP.SELF,
        "*.services.clever-cloud.com",
        "data:",
    ]
    + (["http://127.0.0.1:8080", "http://localhost:8080"] if DEBUG else []),
    "connect-src": [
        CSP.SELF,
        "*.gouv.fr",
        "https://api.iconify.design",
        "https://api.unisvg.com",
        "https://api.simplesvg.com",
    ]
    + (["ws:", "http://127.0.0.1:8080", "http://localhost:8080"] if DEBUG else []),
}
