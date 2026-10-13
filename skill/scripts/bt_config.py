"""Machine-local configuration stored in <STATE>/config.json.

Values in this file override the defaults below. Invalid stored values are ignored one key at a time so a damaged
setting does not make the rest of the configuration unavailable.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

from bt_core import STATE

DEFAULTS: dict = {
    "executor": {"display": "background"},
    "approval": {"auto": True, "max_milestones": 8, "max_tasks": 40},
    "learn": {"promote_after": 3, "inject_max": 12},
    "routing": {"mode": "auto", "pool": []},
    "audit": {"mode": "milestone", "cross_provider": True},
    "quota": {"default_cooldown_min": 30},
}
ALLOWED: dict[str, tuple] = {
    "executor.display": ("background", "window"),
    "routing.mode": ("auto", "fixed"),
    "audit.mode": ("milestone", "off"),
}


class ConfigError(SystemExit):
    """Invalid configuration key or value."""


def _path() -> Path:
    return STATE / "config.json"


def _keys() -> dict[str, object]:
    return {f"{section}.{name}": value for section, values in DEFAULTS.items() for name, value in values.items()}


def _valid(key: str, value: object) -> bool:
    default = _keys()[key]
    if isinstance(default, bool):
        correct_type = isinstance(value, bool)
    elif isinstance(default, int):
        correct_type = isinstance(value, int) and not isinstance(value, bool) and value >= 0
    elif isinstance(default, list):
        correct_type = isinstance(value, list) and all(isinstance(item, str) for item in value)
    else:
        correct_type = isinstance(value, type(default))
    return correct_type and (key not in ALLOWED or value in ALLOWED[key])


def _flatten(data: object) -> dict[str, object]:
    if not isinstance(data, dict):
        return {}
    flattened = {}
    for section, values in data.items():
        if isinstance(values, dict):
            flattened.update({f"{section}.{name}": value for name, value in values.items()})
    return flattened


def load() -> dict:
    """Return defaults merged with each valid stored override."""
    config = copy.deepcopy(DEFAULTS)
    try:
        stored = json.loads(_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return config
    for key, value in _flatten(stored).items():
        if key in _keys() and _valid(key, value):
            section, name = key.split(".", 1)
            config[section][name] = value
    return config


def get(key: str, default=None):
    """Return a dotted setting, or `default` for an unknown key."""
    if key not in _keys():
        return default
    section, name = key.split(".", 1)
    return load()[section][name]


def _overrides() -> dict[str, object]:
    try:
        stored = json.loads(_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return {key: value for key, value in _flatten(stored).items()
            if key in _keys() and _valid(key, value) and value != _keys()[key]}


def _write(overrides: dict[str, object]) -> Path:
    path = _path()
    data: dict[str, dict] = {}
    for key, value in overrides.items():
        section, name = key.split(".", 1)
        data.setdefault(section, {})[name] = value
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)
    return path


def set_value(key: str, value) -> Path:
    """Validate and persist one setting, writing only non-default overrides."""
    if key not in _keys():
        raise ConfigError(f"Unknown configuration key '{key}'")
    if not _valid(key, value):
        expected = f"one of {ALLOWED[key]}" if key in ALLOWED else type(_keys()[key]).__name__
        raise ConfigError(f"Invalid value for '{key}': expected {expected}")
    overrides = _overrides()
    if value == _keys()[key]:
        overrides.pop(key, None)
    else:
        overrides[key] = value
    return _write(overrides)


def unset(key: str) -> Path:
    """Remove one setting override."""
    if key not in _keys():
        raise ConfigError(f"Unknown configuration key '{key}'")
    overrides = _overrides()
    overrides.pop(key, None)
    return _write(overrides)


def parse_cli_value(text: str):
    """Parse JSON literals while leaving ordinary text untouched."""
    try:
        return json.loads(text)
    except ValueError:
        return text


def cli(action: str, key: str | None, value: str | None) -> str:
    """Run a config command and return the text intended for stdout."""
    if action == "get":
        if key is None:
            return json.dumps(load(), indent=1, ensure_ascii=False)
        if key not in _keys():
            raise ConfigError(f"Unknown configuration key '{key}'")
        return json.dumps(get(key), ensure_ascii=False)
    if action == "set":
        if key is None or value is None:
            raise ConfigError("'set' requires a key and value")
        parsed = parse_cli_value(value)
        if isinstance(_keys().get(key), list) and not isinstance(parsed, list):
            parsed = [] if value == "" else value.split(",")
        set_value(key, parsed)
        return f"Set {key}."
    if action == "unset":
        if key is None:
            raise ConfigError("'unset' requires a key")
        unset(key)
        return f"Unset {key}."
    raise ConfigError(f"Unknown config action '{action}' (get, set, unset)")
