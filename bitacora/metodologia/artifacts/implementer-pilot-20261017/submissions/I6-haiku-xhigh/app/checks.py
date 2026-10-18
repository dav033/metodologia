"""Argument validation for the store API. Runs before any database access."""

INT64_MIN = -(2**63)
INT64_MAX = 2**63 - 1


def require_str(name, value):
    if not isinstance(value, str):
        raise TypeError(f'{name} must be str, not {type(value).__name__}')


def require_optional_str(name, value):
    if value is not None:
        require_str(name, value)


def require_int(name, value):
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f'{name} must be int, not {type(value).__name__}')
    if not INT64_MIN <= value <= INT64_MAX:
        raise OverflowError(f'{name} is outside the SQLite INTEGER range')


def require_callable(name, value):
    if not callable(value):
        raise TypeError(f'{name} must be callable, not {type(value).__name__}')
