"""Read-only, bounded access to validated M4 metric snapshots."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from urllib.parse import quote

from bt_scheduler_monitor import MetricSample

MAX_METRIC_SNAPSHOTS = 100


def read_metric_snapshots(path: str | Path, *, limit: int = MAX_METRIC_SNAPSHOTS) -> tuple[MetricSample, ...]:
    """Return at most 100 validated samples from an existing M4 database without creating or mutating it."""
    if type(limit) is not int or limit < 1:
        raise ValueError("limit must be a positive integer")
    count = min(limit, MAX_METRIC_SNAPSHOTS)
    database_path = Path(path)
    if not database_path.is_file():
        return ()
    database_uri = f"file:{quote(str(database_path.resolve()), safe='/')}?mode=ro"
    connection = sqlite3.connect(database_uri, uri=True)
    connection.row_factory = sqlite3.Row
    try:
        try:
            rows = connection.execute(
                "SELECT observed_at,body FROM metric_samples "
                "ORDER BY julianday(observed_at) DESC,metric_id DESC LIMIT ?", (count,)
            ).fetchall()
        except sqlite3.OperationalError as exc:
            if "no such table" in str(exc):
                return ()
            raise
        samples = []
        for row in rows:
            sample = MetricSample.from_dict(json.loads(row["body"]))
            if row["observed_at"] != sample.observed_at:
                raise ValueError("metric_observed_at_mismatch")
            samples.append(sample)
        return tuple(samples)
    finally:
        connection.close()


__all__ = ["MAX_METRIC_SNAPSHOTS", "read_metric_snapshots"]
