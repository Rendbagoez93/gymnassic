import logging
import os

logger = logging.getLogger(__name__)


class Maybe:
    def __init__(self, value):
        self._value = value

    def bind(self, func):
        if self._value is None:
            return Maybe(None)
        else:
            return Maybe(func(self._value))

    def orElse(self, default):
        if self._value is None:
            return Maybe(default)
        else:
            return self

    def unwrap(self):
        return self._value

    def __or__(self, other):
        return Maybe(self._value or other._value)

    def __str__(self):
        if self._value is None:
            return "Nothing"
        else:
            return f"Just {self._value}"

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        if isinstance(other, Maybe):
            return self._value == other._value
        else:
            return False

    def __ne__(self, other):
        return not (self == other)

    def __bool__(self):
        return self._value is not None

    def __getattr__(self, item):
        if self._value is None:
            return None
        return getattr(self._value, item, None)


class Either:
    """
    Either monad - the reverse of Maybe.
    Where Maybe continues when value is not None, Either stops when value is not None.
    Examples:
        result = Either(None).bind(lambda: first_func()).bind(lambda: second_func())
    """

    def __init__(self, value=None):
        self._value = value

    def __is_not_none_or_empty(self) -> bool:
        """
        zero is allowed.
        boolean False is allowed.
        empty list is not allowed.
        """
        if isinstance(self._value, list) and len(self._value) == 0:
            return False
        return self._value is not None

    def bind(self, func, *args, **kwargs):
        if self.__is_not_none_or_empty():
            # Stop the chain if we already have a value
            return self
        else:
            try:
                return Either(func(*args, **kwargs))
            except Exception:
                logger.debug(f"Error occurred while binding {func.__name__}")
                return Either(None)

    def unwrap(self):
        if self._value:
            return self._value
        else:
            raise ValueError("No value present")

    def unwrap_or(self, default):
        if self._value is not None:
            return self._value
        else:
            return default

    def __str__(self):
        if self._value is not None:
            return f"Either({self._value})"
        else:
            return "Empty"

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        if isinstance(other, Either):
            return self._value == other._value
        else:
            return False

    def __bool__(self):
        return self._value is not None


# Environment variable helpers using Maybe monad
def get_env(key: str, default=None):
    return Maybe(os.getenv(key)).orElse(default)


def get_env_bool(key: str, default: bool = False) -> bool:

    value = os.getenv(key)
    if value is None:
        return default

    return value.lower() in ("true", "1", "yes", "on")


def get_env_int(key: str, default: int = 0) -> int:
    try:
        return Maybe(get_env(key, None).unwrap()).bind(int).unwrap()
    except (ValueError, TypeError):
        logger.debug(f"Failed to parse {key} as int, using default: {default}")
        return default


def get_env_list(key: str, separator: str = ",", default: list | None = None) -> list:
    """
    Get list environment variable.

    Args:
        key: Environment variable name
        separator: Separator for splitting the value
        default: Default value if not found

    Returns:
        List parsed from environment variable.
    """
    import os

    value = os.getenv(key)
    if value is None:
        return default or []

    return [item.strip() for item in value.split(separator) if item.strip()]
