"""Environment variables for the independent checks (M6), read from an owner-kept dotenv file.

The sandbox starts with a clean environment, so a check that needs a database URL or an API key gets it only from
here. The file lives outside the repositories (the config key `verifier.env_file`); its values never reach the
bitácora, the plan or argv, and the ones that look secret are registered so every output redacts them.
"""
from __future__ import annotations

import fnmatch
import os
import re
from pathlib import Path

from bt_scheduler_quality.policy import ENV_NAME, FORBIDDEN_ENV, MAX_ENV_BYTES, SENSITIVE_ENV

MAX_VALUE_BYTES = 4096
_LINE = re.compile(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$")
_CREDENTIAL_URL = re.compile(r"://[^/\s:@]+:[^/\s@]+@")


def _value(raw: str) -> str:
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "\"'":
        return raw[1:-1]
    return raw.split(" #", 1)[0].strip()


def path_for(template: object, project: str) -> str:
    """The env file of a project: `{project}` in the configured path is replaced, so one setting keeps each project's
    keys out of the checks of the others. A project without its own file simply gets none."""
    if not isinstance(template, str) or not template.strip():
        return ""
    return template.replace("{project}", re.sub(r"[^A-Za-z0-9_.-]", "", project or ""))


def load(path: str | Path | None) -> tuple[tuple[tuple[str, str], ...], tuple[str, ...]]:
    """(environment, secret values) from the dotenv file, or empty ones when it is unset, missing or unreadable.
    A name the sandbox protects, a value that is too long or has control characters is skipped, never an error."""
    if not path:
        return (), ()
    try:
        lines = Path(path).expanduser().read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return (), ()
    environment: dict[str, str] = {}
    total = 0
    for line in lines:
        match = None if line.lstrip().startswith("#") else _LINE.match(line)
        if not match:
            continue
        key, value = match.group(1), _value(match.group(2))
        if (not ENV_NAME.fullmatch(key) or key in FORBIDDEN_ENV or key.startswith(("LD_", "GIT_", "PYTHON"))
                or not value or len(value.encode()) > MAX_VALUE_BYTES or any(ord(c) < 32 for c in value)):
            continue
        total += len(key.encode()) + len(value.encode())
        if total > MAX_ENV_BYTES // 2:
            break
        environment[key] = value
    secrets = tuple(dict.fromkeys(value for key, value in environment.items()
                                  if SENSITIVE_ENV.search(key) or _CREDENTIAL_URL.search(value)))
    return tuple(environment.items()), secrets


def declared(rdir: str | Path | None) -> set[str]:
    """Variable names the checks of the run's latest frozen revision declare in `requires` (a `service:` probe is not a
    variable); empty when there is no frozen revision."""
    if not rdir:
        return set()
    import bt_plan_adapter   # the planner is reached only through its adapter (test_plan_boundary)
    try:
        plan = bt_plan_adapter.latest_plan(Path(rdir)) or {}
    except Exception:  # noqa: BLE001 - an unreadable store adds nothing; the frozen-plan gates report it
        return set()
    return {name for task in plan.get("tasks") or [] if isinstance(task, dict)
            for check in task.get("verification") or [] if isinstance(check, dict)
            for name in check.get("requires") or []
            if isinstance(name, str) and ENV_NAME.fullmatch(name)}


def _patterns(value: object) -> tuple[str, ...]:
    """`verifier.inherit_env`: True or "*" for everything, or a list of variable-name globs (PICTURES_*, DATABASE_URL)."""
    if value is True:
        return ("*",)
    if isinstance(value, str):
        value = [value]
    return tuple(p for p in value if isinstance(p, str) and p.strip()) if isinstance(value, list) else ()


def inherited(patterns: tuple[str, ...], sources: list[dict[str, str]], skip: set[str]) -> dict[str, str]:
    """The variables a check inherits instead of starting empty: those of `sources` (the owner's environment and its secret
    files) whose name matches a pattern, with the same refusals as the env file (sandbox-protected names, LD_/GIT_/PYTHON*,
    control characters, size). Names in `skip` (already set by the project's env file) keep their value."""
    found: dict[str, str] = {}
    total = 0
    for source in sources:
        for key, value in source.items():
            if (key in skip or key in found or not any(fnmatch.fnmatchcase(key, p) for p in patterns)
                    or not ENV_NAME.fullmatch(key) or key in FORBIDDEN_ENV or key.startswith(("LD_", "GIT_", "PYTHON"))
                    or not value or len(value.encode()) > MAX_VALUE_BYTES or any(ord(c) < 32 for c in value)):
                continue
            total += len(key.encode()) + len(value.encode())
            if total > MAX_ENV_BYTES // 4:
                return found
            found[key] = value
    return found


def for_run(project: str, rdir: str | Path | None = None) -> tuple[tuple[tuple[str, str], ...], tuple[str, ...]]:
    """What the checks of a run receive: the project's `verifier.env_file`, plus each variable a check of the frozen plan
    declares in `requires` that is missing there, taken from the owner's secret files (`verifier.secret_files`). Only
    declared names are copied, so a check never sees the rest of those files; nothing is written anywhere."""
    import bt_config
    environment, _ = load(path_for(bt_config.get("verifier.env_file", ""), project))
    merged = dict(environment)
    wanted = declared(rdir) - set(merged)
    for source in bt_config.get("verifier.secret_files", []) or []:
        if not wanted:
            break
        found = {key: value for key, value in load(path_for(source, project))[0] if key in wanted}
        merged.update(found)
        wanted -= set(found)
    secrets = tuple(dict.fromkeys(value for key, value in merged.items()
                                  if SENSITIVE_ENV.search(key) or _CREDENTIAL_URL.search(value)))
    return tuple(merged.items()), secrets


def ambient_for_run(project: str, explicit: set[str]) -> tuple[tuple[tuple[str, str], ...], tuple[str, ...]]:
    """(variables, secret-looking values) the checks INHERIT under `verifier.inherit_env`: the owner's environment and every
    variable of his secret files. They are handed to the sandbox but kept out of the evidence fingerprint (see
    `QualityPolicy.ambient_environment`); names the project's env file or the plan's `requires` already set keep that value."""
    import bt_config
    patterns = _patterns(bt_config.get("verifier.inherit_env", []))
    if not patterns:
        return (), ()
    files = [dict(load(path_for(source, project))[0]) for source in bt_config.get("verifier.secret_files", []) or []]
    found = inherited(patterns, [dict(os.environ), *files], set(explicit))
    secrets = tuple(dict.fromkeys(value for key, value in found.items() if SENSITIVE_ENV.search(key) or _CREDENTIAL_URL.search(value)))
    return tuple(found.items()), secrets


# URL schemes of network resources a check may need (a database, a cache, a broker, a service) and their default ports
RESOURCE_PORTS = {"postgres": 5432, "postgresql": 5432, "mysql": 3306, "mariadb": 3306, "redis": 6379, "rediss": 6379,
                  "mongodb": 27017, "amqp": 5672, "amqps": 5671, "http": 80, "https": 443}


def resource_of(value: object) -> dict | None:
    """{"scheme", "host", "port", "database", "label"} of a network URL value, or None (not a URL, a unix socket, several
    hosts). `label` (`postgresql 127.0.0.1:55965/req021_visual`) is what may be shown: never the user, password or query."""
    from urllib.parse import urlsplit
    if not isinstance(value, str) or "://" not in value:
        return None
    try:
        parts = urlsplit(value.strip())
        scheme = parts.scheme.lower().split("+", 1)[0]          # postgresql+psycopg -> postgresql
        host, port = parts.hostname, parts.port or RESOURCE_PORTS.get(scheme)
    except ValueError:                                            # a bad port or several hosts (h1:5432,h2:5432)
        return None
    if scheme not in RESOURCE_PORTS or not host or not port:
        return None
    database = parts.path.lstrip("/").split("/", 1)[0] if scheme not in ("http", "https") else ""
    shown = f"[{host}]" if ":" in host else host
    return {"scheme": scheme, "host": host, "port": int(port), "database": database,
            "label": f"{scheme} {shown}:{port}" + (f"/{database}" if database else "")}


def verifier_values(policy: object | None) -> dict[str, str]:
    """Every variable the independent checks receive under `policy` (inherited ones first, the explicit ones win)."""
    values = dict(getattr(policy, "ambient_environment", ()) or ())
    values.update(dict(getattr(policy, "environment", ()) or ()))
    return values


def one_source(test_env: dict | None, policy: object | None, inherited=()) -> tuple[dict[str, str], tuple[dict, ...]]:
    """(the variables an attempt gets over its inherited environment, the divergent keys) with ONE source per key (D-265).

    The checks' environment (`policy`, built by `operator_quality_policy` from `verifier.env_file`, the plan's `requires`
    and `verifier.inherit_env`) is the source of truth: the attempt receives the verifier's value for every key the
    verifier sets explicitly, and for every key it would hold anyway (its inherited names, `inherited`, and the agent env
    file) that the checks inherit. The agent env file (`test_env`) only ADDS keys the checks do not have. A key in both
    with a different value is a divergence: the verifier's value is used and the key is reported (names and
    `resource_of` labels, never a value). pictures REQ-021 r32 T3.91: the agent file's copy of PICTURES_REQ021_DATABASE_URL
    named a port nothing listened on while the checks used the live tunnel; three attempts could not run their check.
    Without a policy (it could not be built) the agent env file is used as it is."""
    test_env = dict(test_env or {})
    if policy is None:
        return test_env, ()
    checks = verifier_values(policy)
    out = {key: value for key, value in test_env.items() if key not in checks}
    out.update(dict(getattr(policy, "environment", ()) or ()))
    for key in {*test_env, *inherited}:
        if key in checks:
            out[key] = checks[key]
    divergent = []
    for key in sorted(test_env):
        if key in checks and test_env[key] != checks[key]:
            mine, theirs = resource_of(test_env[key]), resource_of(checks[key])
            divergent.append({"key": key, "agent": mine["label"] if mine else "another value",
                              "verifier": theirs["label"] if theirs else "another value",
                              "same_resource": bool(mine and theirs and mine["label"] == theirs["label"])})
    return out, tuple(divergent)


def divergence_sentence(divergent) -> str:
    """The divergent keys as one sentence (names and resource labels only)."""
    parts = [f"{item['key']} (agent env file: {item['agent']}; verifier: {item['verifier']})" for item in divergent]
    return ("; ".join(parts[:MAX_NAMED]) + (f" and {len(parts) - MAX_NAMED} more" if len(parts) > MAX_NAMED else ""))


MAX_NAMED = 24


def _names(names) -> str:
    names = sorted(names)
    shown = ", ".join(names[:MAX_NAMED])
    return shown + (f" and {len(names) - MAX_NAMED} more" if len(names) > MAX_NAMED else "")


def check_environment(policy: object) -> tuple[tuple[str, ...], int]:
    """(names the checks receive from the owner's verifier settings, how many more they inherit from the owner's own
    environment under `verifier.inherit_env`) for a QualityPolicy-like object. Names only, never a value."""
    explicit = tuple(sorted({name for name, _ in getattr(policy, "environment", ()) or ()}))
    ambient = {name for name, _ in getattr(policy, "ambient_environment", ()) or ()} - set(explicit)
    return explicit, len(ambient)


def check_environment_sentence(policy: object | None) -> str:
    """What the sandbox's environment really is, for an agent: until D-257 every failure digest said the checks get
    «none of your environment variables», whatever the verifier settings gave them (pictures REQ-021 r30 T10.45:
    the owner's verifier file and his whole environment reached the checks, while the attempt read that they got none)."""
    if policy is None:
        return "NOT your environment: only what the owner's verifier settings give them"
    explicit, ambient = check_environment(policy)
    if not explicit and not ambient:
        return "none of your environment variables (the sandbox sets only PATH, HOME, TMPDIR, the locale and the toolchain's own)"
    parts = []
    if explicit:
        parts.append("only " + _names(explicit) + " from the owner's verifier settings")
    if ambient:
        parts.append(f"{'plus ' if explicit else 'only '}{ambient} variable{'s' if ambient != 1 else ''} of the owner's own "
                     "environment (verifier.inherit_env)")
    return ("NOT your environment: they receive " + ", ".join(parts)
            + "; any other variable your attempt had is absent there")


def attempt_note(test_env: dict | None, policy: object | None, divergent=()) -> str:
    """The brief's environment paragraph: the owner's test variables of this attempt (`execution.agent_env_file`) and what
    the independent checks will receive instead, so a harness that starts the product sets what it depends on itself.
    `divergent` (`one_source`): keys whose agent env file value differed from the verifier's; the attempt got the
    verifier's value."""
    test_env = dict(test_env or {})
    lines = []
    if divergent:
        lines.append("Environment source: " + divergence_sentence(divergent) + ". The owner's agent env file disagreed "
                     "with the verifier for " + ("this key" if len(divergent) == 1 else "these keys") + "; you received "
                     "the VERIFIER's value, the one your checks run with, and the owner has been told the agent env file "
                     "is stale. Reproduce what the verifier runs; do not point your checks anywhere else.")
    if test_env:
        lines.append("Test environment: " + ", ".join(sorted(test_env)) + (" is" if len(test_env) == 1 else " are")
                     + " set in your environment by the owner for testing (a disposable database, never production). "
                     "Run the verification commands that need them yourself before you finish; never print, copy or "
                     "commit their values.")
    if policy is None:
        return "\n".join(lines)
    explicit, ambient = check_environment(policy)
    seen = set(explicit) | {name for name, _ in getattr(policy, "ambient_environment", ()) or ()}
    missing = sorted(set(test_env) - seen)
    text = ("Check environment: the independent verification runs your checks in a sandbox that does NOT get your "
            "environment. It receives " + (("only " + _names(explicit) + " from the owner's verifier settings")
                                           if explicit else "no variable from the owner's verifier settings"))
    if ambient:
        text += f", plus {ambient} variable{'s' if ambient != 1 else ''} of the owner's own environment"
    text += "."
    if missing:
        text += " " + _names(missing) + (" is" if len(missing) == 1 else " are") + " NOT among them."
    text += (" A test harness that starts the product (a server, a worker) with an explicit environment gets nothing it "
             "does not set itself: set every product setting its scenario depends on (feature flags and provider "
             "switches included) explicitly; otherwise the product runs with its own defaults, never with your shell's.")
    lines.append(text)
    return "\n".join(lines)
