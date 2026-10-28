"""Telemetry port: one JSON line per event, correlated project → req → plan revision → task → attempt → unit.

Values are filtered: keys that look like secrets are dropped and long strings are cut, so an event can be shared."""
from __future__ import annotations

import json
import os
import re
import threading
import time
from pathlib import Path

_SECRET = re.compile(r"(?i)token|secret|password|api_?key|authorization|cookie")


class JsonlTelemetry:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def emit(self, event: str, **fields: object) -> None:
        clean = {k: (v[:1000] if isinstance(v, str) else v) for k, v in fields.items() if not _SECRET.search(k)}
        line = json.dumps({"ts": time.time(), "event": event, "pid": os.getpid(), **clean}, default=str,
                          ensure_ascii=False, sort_keys=True)
        with self._lock, open(self.path, "a", encoding="utf-8") as stream:
            stream.write(line + "\n")

    def read(self) -> list[dict]:
        try:
            return [json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines() if line.strip()]
        except OSError:
            return []
