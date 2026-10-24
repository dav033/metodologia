"""SQLite persistence, Git evidence checks, filtered reads and generated views."""
from __future__ import annotations

import json
import sqlite3
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from .contract import KnowledgeError, canonical_json, fingerprint, validate_delta


SCHEMA = """
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS entities (
 id INTEGER PRIMARY KEY, project TEXT NOT NULL, repository TEXT NOT NULL, entity_id TEXT NOT NULL,
 UNIQUE(project, repository, entity_id));
CREATE TABLE IF NOT EXISTS relations (
 id INTEGER PRIMARY KEY, project TEXT NOT NULL, repository TEXT NOT NULL, subject TEXT NOT NULL,
 relation TEXT NOT NULL, object TEXT NOT NULL, disputed INTEGER NOT NULL DEFAULT 0,
 UNIQUE(project, repository, subject, relation, object));
CREATE TABLE IF NOT EXISTS evidence (
 id INTEGER PRIMARY KEY, relation_id INTEGER NOT NULL REFERENCES relations(id), fingerprint TEXT NOT NULL UNIQUE,
 evidence_ref TEXT NOT NULL, observed_commit TEXT NOT NULL, contributor TEXT NOT NULL,
 contributors TEXT NOT NULL, status TEXT NOT NULL, verification TEXT NOT NULL,
 recorded_at TEXT NOT NULL, stale INTEGER NOT NULL DEFAULT 0, stale_reason TEXT);
CREATE TABLE IF NOT EXISTS conflicts (
 id INTEGER PRIMARY KEY, project TEXT NOT NULL, repository TEXT NOT NULL, relation_id INTEGER NOT NULL,
 peer_relation_id INTEGER, reason TEXT NOT NULL, evidence_json TEXT NOT NULL, fingerprint TEXT NOT NULL UNIQUE,
 recorded_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS history (
 id INTEGER PRIMARY KEY, project TEXT NOT NULL, repository TEXT NOT NULL, event TEXT NOT NULL,
 identity_json TEXT NOT NULL, payload_json TEXT NOT NULL, recorded_at TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS evidence_commit_idx ON evidence(observed_commit);
CREATE INDEX IF NOT EXISTS relation_scope_idx ON relations(project, repository, subject, object);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _connect(db_path: str | Path) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=30, isolation_level=None)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA busy_timeout=30000")
    deadline = time.monotonic() + 30
    while True:
        try:
            connection.executescript(SCHEMA)
            break
        except sqlite3.OperationalError as exc:
            if "locked" not in str(exc).lower() or time.monotonic() >= deadline:
                connection.close()
                raise
            time.sleep(0.05)
    return connection


def _git(repo_path: str | Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    try:
        return subprocess.run(["git", "-C", str(repo_path), *args], check=False, capture_output=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return subprocess.CompletedProcess(args, 128, b"", b"")


def _path_from_ref(ref: str) -> tuple[str | None, int | None, int | None]:
    if ref.startswith(("symbol:", "test:")):
        return None, None, None
    before, sep, suffix = ref.rpartition(":")
    if sep and suffix[:1].isdigit():
        first, dash, last = suffix.partition("-")
        return before, int(first), int(last) if dash else int(first)
    return ref, None, None


def _verify(repo_path: str | Path | None, commit: str, ref: str) -> str:
    path, start, end = _path_from_ref(ref)
    if repo_path is None or path is None:
        return "unverified"
    exists = _git(repo_path, "cat-file", "-e", f"{commit}:{path}")
    if exists.returncode != 0:
        return "unverified"
    if start is None:
        return "verified"
    contents = _git(repo_path, "show", f"{commit}:{path}")
    if contents.returncode != 0:
        return "unverified"
    try:
        lines = len(contents.stdout.decode("utf-8").splitlines())
    except UnicodeDecodeError:
        return "unverified"
    return "verified" if 1 <= start <= end <= lines else "unverified"


def ingest(db_path: str | Path, delta: object, repo_path: str | Path | None = None) -> dict:
    """Validate and atomically merge one delta; duplicate evidence is a no-op."""
    item = validate_delta(delta)
    db = _connect(db_path)
    counts = {"added": 0, "relations_added": 0, "evidence_added": 0, "conflicts_added": 0,
              "stale_marked": 0, "duplicates_avoided": 0}
    try:
        db.execute("BEGIN IMMEDIATE")
        project, repository, commit = item["project"], item["repository"], item["observed_commit"]
        for observation in item["observations"]:
            identity = (project, repository, observation["subject"], observation["relation"], observation["object"])
            db.execute("INSERT OR IGNORE INTO entities(project,repository,entity_id) VALUES(?,?,?)",
                       (project, repository, identity[2]))
            db.execute("INSERT OR IGNORE INTO entities(project,repository,entity_id) VALUES(?,?,?)",
                       (project, repository, identity[4]))
            before = db.total_changes
            db.execute("INSERT OR IGNORE INTO relations(project,repository,subject,relation,object) VALUES(?,?,?,?,?)", identity)
            relation_added = db.total_changes > before
            row = db.execute("SELECT id FROM relations WHERE project=? AND repository=? AND subject=? AND relation=? AND object=?",
                             identity).fetchone()
            if relation_added:
                counts["relations_added"] += 1
                db.execute("INSERT INTO history VALUES(NULL,?,?,?,?,?,?)",
                           (project, repository, "relation_added", canonical_json(identity[2:]), "{}", _now()))
            for ref in observation["evidence"]:
                fp = fingerprint(identity, ref, commit)
                verification = _verify(repo_path, commit, ref)
                present = db.execute("SELECT id, contributors FROM evidence WHERE fingerprint=?", (fp,)).fetchone()
                if present:
                    contributors = json.loads(present["contributors"])
                    if item["contributor"] not in contributors:
                        contributors.append(item["contributor"])
                        db.execute("UPDATE evidence SET contributors=? WHERE id=?",
                                   (canonical_json(sorted(contributors)), present["id"]))
                        counts["added"] += 1
                        db.execute("INSERT INTO history VALUES(NULL,?,?,?,?,?,?)",
                                   (project, repository, "contributor_added", canonical_json(identity[2:]),
                                    canonical_json({"fingerprint": fp, "contributor": item["contributor"]}), _now()))
                    else:
                        counts["duplicates_avoided"] += 1
                    continue
                db.execute("INSERT INTO evidence(relation_id,fingerprint,evidence_ref,observed_commit,contributor,contributors,status,verification,recorded_at) "
                           "VALUES(?,?,?,?,?,?,?,?,?)",
                           (row["id"], fp, ref, commit, item["contributor"], canonical_json([item["contributor"]]),
                            observation["status"], verification, _now()))
                db.execute("INSERT INTO history VALUES(NULL,?,?,?,?,?,?)",
                           (project, repository, "evidence_added", canonical_json(identity[2:]),
                            canonical_json({"fingerprint": fp, "status": observation["status"],
                                            "verification": verification}), _now()))
                counts["added"] += 1
                counts["evidence_added"] += 1
        for contradiction in item["contradictions"]:
            identity = (project, repository, contradiction["subject"], contradiction["relation"], contradiction["object"])
            db.execute("INSERT OR IGNORE INTO entities(project,repository,entity_id) VALUES(?,?,?)", (project, repository, identity[2]))
            db.execute("INSERT OR IGNORE INTO entities(project,repository,entity_id) VALUES(?,?,?)", (project, repository, identity[4]))
            before = db.total_changes
            db.execute("INSERT OR IGNORE INTO relations(project,repository,subject,relation,object) VALUES(?,?,?,?,?)", identity)
            if db.total_changes > before:
                counts["relations_added"] += 1
                db.execute("INSERT INTO history VALUES(NULL,?,?,?,?,?,?)",
                           (project, repository, "relation_added", canonical_json(identity[2:]), "{}", _now()))
            row = db.execute("SELECT id FROM relations WHERE project=? AND repository=? AND subject=? AND relation=? AND object=?", identity).fetchone()
            peers = db.execute("SELECT id FROM relations WHERE project=? AND repository=? AND subject=? AND relation=? AND object<>?",
                               identity).fetchall()
            db.execute("UPDATE relations SET disputed=1 WHERE id=?", (row["id"],))
            if peers:
                db.executemany("UPDATE relations SET disputed=1 WHERE id=?", [(peer["id"],) for peer in peers])
            refs = contradiction["evidence"]
            for ref in refs:
                fp = fingerprint(identity, ref, commit)
                present = db.execute("SELECT id, contributors FROM evidence WHERE fingerprint=?", (fp,)).fetchone()
                if present:
                    contributors = json.loads(present["contributors"])
                    if item["contributor"] not in contributors:
                        contributors.append(item["contributor"])
                        db.execute("UPDATE evidence SET contributors=? WHERE id=?",
                                   (canonical_json(sorted(contributors)), present["id"]))
                        counts["added"] += 1
                        db.execute("INSERT INTO history VALUES(NULL,?,?,?,?,?,?)",
                                   (project, repository, "contributor_added", canonical_json(identity[2:]),
                                    canonical_json({"fingerprint": fp, "contributor": item["contributor"]}), _now()))
                else:
                    db.execute("INSERT INTO evidence(relation_id,fingerprint,evidence_ref,observed_commit,contributor,contributors,status,verification,recorded_at) "
                               "VALUES(?,?,?,?,?,?,?,?,?)",
                               (row["id"], fp, ref, commit, item["contributor"], canonical_json([item["contributor"]]),
                                "observed", _verify(repo_path, commit, ref), _now()))
                    counts["evidence_added"] += 1
                    counts["added"] += 1
                    db.execute("INSERT INTO history VALUES(NULL,?,?,?,?,?,?)",
                               (project, repository, "evidence_added", canonical_json(identity[2:]),
                                canonical_json({"fingerprint": fp, "status": "observed", "source": "contradiction"}), _now()))
            conflict_peers = [peer["id"] for peer in peers] or [None]
            for peer_id in conflict_peers:
                conflict_fp = fingerprint(identity, canonical_json([peer_id, refs, contradiction["reason"]]), commit)
                cursor = db.execute("INSERT OR IGNORE INTO conflicts(project,repository,relation_id,peer_relation_id,reason,evidence_json,fingerprint,recorded_at) "
                                    "VALUES(?,?,?,?,?,?,?,?)",
                                    (project, repository, row["id"], peer_id, contradiction["reason"], canonical_json(refs), conflict_fp, _now()))
                if cursor.rowcount:
                    counts["conflicts_added"] += 1
                    counts["added"] += 1
                    db.execute("INSERT INTO history VALUES(NULL,?,?,?,?,?,?)",
                               (project, repository, "conflict_recorded", canonical_json(identity[2:]),
                                canonical_json({"peer_relation_id": peer_id, "reason": contradiction["reason"]}), _now()))
        for stale in item["stale"]:
            identity = (project, repository, stale["subject"], stale["relation"], stale["object"])
            row = db.execute("SELECT id FROM relations WHERE project=? AND repository=? AND subject=? AND relation=? AND object=?", identity).fetchone()
            if not row:
                continue
            updated = db.execute("UPDATE evidence SET stale=1,stale_reason=? WHERE relation_id=? AND stale=0",
                                 (stale["reason"], row["id"]))
            if updated.rowcount:
                counts["stale_marked"] += updated.rowcount
                counts["added"] += updated.rowcount
                db.execute("INSERT INTO history VALUES(NULL,?,?,?,?,?,?)",
                           (project, repository, "stale_marked", canonical_json(identity[2:]),
                            canonical_json({"reason": stale["reason"], "evidence_count": updated.rowcount}), _now()))
        db.commit()
        return counts
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def _unchanged(repo_path: str | Path, old: str, target: str, path: str) -> bool:
    result = _git(repo_path, "diff", "--quiet", old, target, "--", path)
    return result.returncode == 0


def query(db_path: str | Path, project: str, *, commit: str | None = None, area: str | None = None,
          status: str | None = None, repository: str | None = None, repo_path: str | Path | None = None) -> list[dict]:
    """Read relations filtered to one project and optionally revision, evidence area and status."""
    if commit is not None:
        if len(commit) != 40 or any(char not in "0123456789abcdefABCDEF" for char in commit):
            raise KnowledgeError("INVALID_COMMIT", "query commit must be a full 40-hex SHA")
        commit = commit.lower()
    db = _connect(db_path)
    try:
        sql = "SELECT r.*,e.evidence_ref,e.observed_commit,e.contributor,e.contributors,e.status AS knowledge_status,e.verification,e.recorded_at,e.stale,e.stale_reason " \
              "FROM relations r LEFT JOIN evidence e ON e.relation_id=r.id WHERE r.project=?"
        args: list[object] = [project]
        if repository:
            sql += " AND r.repository=?"
            args.append(repository)
        sql += " ORDER BY r.repository,r.subject,r.relation,r.object,e.observed_commit,e.evidence_ref"
        rows = db.execute(sql, args).fetchall()
        grouped: dict[int, dict] = {}
        for row in rows:
            relation = grouped.setdefault(row["id"], {"subject": row["subject"], "relation": row["relation"],
                "object": row["object"], "evidence": []})
            if row["disputed"]:
                relation["disputed"] = True
            if row["evidence_ref"] is None:
                continue
            ev = {"ref": row["evidence_ref"], "commit": row["observed_commit"],
                  "contributors": json.loads(row["contributors"]), "status": row["knowledge_status"],
                  "verification": row["verification"]}
            if row["stale"]:
                ev["stale"] = True
                ev["stale_reason"] = row["stale_reason"]
            if commit:
                if row["observed_commit"] == commit:
                    ev["validity"] = "current"
                elif repo_path and not row["stale"] and (path := _path_from_ref(row["evidence_ref"])[0]) and _unchanged(
                        repo_path, row["observed_commit"], commit, path):
                    ev["validity"] = f"unchanged_since:{row['observed_commit']}"
                else:
                    ev["validity"] = "historical"
            else:
                ev["validity"] = "unbounded"
            relation["evidence"].append(ev)
        result = []
        for relation in grouped.values():
            validities = {ev["validity"] for ev in relation["evidence"]}
            relation["validity"] = ("current" if "current" in validities else
                                     "historical" if "historical" in validities else
                                     next(iter(validities), "unverified"))
            labels = {relation["validity"]}
            labels.update(ev["status"] for ev in relation["evidence"])
            if relation.get("disputed", False):
                relation["status"] = "disputed"
                labels.add("disputed")
            if any(ev["verification"] == "unverified" for ev in relation["evidence"]):
                labels.add("unverified")
            if any(ev.get("stale") for ev in relation["evidence"]):
                labels.add("stale")
            if status and status not in labels and not any(status in (ev["status"], ev["verification"], ev["validity"])
                                                          for ev in relation["evidence"]):
                continue
            if area:
                entities = (relation["subject"], relation["object"])
                paths = [_path_from_ref(ev["ref"])[0] for ev in relation["evidence"]
                         if not ev["ref"].startswith(("symbol:", "test:"))]
                if not any(value.startswith(area) for value in entities + tuple(paths)):
                    continue
            result.append(relation)
        return result
    finally:
        db.close()


def stats(db_path: str | Path, project: str) -> dict:
    db = _connect(db_path)
    try:
        return {"project": project,
                "relations": db.execute("SELECT count(*) FROM relations WHERE project=?", (project,)).fetchone()[0],
                "evidence": db.execute("SELECT count(*) FROM evidence e JOIN relations r ON r.id=e.relation_id WHERE r.project=?", (project,)).fetchone()[0],
                "conflicts": db.execute("SELECT count(*) FROM conflicts WHERE project=?", (project,)).fetchone()[0],
                "stale": db.execute("SELECT count(*) FROM evidence e JOIN relations r ON r.id=e.relation_id WHERE r.project=? AND e.stale=1", (project,)).fetchone()[0],
                "history": db.execute("SELECT count(*) FROM history WHERE project=?", (project,)).fetchone()[0]}
    finally:
        db.close()


def export(db_path: str | Path, project: str, fmt: str, *, commit: str | None = None) -> str:
    rows = query(db_path, project, commit=commit)
    if fmt == "json":
        return json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    if fmt == "md":
        lines = [f"# Knowledge map: {project}", "", "| Subject | Relation | Object | Validity | Evidence |", "|---|---|---|---|---|"]
        for relation in rows:
            evidence = ", ".join("{} [{}/{}/{}]".format(item["ref"], item["status"], item["verification"],
                                                           item["validity"]) for item in relation["evidence"])
            lines.append(f"| {relation['subject']} | {relation['relation']} | {relation['object']} | "
                         f"{relation['validity']} | {evidence} |")
        return "\n".join(lines) + "\n"
    if fmt == "mermaid":
        lines = ["graph LR"]
        lines.extend(f'  {json.dumps(r["subject"])} -->|{r["relation"]} ({r["validity"]})| {json.dumps(r["object"])}'
                     for r in rows)
        return "\n".join(lines) + "\n"
    raise KnowledgeError("INVALID_FORMAT", "format must be md, mermaid or json")


def benchmark(db_path: str | Path, *, explorers: int = 3, observations: int = 40) -> dict:
    """Replay overlapping synthetic deltas and report compactness and deduplication."""
    start = time.monotonic()
    commit_a = "a" * 40
    commit_b = "b" * 40
    raw = []
    unique = max(1, observations // 2)
    for explorer in range(explorers):
        selected = range(observations) if explorer == 0 else range(unique)
        delta = {"schema": "knowledge-delta/1", "project": "benchmark", "repository": "synthetic",
                 "observed_commit": commit_a if explorer < explorers - 1 else commit_b,
                 "contributor": f"explorer:{explorer}", "observations": [
                     {"subject": f"module:m{i}", "relation": "CONSUMES", "object": f"contract:c{i}",
                      "status": "observed", "evidence": [f"src/m{i}.py:1"]} for i in selected]}
        if explorer == explorers - 1:
            delta["contradictions"] = [{"subject": "module:m0", "relation": "CONSUMES", "object": "contract:other",
                                        "evidence": ["src/other.py:1"], "reason": "synthetic contradiction"}]
        raw.append(json.dumps(delta, indent=2, ensure_ascii=False))
        ingest(db_path, delta)
    payload = export(db_path, "benchmark", "json", commit=commit_b)
    result = stats(db_path, "benchmark")
    return {"relations": result["relations"], "correct_relations": observations + 1,
            "duplicates_avoided": max(0, (observations + (explorers - 1) * unique) - observations),
            "stale_labelled": payload.count("historical"),
            "query_json_bytes": len(payload.encode()), "raw_delta_bytes": sum(len(value.encode()) for value in raw),
            "elapsed_seconds": round(time.monotonic() - start, 6)}
