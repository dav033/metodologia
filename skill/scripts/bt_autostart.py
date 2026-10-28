"""Per-user login entries for resuming a marathon; no system privileges required."""
from __future__ import annotations

import os
import plistlib
import re
import shutil
import subprocess
import sys
from pathlib import Path

import bt_platform as host


def entry_path(project: str, req: str) -> Path:
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", f"{project}-{req}")
    if host.platform() == "macos":
        return Path.home() / "Library/LaunchAgents" / f"local.metodologia.{name}.plist"
    config = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    if shutil.which("systemctl"):
        return config / "systemd/user" / f"metodologia-run-{name}.service"
    return config / "autostart" / f"metodologia-run-{name}.desktop"


def desktop_arg(value: str) -> str:
    if "\n" in value or "\r" in value:
        raise ValueError("Desktop command paths must not contain line breaks")
    # Exec quoting is decoded after the desktop-entry string escaping layer.
    quoted = '"' + re.sub(r'([\\"`$])', r'\\\1', value) + '"'
    return quoted.replace("\\", "\\\\").replace("%", "%%")


def stable_path(value: str) -> str:
    """The PATH to bake into a boot-time script, without per-shell directories. fnm puts `/run/user/<uid>/fnm_multishells/<pid>_<ts>/bin`
    on PATH: a symlink to the node version in use, created by that shell and gone after the next boot. A service launched with it
    could not find `codex` or `node` (REQ-021 after a reboot: Codex quota sampling answered `app_server_unavailable`, so the
    router assigned nothing). Each such entry becomes the real directory it points to, or is dropped if it points nowhere."""
    out: list[str] = []
    for entry in value.split(os.pathsep):
        if "fnm_multishells" in entry:
            entry = os.path.realpath(entry) if os.path.isdir(entry) else ""
        if entry and entry not in out:
            out.append(entry)
    return os.pathsep.join(out)


def install(project: str, req: str, root: Path, cli: Path, *, scheduler: bool = False) -> Path:
    path = entry_path(project, req)
    name = path.stem
    state = root / ".state"
    # a Scheduler run comes back through its watchdog, which resumes the owner and keeps it alive
    command = ["scheduler-watch", req] if scheduler else ["run", req, "--resume"]
    script = host.write_script(state / "launch" / name, root,
                               [sys.executable, str(cli), "--project", project, *command],
                               {"BITACORA_ROOT": str(root), "PATH": stable_path(os.environ.get("PATH", ""))})
    argv = ["/bin/bash", "-l", str(script)]
    path.parent.mkdir(parents=True, exist_ok=True)
    if host.platform() == "macos":
        content = {"Label": name, "ProgramArguments": argv, "RunAtLoad": True,
                   "StandardOutPath": str(state / f"{name}.log"),
                   "StandardErrorPath": str(state / f"{name}.log")}
        path.write_bytes(plistlib.dumps(content))
    elif path.suffix == ".service":
        script_arg = str(script).replace("\\", "\\\\").replace('"', '\\"').replace("$", "$$").replace("%", "%%")
        if "\n" in script_arg or "\r" in script_arg:
            raise ValueError("Service paths must not contain line breaks")
        path.write_text('[Unit]\nDescription=Metodologia marathon\n[Service]\nType=exec\n'
                        f'ExecStart=/bin/bash -l "{script_arg}"\n[Install]\nWantedBy=default.target\n', encoding="utf-8")
    else:
        path.write_text("[Desktop Entry]\nType=Application\nName=Metodologia marathon\n"
                        f"Exec={' '.join(desktop_arg(arg) for arg in argv)}\nTerminal=false\n", encoding="utf-8")
    path.chmod(0o600)
    if path.suffix == ".service":
        subprocess.run(["systemctl", "--user", "daemon-reload"], check=True, capture_output=True, timeout=15)
        subprocess.run(["systemctl", "--user", "enable", path.name], check=True, capture_output=True, timeout=15)
    return path


def remove(project: str, req: str) -> None:
    path = entry_path(project, req)
    if not path.exists():
        return
    if path.suffix == ".service":
        # Do not stop the current supervisor when it removes its next-login entry.
        subprocess.run(["systemctl", "--user", "disable", path.name], check=True, capture_output=True, timeout=15)
    path.unlink()
    if path.suffix == ".service":
        subprocess.run(["systemctl", "--user", "daemon-reload"], check=True, capture_output=True, timeout=15)
