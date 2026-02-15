"""
Settings package initialization.

Automatically loads the appropriate settings module based on the environment.
"""

import os

from .factory import get_settings

# Determine which settings module to use
env_settings = get_settings()
environment = env_settings.environment

if environment == "production":
    from .production import *  # noqa: F401, F403
else:
    from .development import *  # noqa: F401, F403
