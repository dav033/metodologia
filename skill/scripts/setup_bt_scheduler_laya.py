#!/usr/bin/env python3
"""Install and verify the pinned, user-local Laya runtime for Scheduler M2."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOCK = HERE / "bt_scheduler_decision" / "laya-requirements.lock"
UPSTREAM_COMMIT = "432312b36714d8889eba405507b37eda25257d9c"
PYTHON_VERSION = (3, 12, 14)
TORCH_VERSION = "2.14.0+cu132"
CHECKPOINTS = {
    "english": {
        "repo": "convaiinnovations/laya",
        "revision": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851",
        "sha256": "891102d372688fc2a094dac56a384bc537b87c63f21f9f3dac0be2b7cbc8d86c",
        "size": 842_609_210,
    },
    "multilingual": {
        "repo": "convaiinnovations/laya-multilingual",
        "revision": "e4e9ddf21a7b1903b7acffd8814ad4307bf63a67",
        "sha256": "9d628fd971b700382ac6f65920a86f149777b2e748e0c955fb3b19695aa8f204",
        "size": 643_835_514,
    },
    "typed-decisions": {
        "repo": "convaiinnovations/laya-typed-decisions",
        "revision": "1a793eb568e6718f15941d08f85432581df534e3",
        "sha256": "4fa56de72383a9d3efa9cfa78955733c81b9fc8067a587ca4beb82c78107a24e",
        "size": 842_609_220,
    },
}
CHECKPOINT_FILES = (
    "encoder/config.json",
    "model.safetensors",
    "rl_agent_config.json",
    "tokenizer/tokenizer.json",
    "tokenizer/tokenizer_config.json",
)


def default_root() -> Path:
    configured = os.environ.get("BT_SCHEDULER_LAYA_HOME")
    return Path(configured).expanduser() if configured else Path.home() / ".local/share/bt-scheduler-laya"


def private_directory(path: Path) -> None:
    if path.is_symlink():
        raise RuntimeError(f"refusing symlink directory: {path}")
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    if not path.is_dir():
        raise RuntimeError(f"not a directory: {path}")
    os.chmod(path, 0o700)


def resolve_uv() -> str:
    executable = shutil.which("uv")
    if executable:
        return executable
    fallback = Path.home() / ".local/bin/uv"
    if fallback.is_file() and os.access(fallback, os.X_OK):
        return str(fallback)
    raise RuntimeError("uv is required; install it in user space before running --install")


def run(command: list[str], *, env: dict[str, str] | None = None) -> None:
    subprocess.run(command, check=True, env=env)


def _contained_path(base: Path, relative: str, *, directory: bool) -> Path:
    """Return a real path beneath ``base``, rejecting symlinks in every component."""
    relative_path = Path(relative)
    if relative_path.is_absolute() or not relative_path.parts or any(part in {".", ".."} for part in relative_path.parts):
        raise RuntimeError(f"unsafe checkpoint path: {relative}")
    if base.is_symlink() or not base.is_dir():
        raise RuntimeError(f"checkpoint directory missing or unsafe: {base}")
    resolved_base = base.resolve(strict=True)
    current = base
    for part in relative_path.parts:
        current = current / part
        if current.is_symlink() or not current.exists():
            raise RuntimeError(f"checkpoint path missing or unsafe: {relative}")
    resolved = current.resolve(strict=True)
    try:
        resolved.relative_to(resolved_base)
    except ValueError as exc:
        raise RuntimeError(f"checkpoint path escapes its snapshot: {relative}") from exc
    expected_kind = current.is_dir() if directory else current.is_file()
    if not expected_kind:
        kind = "directory" if directory else "regular file"
        raise RuntimeError(f"checkpoint path is not a {kind}: {relative}")
    return current


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_checkpoints(root: Path) -> dict[str, dict[str, object]]:
    if root.is_symlink() or not root.is_dir():
        raise RuntimeError("Laya install root is missing or unsafe")
    checkpoints_root = root / "checkpoints"
    if checkpoints_root.is_symlink() or not checkpoints_root.is_dir():
        raise RuntimeError("checkpoint root is missing or unsafe")
    manifest_path = _contained_path(checkpoints_root, "manifest.json", directory=False)
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("checkpoint manifest is missing or invalid; run --install") from exc
    if not isinstance(manifest, dict) or manifest.get("schema_version") != 1 or \
            manifest.get("laya_source_commit") != UPSTREAM_COMMIT:
        raise RuntimeError("checkpoint manifest does not match the pinned Laya source")
    manifest_checkpoints = manifest.get("checkpoints")
    if not isinstance(manifest_checkpoints, dict):
        raise RuntimeError("checkpoint manifest entries are invalid")  # noqa: TRY004 - damaged install manifest.
    for name, spec in CHECKPOINTS.items():
        entry = manifest_checkpoints.get(name)
        if not isinstance(entry, dict) or \
                (entry.get("revision"), entry.get("model_sha256"), entry.get("model_bytes")) != \
                (spec["revision"], spec["sha256"], spec["size"]):
            raise RuntimeError(f"checkpoint manifest entry mismatch: {name}")

    checked: dict[str, dict[str, object]] = {}
    for name, spec in CHECKPOINTS.items():
        directory = _contained_path(checkpoints_root, name, directory=True)
        for relative in CHECKPOINT_FILES:
            _contained_path(directory, relative, directory=False)
        weights = _contained_path(directory, "model.safetensors", directory=False)
        actual_size = weights.stat().st_size
        actual_digest = sha256_file(weights)
        if actual_size != spec["size"] or actual_digest != spec["sha256"]:
            raise RuntimeError(f"checkpoint integrity mismatch: {name}/model.safetensors")
        checked[name] = {"revision": spec["revision"], "model_bytes": actual_size, "sha256": actual_digest}
    return checked


def child_python(root: Path) -> Path:
    return root / "venv/bin/python"


def verify_runtime(root: Path) -> dict[str, object]:
    python = child_python(root)
    if not python.is_file():
        raise RuntimeError(f"isolated Python environment missing: {python}; run --install")
    probe = """
import importlib.metadata as metadata
import json
import sys
import torch
import laya
distribution = metadata.distribution("laya")
direct_url = json.loads(distribution.read_text("direct_url.json") or "{}")
cuda = torch.cuda.is_available()
device = None
if cuda:
    props = torch.cuda.get_device_properties(0)
    device = {"name": props.name, "total_memory": props.total_memory, "capability": list(props.major_minor) if hasattr(props, "major_minor") else [props.major, props.minor]}
print(json.dumps({
    "python": list(sys.version_info[:3]),
    "laya_version": distribution.version,
    "laya_commit": direct_url.get("vcs_info", {}).get("commit_id"),
    "torch_version": torch.__version__,
    "cuda_build": torch.version.cuda,
    "cuda_available": cuda,
    "cuda_device": device,
}, sort_keys=True))
"""
    try:
        result = subprocess.run([str(python), "-I", "-c", probe], check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or "").strip().splitlines()
        raise RuntimeError("isolated runtime probe failed" + (f": {detail[-1]}" if detail else "")) from exc
    try:
        details = json.loads(result.stdout.splitlines()[-1])
    except (IndexError, json.JSONDecodeError) as exc:
        raise RuntimeError("isolated runtime probe returned invalid output") from exc
    if tuple(details["python"]) != PYTHON_VERSION:
        raise RuntimeError(f"expected Python {'.'.join(map(str, PYTHON_VERSION))}, got {details['python']}")
    if details["laya_version"] != "0.4.7" or details["laya_commit"] != UPSTREAM_COMMIT:
        raise RuntimeError("installed Laya package does not match the pinned upstream commit")
    if details["torch_version"] != TORCH_VERSION or details["cuda_build"] != "13.2":
        raise RuntimeError("installed PyTorch build does not match the pinned CUDA wheel")
    return details


def download_checkpoints(root: Path) -> None:
    private_directory(root)
    checkpoints_root = root / "checkpoints"
    private_directory(checkpoints_root)
    probe = """
import json
import sys
from pathlib import Path
from huggingface_hub import snapshot_download
specs = json.loads(sys.argv[1])
root = Path(sys.argv[2])
patterns = ["encoder/config.json", "model.safetensors", "rl_agent_config.json",
            "tokenizer/tokenizer.json", "tokenizer/tokenizer_config.json"]
for name, spec in specs.items():
    destination = root / name
    destination.mkdir(mode=0o700, parents=True, exist_ok=True)
    snapshot_download(repo_id=spec["repo"], revision=spec["revision"],
                      local_dir=str(destination), allow_patterns=patterns)
    print(name, spec["revision"], flush=True)
"""
    specs = json.dumps(CHECKPOINTS, sort_keys=True)
    run([str(child_python(root)), "-I", "-c", probe, specs, str(checkpoints_root)])
    entries = {
        name: {
            "repo": spec["repo"],
            "revision": spec["revision"],
            "model_sha256": spec["sha256"],
            "model_bytes": spec["size"],
        }
        for name, spec in CHECKPOINTS.items()
    }
    manifest = {
        "schema_version": 1,
        "laya_source_commit": UPSTREAM_COMMIT,
        "installed_at_utc": datetime.now(UTC).isoformat(),
        "checkpoints": entries,
    }
    descriptor, temporary_name = tempfile.mkstemp(prefix="manifest-", dir=checkpoints_root)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(manifest, stream, sort_keys=True, separators=(",", ":"))
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, checkpoints_root / "manifest.json")
    finally:
        temporary.unlink(missing_ok=True)
    verify_checkpoints(root)


def install(root: Path) -> None:
    private_directory(root)
    if not LOCK.is_file():
        raise RuntimeError(f"pinned requirements lock missing: {LOCK}")
    python = child_python(root)
    if not python.exists():
        run([resolve_uv(), "venv", "--python", ".".join(map(str, PYTHON_VERSION)), str(root / "venv")])
    run([resolve_uv(), "pip", "sync", "--python", str(python), str(LOCK)])
    verify_runtime(root)
    download_checkpoints(root)
    check(root)


def check(root: Path) -> None:
    runtime = verify_runtime(root)
    checkpoints = verify_checkpoints(root)
    result = {"runtime": runtime, "checkpoints": checkpoints, "offline_ready": True}
    print(json.dumps(result, indent=2, sort_keys=True))
    if not runtime["cuda_available"]:
        print("CUDA unavailable; the pinned PyTorch environment remains usable on CPU.", file=sys.stderr)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    operation = parser.add_mutually_exclusive_group(required=True)
    operation.add_argument("--install", action="store_true", help="install the isolated environment and checkpoints")
    operation.add_argument("--check", action="store_true", help="verify pins and local checkpoint hashes offline")
    parser.add_argument("--root", type=Path, default=default_root(), help="private user-local install directory")
    args = parser.parse_args()
    try:
        if args.install:
            install(args.root.expanduser())
        else:
            check(args.root.expanduser())
    except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"Laya setup failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
