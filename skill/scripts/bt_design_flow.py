"""Read durable design approval records as flow-bus events."""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path


def events(rdir: Path, project: str, after: int) -> list[dict]:
    try:
        records = json.loads((Path(rdir) / "design-approvals.json").read_text(encoding="utf-8")).get("approvals", {})
    except (OSError, UnicodeError, ValueError, AttributeError):
        return []
    out = []
    for index, (ref, record) in enumerate(sorted(records.items()), 1):
        if not isinstance(record, dict):
            continue
        try:
            at = dt.datetime.fromisoformat(record["when"]).timestamp()
        except (KeyError, TypeError, ValueError, OverflowError):
            continue
        ident = int(at * 1_000_000) * 1000 + index
        if ident <= after:
            continue
        status = record.get("status", "unknown")
        label = "aprobado" if status == "approved" else "cambios solicitados"
        req = Path(rdir).name
        if req.startswith("REQ-"):
            req = "-".join(req.split("-")[:2])
        out.append({"v": 1, "seq": f"design:{ident}", "ord": f"{at:018.6f}:design:{ident:010d}",
                    "at": dt.datetime.fromtimestamp(at, dt.UTC).isoformat(timespec="milliseconds"),
                    "at_epoch": at, "run": f"{project}/{req}", "task": None, "attempt": None,
                    "from": "owner", "to": "designer", "kind": "design_approval",
                    "summary": f"Contrato de diseño {ref}: {label}", "ref": {"store": "design", "id": ident},
                    "data": {"contract": ref, "state": status, "sha256": record.get("sha256"),
                             "via": record.get("via")}})
    return sorted(out, key=lambda item: item["ord"])
