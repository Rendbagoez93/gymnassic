"""
Development settings for Gymnassic project.

This module extends base settings with development-specific configurations.
"""

from .base import *  # noqa: F401, F403

# Development-specific settings
DEBUG = True

# Enable Django Debug Toolbar in development (if installed later)
# INSTALLED_APPS += ["debug_toolbar"]  # noqa: F405
# MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]  # noqa: F405

# Allow all hosts in development
INTERNAL_IPS = [
    "127.0.0.1",
    "localhost",
]

# Email backend for development (console)
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Logging configuration for development
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "DEBUG",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
