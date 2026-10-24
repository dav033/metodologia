"""Ingest-only SQLite store for versioned external research claims."""
from __future__ import annotations

import json
import sqlite3
import time
from datetime import date, datetime, timezone
from pathlib import Path

from .contract import KnowledgeError, _secret_scan, canonical_json
from .external_contract import normalize_claim, validate_claims
from .freshness import claim_status
from .store import _connect


SCHEMA = """
CREATE TABLE IF NOT EXISTS external_claims (
 id INTEGER PRIMARY KEY, project TEXT NOT NULL, fingerprint TEXT NOT NULL, topic TEXT NOT NULL,
 claim TEXT NOT NULL, normalized_claim TEXT NOT NULL, kind TEXT NOT NULL, confidence TEXT NOT NULL,
 subplans_json TEXT NOT NULL, independent_of_json TEXT NOT NULL,
 contains_instructions INTEGER NOT NULL DEFAULT 0, disputed INTEGER NOT NULL DEFAULT 0,
 invalidated INTEGER NOT NULL DEFAULT 0, recorded_at TEXT NOT NULL,
 UNIQUE(project, fingerprint));
CREATE TABLE IF NOT EXISTS external_evidence (
 id INTEGER PRIMARY KEY, claim_id INTEGER NOT NULL REFERENCES external_claims(id),
 canonical_url TEXT NOT NULL, url TEXT, locator TEXT NOT NULL, retrieved_at TEXT, published TEXT,
 excerpt TEXT, contributors_json TEXT NOT NULL, side TEXT NOT NULL,
 contains_instructions INTEGER NOT NULL DEFAULT 0, recorded_at TEXT NOT NULL,
 UNIQUE(claim_id, canonical_url, locator, side));
CREATE TABLE IF NOT EXISTS external_contradictions (
 id INTEGER PRIMARY KEY, claim_id INTEGER NOT NULL REFERENCES external_claims(id),
 evidence_id INTEGER, reason TEXT NOT NULL, contributor TEXT NOT NULL,
 recorded_at TEXT NOT NULL, fingerprint TEXT NOT NULL UNIQUE);
CREATE TABLE IF NOT EXISTS external_history (
 id INTEGER PRIMARY KEY, project TEXT NOT NULL, claim_id INTEGER, event TEXT NOT NULL,
 payload_json TEXT NOT NULL, recorded_at TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS external_claim_topic_idx ON external_claims(project, topic, kind);
CREATE INDEX IF NOT EXISTS external_evidence_claim_idx ON external_evidence(claim_id, retrieved_at);
"""


def _open(db_path: str | Path) -> sqlite3.Connection:
    db = _connect(db_path)
    db.executescript(SCHEMA)
    return db


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _source_key(source: dict) -> tuple[str, str]:
    return source["canonical"] or "", source["locator"] or ""


def _add_evidence(db: sqlite3.Connection, claim_id: int, source: dict, contributor: str,
                  side: str, flagged: bool) -> tuple[int | None, bool, bool]:
    canonical_url, locator = _source_key(source)
    row = db.execute("SELECT id, contributors_json, retrieved_at FROM external_evidence "
                     "WHERE claim_id=? AND canonical_url=? AND locator=? AND side=?",
                     (claim_id, canonical_url, locator, side)).fetchone()
    if row:
        contributors = json.loads(row["contributors_json"])
        if contributor not in contributors:
            contributors.append(contributor)
            db.execute("UPDATE external_evidence SET contributors_json=? WHERE id=?",
                       (canonical_json(sorted(contributors)), row["id"]))
        existing_date = date.fromisoformat(row["retrieved_at"]) if row["retrieved_at"] else None
        incoming_date = date.fromisoformat(source["retrieved_at"]) if source["retrieved_at"] else None
        if incoming_date and (existing_date is None or incoming_date > existing_date):
            db.execute("UPDATE external_evidence SET url=?,retrieved_at=?,published=?,excerpt=?,"
                       "contains_instructions=? WHERE id=?",
                       (source["url"], source["retrieved_at"], source["published"], source["excerpt"],
                        int(flagged), row["id"]))
            return row["id"], False, True
        return row["id"], False, False
    cursor = db.execute("INSERT INTO external_evidence(claim_id,canonical_url,url,locator,retrieved_at,published,"
                        "excerpt,contributors_json,side,contains_instructions,recorded_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                        (claim_id, canonical_url, source["url"], locator, source["retrieved_at"], source["published"],
                         source["excerpt"], canonical_json([contributor]), side, int(flagged), _now()))
    return cursor.lastrowid, True, False


def ingest_claims(db_path: str | Path, raw: object) -> dict:
    """Validate and merge research claims; repeated sources do not add evidence rows."""
    item = validate_claims(raw)
    db = _open(db_path)
    counts = {"added": 0, "claims_added": 0, "evidence_added": 0, "contradictions_added": 0,
              "duplicates_avoided": 0}
    try:
        db.execute("BEGIN IMMEDIATE")
        project, contributor = item["project"], item["contributor"]
        for claim in item["claims"]:
            db.execute("INSERT OR IGNORE INTO external_claims(project,fingerprint,topic,claim,normalized_claim,kind,"
                       "confidence,subplans_json,independent_of_json,contains_instructions,recorded_at) "
                       "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                       (project, claim["fingerprint"], claim["topic"], claim["claim"], claim["normalized_claim"],
                        claim["kind"], claim["confidence"], canonical_json(claim["subplans"]),
                        canonical_json(claim["independent_of"]), int(claim["contains_instructions"]), _now()))
            row = db.execute("SELECT id, subplans_json, contains_instructions FROM external_claims "
                             "WHERE project=? AND fingerprint=?", (project, claim["fingerprint"])).fetchone()
            if db.execute("SELECT changes()").fetchone()[0]:
                counts["claims_added"] += 1
                counts["added"] += 1
                db.execute("INSERT INTO external_history(project,claim_id,event,payload_json,recorded_at) "
                           "VALUES(?,?,?,?,?)", (project, row["id"], "claim_added", "{}", _now()))
            merged_subplans = sorted(set(json.loads(row["subplans_json"])) | set(claim["subplans"]))
            db.execute("UPDATE external_claims SET subplans_json=?,contains_instructions=? WHERE id=?",
                       (canonical_json(merged_subplans), int(bool(row["contains_instructions"] or
                                                                  claim["contains_instructions"])), row["id"]))
            evidence_id, added, refreshed = _add_evidence(db, row["id"], claim["source"], contributor, "claim",
                                                          claim["contains_instructions"])
            if added:
                counts["evidence_added"] += 1
                counts["added"] += 1
                db.execute("UPDATE external_claims SET invalidated=0 WHERE id=?", (row["id"],))
                db.execute("INSERT INTO external_history(project,claim_id,event,payload_json,recorded_at) "
                           "VALUES(?,?,?,?,?)", (project, row["id"], "evidence_added",
                           canonical_json({"canonical_url": claim["source"]["canonical"],
                                           "locator": claim["source"]["locator"]}), _now()))
            elif refreshed:
                db.execute("UPDATE external_claims SET invalidated=0 WHERE id=?", (row["id"],))
                db.execute("INSERT INTO external_history(project,claim_id,event,payload_json,recorded_at) "
                           "VALUES(?,?,?,?,?)", (project, row["id"], "evidence_refreshed",
                           canonical_json({"evidence_id": evidence_id,
                                           "retrieved_at": claim["source"]["retrieved_at"]}), _now()))
            else:
                counts["duplicates_avoided"] += 1
        for contradiction in item["contradictions"]:
            matches = db.execute("SELECT id,fingerprint,claim FROM external_claims WHERE project=? AND "
                                 "(fingerprint=? OR normalized_claim=?)",
                                 (project, contradiction["claim_ref"],
                                  normalize_claim(contradiction["claim_ref"]))).fetchall()
            if not matches:
                raise KnowledgeError("UNKNOWN_CLAIM_REF", "contradiction does not identify a stored claim")
            if len(matches) > 1:
                raise KnowledgeError("AMBIGUOUS_CLAIM_REF", "contradiction text identifies multiple claims")
            row = matches[0]
            evidence_id, evidence_added, _ = _add_evidence(db, row["id"], contradiction["source"], contributor,
                                                            "contradiction", contradiction["contains_instructions"])
            fp = f"{row['fingerprint']}:{_source_key(contradiction['source'])}:{contradiction['reason']}"
            cursor = db.execute("INSERT OR IGNORE INTO external_contradictions(claim_id,evidence_id,reason,contributor,"
                                "recorded_at,fingerprint) VALUES(?,?,?,?,?,?)",
                                (row["id"], evidence_id, contradiction["reason"], contributor, _now(), fp))
            if cursor.rowcount:
                counts["contradictions_added"] += 1
                counts["added"] += 1
                db.execute("UPDATE external_claims SET disputed=1,contains_instructions=MAX(contains_instructions,?) "
                           "WHERE id=?", (int(contradiction["contains_instructions"]), row["id"]))
                db.execute("INSERT INTO external_history(project,claim_id,event,payload_json,recorded_at) "
                           "VALUES(?,?,?,?,?)", (project, row["id"], "contradiction_added",
                           canonical_json({"reason": contradiction["reason"], "evidence_added": evidence_added}), _now()))
        db.commit()
        return counts
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def _row_status(db: sqlite3.Connection, row: sqlite3.Row, as_of: date | None = None) -> tuple[str, list[dict]]:
    evidence_rows = db.execute("SELECT * FROM external_evidence WHERE claim_id=? ORDER BY retrieved_at,canonical_url,locator",
                               (row["id"],)).fetchall()
    evidence = []
    retrieval_dates = []
    for ev in evidence_rows:
        retrieval = ev["retrieved_at"]
        if ev["side"] == "claim" and ev["canonical_url"] and retrieval:
            retrieval_dates.append(retrieval)
        item = {"url": ev["url"], "canonical": ev["canonical_url"] or None,
                "retrieved_at": retrieval, "published": ev["published"], "locator": ev["locator"] or None,
                "excerpt": ev["excerpt"], "contributors": json.loads(ev["contributors_json"]),
                "side": ev["side"], "contains_instructions": bool(ev["contains_instructions"])}
        evidence.append(item)
    status = claim_status(row["kind"], retrieval_dates, disputed=bool(row["disputed"]),
                          invalidated=bool(row["invalidated"]), as_of=as_of)
    return status, evidence


def query_claims(db_path: str | Path, project: str, *, topic: str | None = None, kind: str | None = None,
                 facts_only: bool = False, as_of: date | None = None) -> list[dict]:
    """Return claims with evidence provenance and an explicit freshness status."""
    if kind is not None and kind not in {"package_version", "api_behavior", "price", "license", "changelog",
                                         "security_advisory", "docs", "other"}:
        raise KnowledgeError("INVALID_KIND", "kind is not supported")
    db = _open(db_path)
    try:
        sql = "SELECT * FROM external_claims WHERE project=?"
        params: list[object] = [project]
        if topic is not None:
            sql += " AND topic=?"
            params.append(topic)
        if kind is not None:
            sql += " AND kind=?"
            params.append(kind)
        sql += " ORDER BY topic,normalized_claim"
        result = []
        for row in db.execute(sql, params).fetchall():
            status, evidence = _row_status(db, row, as_of)
            if facts_only and status != "fresh":
                continue
            contradictions = db.execute("SELECT reason,contributor,recorded_at FROM external_contradictions "
                                        "WHERE claim_id=? ORDER BY id", (row["id"],)).fetchall()
            history = db.execute("SELECT event,payload_json,recorded_at FROM external_history WHERE claim_id=? "
                                 "ORDER BY id", (row["id"],)).fetchall()
            result.append({"topic": row["topic"], "claim": row["claim"], "kind": row["kind"],
                "fingerprint": row["fingerprint"], "confidence": row["confidence"],
                "subplans": json.loads(row["subplans_json"]),
                "independent_of": json.loads(row["independent_of_json"]), "status": status,
                "contains_instructions": bool(row["contains_instructions"]), "evidence": evidence,
                "contradictions": [dict(value) for value in contradictions],
                "history": [{"event": value["event"], "payload": json.loads(value["payload_json"]),
                             "recorded_at": value["recorded_at"]} for value in history]})
        return result
    finally:
        db.close()


def claims_dossier(db_path: str | Path, project: str, subplan: str, *, max_bytes: int = 12000,
                   as_of: date | None = None) -> str:
    """Render a byte-bounded Markdown dossier; unsafe embedded command text is omitted."""
    if not isinstance(max_bytes, int) or max_bytes < 256:
        raise KnowledgeError("INVALID_MAX_BYTES", "max-bytes must be an integer of at least 256")
    rows = [row for row in query_claims(db_path, project, as_of=as_of) if subplan in row["subplans"]]
    lines = [f"# Research dossier: {subplan}", "", "## Verified facts", ""]
    needs = []
    for row in rows:
        if row["status"] != "fresh":
            needs.append(row)
            continue
        if row["contains_instructions"]:
            lines.append(f"- **{row['topic']}** — (content omitted: contains_instructions)")
            continue
        lines.append(f"- **{row['topic']}** — {row['claim']} ({row['kind']}, {row['confidence']})")
        for ev in row["evidence"]:
            if ev["side"] == "claim":
                lines.append(f"  - Source: {ev['canonical'] or '(no URL)'}; retrieved {ev['retrieved_at'] or '(unknown)'}; "
                             f"locator: {ev['locator'] or '(none)'}; contributor(s): {', '.join(ev['contributors'])}")
                if ev["excerpt"] and not ev["contains_instructions"]:
                    lines.append(f"  - Excerpt: {ev['excerpt']}")
    if not any(row["status"] == "fresh" for row in rows):
        lines.append("(No verified facts.)")
    lines.extend(["", "## Needs re-verification", ""])
    if not needs:
        lines.append("(None.)")
    for row in needs:
        claim = "(content omitted: contains_instructions)" if row["contains_instructions"] else row["claim"]
        lines.append(f"- **{row['topic']}** [{row['status']}] — {claim}")
    output = "\n".join(lines) + "\n"
    encoded = output.encode("utf-8")
    if len(encoded) <= max_bytes:
        return output
    marker = "\n… dossier truncated to byte limit\n"
    budget = max_bytes - len(marker.encode("utf-8"))
    clipped = encoded[:max(0, budget)].decode("utf-8", errors="ignore")
    return clipped + marker


def invalidate_claims(db_path: str | Path, project: str, topic: str, reason: str, *, kind: str | None = None) -> dict:
    """Mark matching claims stale while preserving the evidence and append-only history."""
    if not isinstance(reason, str) or not reason.strip():
        raise KnowledgeError("INVALID_REASON", "reason must be non-empty text")
    _secret_scan({"reason": reason})
    if kind is not None and kind not in {"package_version", "api_behavior", "price", "license", "changelog",
                                         "security_advisory", "docs", "other"}:
        raise KnowledgeError("INVALID_KIND", "kind is not supported")
    db = _open(db_path)
    try:
        db.execute("BEGIN IMMEDIATE")
        sql = "SELECT id FROM external_claims WHERE project=? AND topic=?"
        params: list[object] = [project, topic]
        if kind is not None:
            sql += " AND kind=?"
            params.append(kind)
        rows = db.execute(sql, params).fetchall()
        count = 0
        for row in rows:
            updated = db.execute("UPDATE external_claims SET invalidated=1 WHERE id=? AND invalidated=0", (row["id"],))
            if updated.rowcount:
                count += 1
                db.execute("INSERT INTO external_history(project,claim_id,event,payload_json,recorded_at) "
                           "VALUES(?,?,?,?,?)", (project, row["id"], "invalidated",
                           canonical_json({"topic": topic, "kind": kind, "reason": reason.strip()}), _now()))
        db.commit()
        return {"claims_matched": len(rows), "claims_marked": count}
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def claims_stats(db_path: str | Path, project: str) -> dict:
    db = _open(db_path)
    try:
        return {"project": project,
                "claims": db.execute("SELECT count(*) FROM external_claims WHERE project=?", (project,)).fetchone()[0],
                "evidence": db.execute("SELECT count(*) FROM external_evidence e JOIN external_claims c ON c.id=e.claim_id "
                                       "WHERE c.project=?", (project,)).fetchone()[0],
                "contradictions": db.execute("SELECT count(*) FROM external_contradictions x JOIN external_claims c "
                                             "ON c.id=x.claim_id WHERE c.project=?", (project,)).fetchone()[0],
                "history": db.execute("SELECT count(*) FROM external_history WHERE project=?", (project,)).fetchone()[0]}
    finally:
        db.close()


def external_benchmark(db_path: str | Path, *, claims: int = 20) -> dict:
    """Measure reused-dossier bytes/time against repeatedly ingesting raw offline research."""
    total_start = time.monotonic()
    raw = {"schema": "research-claims/1", "project": "benchmark", "contributor": "researcher:benchmark",
           "claims": [{"topic": f"library:pkg-{i}", "claim": f"Package {i} supports a stable API",
             "kind": "api_behavior", "source": {"url": f"https://docs.example.test/pkg-{i}",
             "canonical": f"https://docs.example.test/pkg-{i}", "retrieved_at": date.today().isoformat(),
             "locator": "API", "excerpt": "Stable API reference."}, "confidence": "high",
             "subplans": ["SP-BENCH"], "independent_of": []} for i in range(claims)], "contradictions": []}
    raw_bytes = len(json.dumps(raw, ensure_ascii=False).encode("utf-8"))
    start = time.monotonic()
    ingest_claims(db_path, raw)
    ingested_seconds = time.monotonic() - start
    start = time.monotonic()
    dossier = claims_dossier(db_path, "benchmark", "SP-BENCH", max_bytes=max(256, claims * 600))
    reused_seconds = time.monotonic() - start
    repeat_start = time.monotonic()
    for _ in range(3):
        ingest_claims(db_path, raw)
    reingest_seconds = time.monotonic() - repeat_start
    return {"claims": claims, "raw_research_bytes": raw_bytes, "dossier_bytes": len(dossier.encode("utf-8")),
            "first_ingest_seconds": round(ingested_seconds, 6), "dossier_seconds": round(reused_seconds, 6),
            "three_reingests_seconds": round(reingest_seconds, 6),
            "elapsed_seconds": round(time.monotonic() - total_start, 6)}
