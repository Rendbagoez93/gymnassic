"""
Database configuration using environment settings.
- SQLite: For Development
- PostgreSQL: For Production
"""

from urllib.parse import urlparse

from .factory import get_settings


def parse_database_url(url: str) -> dict:
    parsed = urlparse(url)

    # Map URL scheme to Django ENGINE - SQLite and PostgreSQL only
    scheme_mapping = {
        "postgresql": "django.db.backends.postgresql",
        "postgres": "django.db.backends.postgresql",
        "sqlite": "django.db.backends.sqlite3",
    }

    engine = scheme_mapping.get(parsed.scheme, "django.db.backends.sqlite3")

    # SQLite configuration (Development)
    if parsed.scheme in ("sqlite", "sqlite3"):
        # Remove leading '/' from path for relative paths
        db_path = parsed.path.lstrip("/") if parsed.path else "db.sqlite3"
        return {
            "ENGINE": engine,
            "NAME": db_path,
        }

    # PostgreSQL configuration (Production)
    config = {
        "ENGINE": engine,
        "NAME": parsed.path.lstrip("/") if parsed.path else "",
        "USER": parsed.username or "",
        "PASSWORD": parsed.password or "",
        "HOST": parsed.hostname or "localhost",
        "PORT": parsed.port or "",
    }

    return config


def get_database_config() -> dict:
    settings = get_settings()

    # Parse database URL
    db_config = parse_database_url(settings.database_url)

    # Override database name if explicitly set
    if settings.database_name:
        db_config["NAME"] = settings.database_name

    return {"default": db_config}


# Django DATABASES setting
DATABASES = get_database_config()
