#!/usr/bin/env python3
"""Install the pinned, measured RTK build without hooks or elevated privileges."""
from __future__ import annotations

import hashlib
import io
import os
from pathlib import Path
import platform
import tempfile
import tarfile
import urllib.request

VERSION = "0.51.0"
ASSET = "rtk-x86_64-unknown-linux-musl.tar.gz"
URL = f"https://github.com/rtk-ai/rtk/releases/download/v{VERSION}/{ASSET}"
ARCHIVE_SHA256 = "5028d3b19a8f0990d30fec9fbb07e32782bc5698e618fb1861aad8a9ccba4eb5"
BINARY_SHA256 = "b947215511bfd8f5f6eb12c6b6d4a9f70b72e9ce37442cfa4df2352b033cd0ea"
MAX_BYTES = 32 * 1024 * 1024


def verified_binary(data: bytes) -> bytes:
    if hashlib.sha256(data).hexdigest() != ARCHIVE_SHA256:
        raise ValueError("RTK archive checksum mismatch; nothing installed")
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
        members = [m for m in archive.getmembers() if m.isfile() and Path(m.name).name == "rtk"]
        if len(members) != 1 or not 0 < members[0].size <= MAX_BYTES:
            raise ValueError("RTK archive must contain exactly one bounded regular binary")
        stream = archive.extractfile(members[0])
        if stream is None:
            raise ValueError("RTK archive binary is unreadable")
        with stream:
            binary = stream.read(MAX_BYTES + 1)
    if hashlib.sha256(binary).hexdigest() != BINARY_SHA256:
        raise ValueError("RTK binary checksum mismatch; nothing installed")
    return binary


def install(destination: Path | None = None) -> Path:
    if platform.system() != "Linux" or platform.machine().lower() not in {"x86_64", "amd64"}:
        raise RuntimeError("Pinned RTK installer supports Linux x86_64; use upstream packages on other platforms")
    destination = destination if destination is not None else Path.home() / ".local" / "bin" / "rtk"
    if destination.is_symlink():
        raise FileExistsError(f"RTK destination is a symlink; preserved: {destination}")
    if destination.exists():
        if hashlib.sha256(destination.read_bytes()).hexdigest() != BINARY_SHA256:
            raise FileExistsError(f"Different RTK binary already exists; preserved: {destination}")
        if destination.stat().st_mode & 0o111 != 0o111:
            raise PermissionError(f"Verified RTK lacks executable permissions; preserved: {destination}")
        return destination
    request = urllib.request.Request(URL, headers={"User-Agent": "metodologia-rtk-installer"})
    with urllib.request.urlopen(request, timeout=30) as response:
        data = response.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError("RTK download exceeds size limit; nothing installed")
    binary = verified_binary(data)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=".rtk-", dir=destination.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "wb") as output:
            output.write(binary)
        temporary.chmod(0o755)
        # A same-filesystem hard link publishes atomically and never replaces a concurrent destination.
        os.link(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)
    return destination


if __name__ == "__main__":
    print(f"RTK {VERSION}: {install()}")
