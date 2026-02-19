"""
Local Development Settings

This module extends base settings with local development-specific configurations.
"""

from .base import *  # noqa: F401, F403
from .factory import get_settings

# Get environment settings
env_settings = get_settings()

# Local development settings
DEBUG = True

# Development-friendly logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}

# Email backend for development (console)
EMAIL_BACKEND = env_settings.email_backend
EMAIL_HOST = env_settings.email_host
EMAIL_PORT = env_settings.email_port
