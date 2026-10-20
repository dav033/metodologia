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
    "routing": {"mode": "auto", "pool": [], "min_samples": 5, "explore_budget_week": 5, "effort_weight": {},
                "group_max": {}, "quality_protection": "critical", "quality_gap": 0.25,
                "explore_global_budget_week": 0},  # 0 = no global exploration cap
    "audit": {"mode": "milestone", "cross_provider": True, "provider": "antigravity"},
    "quota": {"default_cooldown_min": 30},
    "relay": {"enabled": False, "threshold_percent": 92, "exit_current": True, "max_chain": 3, "auto": True},
    "run": {"isolation": "off"},
    # a run without a human retries; up to 3 tasks at once when dependencies, files and resources allow it, but a task
    # whose plan scope is large runs alone in its repository; an agent process may work up to 2 h (the final gate takes
    # longer than 30 min)
    # gates: what the system enforces on its own. An audit is accepted by its findings ledger (bt_audit_gate): findings of
    # these severities left open reject it and send the tasks they name back (at most `max_reworks` times per task, then
    # the owner decides); with `audit_ledger_required` off, an audit that declares no ledger (a plan written before the
    # gate) is accepted on M6's verdict alone and the skip is recorded in the run's audit trail.
    "gates": {"audit_blocking": ["critical", "high"], "audit_ledger_required": True, "max_reworks": 2,
              "second_auditor": True, "audit_read_only": True,   # an audit that changes source is rejected (bt_audit_gate)
              # a verified result that could not be combined with the accepted work around it (the tasks about to start
              # after it) is rejected with the clash, so the task that caused it is the one sent back
              "integration_check": True,
              # clash rejections one task gets before the accepted tasks it clashes with are sent back to resolve the overlap on it
              "integration_retries": 0,
              # what an audit rejection sends back: "named" = the tasks its findings name plus the tests over them (what
              # depends on them keeps its result and is merged with the fix); "downstream" = also everything that
              # depends on them (a finding on a root task then redoes the whole plan)
              "rework_scope": "named",
              # a blocking audit finding becomes a remediation task on the integrated tree (the audit then runs again)
              # instead of sending the tasks it names back; after `remediation_rounds` rounds of one audit the named
              # tasks are sent back as before
              "audit_remediation": True, "remediation_rounds": 2,
              # an audit that sends back more tasks than this at once found a defect of the plan or the integration,
              # not of each builder: the attempt log records those tasks as redone, not as failed (bt_attempt_log)
              "attribute_max_tasks": 3},   # a plan with an audit also needs an independent cross-check audit
    # max_turns: turns one Claude attempt may use under the Scheduler (the legacy marathon keeps 45); an attempt that uses
    # them all is `incomplete_output` and is retried from its snapshot, so a low value costs attempts, not work
    "scheduler": {"max_attempts": 3, "max_parallel_tasks": 3, "attempt_timeout_minutes": 120, "max_turns": 120,
                  "exclusive_scopes": ["large_change", "full_feature", "full_system"]},
}
ALLOWED: dict[str, tuple] = {
    "executor.display": ("background", "window"),
    "routing.mode": ("auto", "fixed"),
    "routing.quality_protection": ("critical", "always", "off"),
    "audit.mode": ("milestone", "off"),
    "gates.rework_scope": ("named", "downstream"),
    "audit.provider": ("antigravity", "claude", "codex", "none"),
    "run.isolation": ("off", "worktree"),
}
ALLOWED_ITEMS: dict[str, tuple] = {"gates.audit_blocking": ("critical", "high", "medium", "low")}


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
    if correct_type and key in ALLOWED_ITEMS:
        correct_type = bool(value) and all(item in ALLOWED_ITEMS[key] for item in value)
    if correct_type and key == "gates.max_reworks":
        correct_type = value >= 1
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


def _stored() -> dict:
    """The file as written, or {} when it is missing, unreadable or not a JSON object."""
    try:
        stored = json.loads(_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return stored if isinstance(stored, dict) else {}


def _write(data: dict) -> Path:
    path = _path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)
    return path


def _change(key: str, value=None, *, remove: bool = False) -> Path:
    """Edit one key of the stored file and leave everything else as it was: sections and keys this version does not
    know (written by a newer one), and values it cannot use, survive a `set` or `unset` (REQ-007 R4, F-M1-01)."""
    data = _stored()
    section, name = key.split(".", 1)
    values = data.get(section)
    if not isinstance(values, dict):
        values = {}
    if remove:
        values.pop(name, None)
    else:
        values[name] = value
    if values:
        data[section] = values
    else:  # a section this change emptied is not left behind as {}
        data.pop(section, None)
    return _write(data)


def set_value(key: str, value) -> Path:
    """Validate and persist one setting; a value equal to the default is removed, not stored."""
    if key not in _keys():
        raise ConfigError(f"Unknown configuration key '{key}'")
    if not _valid(key, value):
        expected = f"one of {ALLOWED[key]}" if key in ALLOWED else type(_keys()[key]).__name__
        raise ConfigError(f"Invalid value for '{key}': expected {expected}")
    return _change(key, value, remove=value == _keys()[key])


def unset(key: str) -> Path:
    """Remove one setting override."""
    if key not in _keys():
        raise ConfigError(f"Unknown configuration key '{key}'")
    return _change(key, remove=True)


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
