"""Marathon notifications and reboot-survival: native notifications (+ optional ntfy.sh) and per-user login entries.

notify() never raises: a failed toast must never stop a marathon. If <root>/.state/notify.json contains
{"ntfy_topic": "..."} the same message is also POSTed to https://ntfy.sh/<topic>.

install_autostart() writes a Windows Startup .cmd, Linux XDG .desktop or macOS LaunchAgent
that resumes the supervisor
(`bitacora.py --project P run REQ --resume`) in a terminal window after a reboot; remove_autostart() deletes it.
"""
from __future__ import annotations

import base64
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path
from xml.sax.saxutils import escape

import bt_autostart
import bt_nowindow  # noqa: F401  (no console windows for helper processes)
import bt_platform as host

APP_ID = "Bitácora"
NTFY_TIMEOUT = 5
TOAST_TIMEOUT = 20

_TOAST_PS = r"""
$ErrorActionPreference = 'Stop'
$id = 'Bitácora'
$key = "HKCU:\Software\Classes\AppUserModelId\$id"
if (-not (Test-Path $key)) { New-Item -Path $key -Force | Out-Null }
New-ItemProperty -Path $key -Name DisplayName -Value $id -PropertyType String -Force | Out-Null
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null
$xml = New-Object Windows.Data.Xml.Dom.XmlDocument
$xml.LoadXml([System.Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('__XML__')))
$toast = New-Object Windows.UI.Notifications.ToastNotification $xml
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($id).Show($toast)
"""


def _state_dir() -> Path:
    root = Path(os.environ.get("BITACORA_ROOT", Path.home() / "bitacora"))
    return root / ".state"


def _toast(title: str, message: str) -> None:
    if host.platform() != "windows":
        return host.local_notification(title, message)
    xml = (
        '<toast><visual><binding template="ToastText02">'
        f'<text id="1">{escape(title)}</text><text id="2">{escape(message)}</text>'
        "</binding></visual></toast>"
    )
    xml64 = base64.b64encode(xml.encode("utf-8")).decode("ascii")
    script = _TOAST_PS.replace("__XML__", xml64)
    encoded = base64.b64encode(script.encode("utf-16-le")).decode("ascii")
    exe = shutil.which("powershell") or "powershell"  # Windows PowerShell 5.1: WinRT types load there
    subprocess.run(
        [exe, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-EncodedCommand", encoded],
        capture_output=True, timeout=TOAST_TIMEOUT, check=True,
    )


def _ntfy(title: str, message: str) -> None:
    cfg = json.loads((_state_dir() / "notify.json").read_text(encoding="utf-8"))
    topic = (cfg.get("ntfy_topic") or "").strip()
    if not topic:
        return
    request = urllib.request.Request(
        f"https://ntfy.sh/{topic}", data=message.encode("utf-8"), method="POST",
        headers={"Title": title.encode("utf-8").decode("latin-1")},
    )
    urllib.request.urlopen(request, timeout=NTFY_TIMEOUT).close()


def notify(title: str, message: str) -> None:
    for send in (_toast, _ntfy):
        try:
            send(title, message)
        except Exception as exc:
            if send is _toast or (_state_dir() / "notify.json").exists():
                print(f"bitácora notification failed ({send.__name__}): {exc}", file=sys.stderr)


# ---------------------------------------------------------------- autostart

def _startup_dir() -> Path:
    appdata = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
    return Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"


def _safe(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name) or "x"


def autostart_path(project: str, req: str) -> Path:
    if host.platform() != "windows":
        return bt_autostart.entry_path(project, req)
    return _startup_dir() / f"metodologia-run-{_safe(project)}-{_safe(req)}.cmd"


def install_autostart(project: str, req: str, *, scheduler: bool = False) -> Path:
    from bt_core import ROOT, SCRIPT

    if host.platform() != "windows":
        return bt_autostart.install(project, req, ROOT, SCRIPT, scheduler=scheduler)

    command = "scheduler-run" if scheduler else "run"
    run = f'""{sys.executable}" "{SCRIPT}" --project {project} {command} {req} --resume"'  # outer quotes: cmd /k strips one pair
    title = f"{project} {req} marathon"
    if shutil.which("wt"):
        launch = f'wt -w new --title "{title}" cmd /k {run}'
    else:
        launch = f'start "{title}" cmd /k {run}'
    path = autostart_path(project, req)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f'@echo off\r\nset "BITACORA_ROOT={ROOT}"\r\n{launch}\r\n', encoding="mbcs", errors="replace")
    return path


def remove_autostart(project: str, req: str) -> None:
    if host.platform() != "windows":
        try:
            return bt_autostart.remove(project, req)
        except Exception as exc:  # a failed cleanup must not stop a marathon
            print(f"bitácora autostart removal failed: {exc}", file=sys.stderr)
            return
    try:
        autostart_path(project, req).unlink(missing_ok=True)
    except OSError:
        pass
