"""Bubblewrap launcher configuration and native process resource ownership."""

from __future__ import annotations

import json
import os
import secrets
import selectors
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .policy import CheckSpec, QualityPolicy

NAMESPACE_FIELDS = {
    "mnt": "mnt-namespace",
    "net": "net-namespace",
    "pid": "pid-namespace",
    "ipc": "ipc-namespace",
    "uts": "uts-namespace",
}
_BASE_ENVIRONMENT = {
    "PATH": "/usr/bin:/bin",
    "HOME": "/home/runner",
    "TMPDIR": "/tmp",
    "LANG": "C.UTF-8",
    "LC_ALL": "C.UTF-8",
    "PYTHONDONTWRITEBYTECODE": "1",
    "PYTHONNOUSERSITE": "1",
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_CONFIG_GLOBAL": "/dev/null",
    "GIT_TERMINAL_PROMPT": "0",
    "GIT_OPTIONAL_LOCKS": "0",
    "GIT_ATTR_NOSYSTEM": "1",
    "GIT_NO_REPLACE_OBJECTS": "1",
}
_LAUNCHER = r"""import json
import os
import resource
import shutil
import subprocess
import sys
from pathlib import Path, PurePosixPath

CONFIG_PATH = "/run/m6-config.json"

def fail(code):
    sys.stderr.write("M6_SETUP_ERROR:" + code + "\n")
    return 125

try:
    with open(CONFIG_PATH, "r", encoding="utf-8") as stream:
        config = json.load(stream)
    os.unlink(CONFIG_PATH)
except Exception:
    raise SystemExit(fail("CONFIG"))

if sys.stdin.buffer.read(1) != b"\x01":
    raise SystemExit(124)

try:
    limits = config["limits"]
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_AS, (limits["address_space"], limits["address_space"]))
    resource.setrlimit(resource.RLIMIT_CPU, (limits["cpu_seconds"], limits["cpu_seconds"]))
    resource.setrlimit(resource.RLIMIT_FSIZE, (limits["file_size"], limits["file_size"]))
    resource.setrlimit(resource.RLIMIT_NOFILE, (128, 128))
    resource.setrlimit(resource.RLIMIT_NPROC, (64, 64))
    shutil.copytree("/source", "/workspace", symlinks=True, dirs_exist_ok=True)
    workspace = Path("/workspace").resolve(strict=True)
    cwd = PurePosixPath(config["cwd"])
    if cwd.is_absolute() or ".." in cwd.parts:
        raise ValueError("cwd")
    target = (workspace / Path(*cwd.parts)).resolve(strict=True)
    target.relative_to(workspace)
    if not target.is_dir():
        raise ValueError("cwd")
    os.chdir(target)
except Exception:
    raise SystemExit(fail("WORKSPACE"))

environment = dict(config["environment"])
if len(environment) != len(config["environment"]):
    raise SystemExit(fail("ENVIRONMENT"))
os.environ.clear()
os.environ.update(environment)
argv = config["argv"]
if not argv or not all(isinstance(value, str) and "\x00" not in value for value in argv):
    raise SystemExit(fail("ARGV"))
try:
    child = subprocess.Popen(argv, env=environment, close_fds=True)
except OSError:
    raise SystemExit(fail("EXEC"))
sys.stderr.write(config["start_marker"] + "\n")
sys.stderr.flush()
raise SystemExit(child.wait())
"""


@dataclass
class SandboxSession:
    """Own process descriptors and close them after collection or launch failure."""

    source_fd: int | None = None
    config_fd: int | None = None
    info_read: int | None = None
    info_write: int | None = None
    process: subprocess.Popen[bytes] | None = None
    selector: selectors.BaseSelector | None = None
    start_marker: str = ""

    def start(self, check: CheckSpec, root: Path, policy: QualityPolicy) -> None:
        self.source_fd = os.open(
            root, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW
        )
        self.config_fd = os.memfd_create("m6-sandbox-config", os.MFD_CLOEXEC)
        self.start_marker = "M6_COMMAND_STARTED:" + secrets.token_hex(16)
        payload = json.dumps(
            _sandbox_config(check, self.start_marker, policy),
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("ascii")
        os.write(self.config_fd, payload)
        os.lseek(self.config_fd, 0, os.SEEK_SET)
        self.info_read, self.info_write = os.pipe2(os.O_CLOEXEC | os.O_NONBLOCK)
        command = _sandbox_command(
            policy, self.source_fd, self.config_fd, self.info_write
        )
        self.process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env={"PATH": "/usr/bin:/bin", "LC_ALL": "C", "HOME": "/nonexistent"},
            start_new_session=True,
            close_fds=True,
            pass_fds=(self.source_fd, self.config_fd, self.info_write),
            bufsize=0,
        )
        os.close(self.info_write)
        self.info_write = None
        assert self.process.stdout and self.process.stderr and self.process.stdin
        for stream in (self.process.stdout, self.process.stderr):
            os.set_blocking(stream.fileno(), False)
        self.selector = selectors.DefaultSelector()
        self.selector.register(self.info_read, selectors.EVENT_READ, "info")
        self.selector.register(self.process.stdout, selectors.EVENT_READ, "stdout")
        self.selector.register(self.process.stderr, selectors.EVENT_READ, "stderr")

    def close(self) -> None:
        if self.selector is not None:
            self.selector.close()
        if self.process is not None:
            for stream in (
                self.process.stdin,
                self.process.stdout,
                self.process.stderr,
            ):
                if stream is not None:
                    try:
                        stream.close()
                    except OSError:
                        pass
        for descriptor in (
            self.source_fd,
            self.config_fd,
            self.info_read,
            self.info_write,
        ):
            if descriptor is not None:
                try:
                    os.close(descriptor)
                except OSError:
                    pass


def sandbox_available(policy: QualityPolicy) -> bool:
    binary = Path(policy.bubblewrap_binary)
    return (
        binary.is_file() and os.access(binary, os.X_OK) and hasattr(os, "memfd_create")
    )


def _sandbox_config(
    check: CheckSpec, marker: str, policy: QualityPolicy
) -> dict[str, object]:
    return {
        "argv": list(check.argv),
        "cwd": check.cwd,
        "start_marker": marker,
        "environment": list(_BASE_ENVIRONMENT.items()) + list(policy.environment),
        "limits": {
            "address_space": policy.max_address_space_bytes,
            "cpu_seconds": policy.max_cpu_seconds,
            "file_size": policy.max_workspace_bytes,
        },
    }


def _sandbox_command(
    policy: QualityPolicy, source_fd: int, config_fd: int, info_write: int
) -> list[str]:
    return [
        policy.bubblewrap_binary,
        "--unshare-all",
        "--die-with-parent",
        "--new-session",
        "--clearenv",
        "--cap-drop",
        "ALL",
        "--ro-bind",
        "/usr",
        "/usr",
        "--symlink",
        "usr/bin",
        "/bin",
        "--symlink",
        "usr/lib",
        "/lib",
        "--symlink",
        "usr/lib",
        "/lib64",
        "--proc",
        "/proc",
        "--dev",
        "/dev",
        "--dir",
        "/home",
        "--dir",
        "/home/runner",
        "--dir",
        "/run",
        "--size",
        str(policy.max_tmp_bytes),
        "--tmpfs",
        "/tmp",
        "--size",
        str(policy.max_workspace_bytes),
        "--tmpfs",
        "/workspace",
        "--dir",
        "/source",
        "--ro-bind-fd",
        str(source_fd),
        "/source",
        "--perms",
        "600",
        "--file",
        str(config_fd),
        "/run/m6-config.json",
        "--info-fd",
        str(info_write),
        "--chdir",
        "/",
        "--",
        "/usr/bin/python3",
        "-c",
        _LAUNCHER,
    ]
