"""
Local development settings.

This module imports all base settings and can override them for local development.
"""

from .base import *  # noqa: F403, F401

# Override for local development
DEBUG = True

# Additional local development settings can be added here
