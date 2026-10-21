"""Native process and terminal integration for Windows, Linux and macOS."""
from __future__ import annotations

import os
import re
import shlex
import socket
import shutil
import subprocess
import sys
from pathlib import Path


def systemd_listener(port: int) -> socket.socket | None:
    """Return systemd's inherited listening socket for `port`, if this is its activated service."""
    if not sys.platform.startswith("linux"):
        return None
    try:
        if os.environ.get("LISTEN_PID") != str(os.getpid()) or os.environ.get("LISTEN_FDS") != "1":
            return None
        listener = socket.fromfd(3, socket.AF_INET, socket.SOCK_STREAM)
    except (OSError, ValueError):
        return None
    if listener.getsockname() != ("127.0.0.1", port):
        listener.close()
        raise RuntimeError(f"systemd listener is not bound to 127.0.0.1:{port}")
    return listener


def platform() -> str:
    if os.name == "nt":
        return "windows"
    if sys.platform == "darwin":
        return "macos"
    if sys.platform.startswith("linux"):
        return "linux"
    raise RuntimeError(f"Unsupported platform: {sys.platform}")


def detached_options() -> dict:
    if platform() == "windows":
        return {"creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
                | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 512)}
    return {"start_new_session": True}


def sleep_inhibitor_argv(platform_name: str, pid: int) -> list[str] | None:
    """Sleep-inhibitor command that exits by itself when process `pid` does; None when the host has none."""
    if platform_name == "darwin" and shutil.which("caffeinate"):
        return ["caffeinate", "-i", "-w", str(pid)]
    if platform_name.startswith("linux") and shutil.which("systemd-inhibit"):
        return ["systemd-inhibit", "--what=sleep:idle", "--who=metodologia", "--why=marathon running",
                "--mode=block", "tail", f"--pid={pid}", "-f", "/dev/null"]
    return None


def ps_quote(value: str | Path) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def write_script(base: Path, cwd: Path, argv: list[str], env: dict[str, str],
                 prompt_file: Path | None = None) -> Path:
    """Store arguments as literals; only an explicitly supplied prompt file is expanded."""
    if platform() == "windows":
        path = base.parent / (base.name + ".ps1")
        lines = ["$ErrorActionPreference = 'Stop'", f"Set-Location -LiteralPath {ps_quote(cwd)}"]
        lines += [f"$env:{key} = {ps_quote(value)}" for key, value in env.items()]
        if prompt_file:
            lines.append(f"$prompt = Get-Content -Raw -Encoding UTF8 -LiteralPath {ps_quote(prompt_file)}")
        lines.append("& " + " ".join(ps_quote(arg) for arg in argv) + (" $prompt" if prompt_file else ""))
        lines.append("exit $LASTEXITCODE")
    else:
        path = base.parent / (base.name + ".sh")
        lines = ["#!/bin/bash", "set -e", f"cd -- {shlex.quote(str(cwd))}"]
        lines += [f"export {key}={shlex.quote(value)}" for key, value in env.items()]
        prompt = f' "$(cat -- {shlex.quote(str(prompt_file))})"' if prompt_file else ""
        lines.append("exec " + shlex.join(argv) + prompt)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Windows PowerShell 5.1 needs a BOM to decode non-ASCII paths correctly.
    path.write_text("\n".join(lines) + "\n", encoding="utf-8-sig" if platform() == "windows" else "utf-8")
    if platform() != "windows":
        path.chmod(0o700)
    return path


def _headless() -> bool:
    """No graphical session (SSH, systemd) or an explicit BITACORA_TERMINAL=tmux."""
    if os.environ.get("BITACORA_TERMINAL") == "tmux":
        return True
    return not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))


def _headless_command(cwd: Path, script: Path, title: str) -> list[str]:
    """tmux session when available (attachable: `tmux attach -t NAME`), else a transient systemd user unit."""
    name = re.sub(r"[^A-Za-z0-9_-]+", "-", title).strip("-") or "metodologia"
    if shutil.which("tmux"):
        return ["tmux", "new-session", "-d", "-s", name, "-c", str(cwd), "/bin/bash", "-l", str(script)]
    if shutil.which("systemd-run"):
        return ["systemd-run", "--user", f"--unit=metodologia-{name}", f"--working-directory={cwd}",
                "/bin/bash", "-l", str(script)]
    raise RuntimeError(f"No display, tmux or systemd-run available. Run manually: bash {shlex.quote(str(script))}")


def open_terminal(cwd: Path, script: Path, title: str) -> str:
    host = platform()
    if host == "windows":
        pwsh = shutil.which("pwsh") or shutil.which("powershell")
        if not pwsh:
            raise RuntimeError(f"PowerShell not found. Run manually: {script}")
        cmd = (["wt", "-w", "new", "--title", title, "-d", str(cwd)] if shutil.which("wt")
               else ["cmd", "/c", "start", title]) + [pwsh, "-NoExit", "-File", str(script)]
        subprocess.Popen(cmd, cwd=str(cwd), creationflags=getattr(subprocess, "CREATE_NEW_CONSOLE", 16))
    elif host == "macos":
        # AppleScript receives the shell command as data, never interpolated source.
        command = shlex.join(["/bin/bash", "-l", str(script)])
        source = ('on run argv\n tell application "Terminal"\n activate\n'
                  ' do script (item 1 of argv)\n end tell\nend run')
        cmd = ["osascript", "-e", source, command]
        subprocess.run(cmd, check=True, capture_output=True, timeout=20)
    elif _headless():
        cmd = _headless_command(cwd, script, title)
        subprocess.run(cmd, cwd=str(cwd), check=True, capture_output=True, timeout=20)
    else:
        terminals = {
            "kitty": ["--title", title, "--hold"],
            "gnome-terminal": ["--title", title, "--"],
            "konsole": ["--hold", "-e"],
            "xterm": ["-T", title, "-hold", "-e"],
            "x-terminal-emulator": ["-e"],
        }
        found = next((exe for exe in terminals if shutil.which(exe)), None)
        if not found:
            raise RuntimeError(f"No supported terminal found. Run manually: bash {shlex.quote(str(script))}")
        cmd = [found, *terminals[found], "/bin/bash", "-l", str(script)]
        subprocess.Popen(cmd, cwd=str(cwd), **detached_options())
    return subprocess.list2cmdline(cmd) if host == "windows" else shlex.join(cmd)


def local_notification(title: str, message: str) -> None:
    if platform() == "macos":
        source = ('on run argv\n display notification (item 2 of argv) '
                  'with title (item 1 of argv)\nend run')
        cmd = ["osascript", "-e", source, title, message]
    else:
        cmd = ["notify-send", "--app-name=Bitácora", "--", title, message]
    subprocess.run(cmd, check=True, capture_output=True, timeout=20)


def gitleaks_install_hint() -> str:
    return {"windows": "winget install Gitleaks.Gitleaks", "macos": "brew install gitleaks",
            "linux": "install gitleaks with your distribution package manager (Arch: pacman -S gitleaks)"}[platform()]
