"""
Base Django settings for Gymnassic project.

This module contains core settings shared across all environments.
Environment-specific settings are loaded from local.py or production.py.

Settings are coordinated through the factory module which provides:
- Environment settings (env_settings)
- Database settings (via DATABASES)
- Gym configuration (gym_config)
"""

from pathlib import Path

from .databases import DATABASES
from .factory import get_gym_settings, get_settings

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load environment-specific settings
env_settings = get_settings()

# Load gym configuration (if available)
try:
    GYM_CONFIG = get_gym_settings()
except Exception:
    GYM_CONFIG = None

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env_settings.secret_key

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env_settings.debug

ALLOWED_HOSTS = env_settings.get_allowed_hosts_list()


# Application definition

# Django and third-party apps
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "django_extensions",
    "django_filters",
]

# Modular components (modules.*)
MODULES_APPS = [
    "modules.user",
]

# Business applications (applications.*)
MAIN_APPS = [
    "applications.gym_setup",
    "applications.user_management",
    "applications.membership",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + MODULES_APPS + MAIN_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases
# Database configuration is loaded from databases.py module


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
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = env_settings.language_code

TIME_ZONE = env_settings.timezone

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Media files (User-uploaded content)
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# Default primary key field type
# https://docs.djangoproject.com/en/6.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
