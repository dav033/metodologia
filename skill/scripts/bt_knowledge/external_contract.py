"""Validation and canonical forms for research-claims/1."""
from __future__ import annotations

import hashlib
import re
import unicodedata
from urllib.parse import urlsplit

from .contract import KnowledgeError, _secret_scan


KINDS = {"package_version", "api_behavior", "price", "license", "changelog", "docs", "security_advisory", "other"}
CONFIDENCE = {"high", "medium", "low"}
INSTRUCTIONS = re.compile(
    r"(?:\b(?:sudo|curl|wget|chmod)\b|\brm\s+-[a-z]*r[a-z]*f\b|"
    r"\b(?:bash|sh|python|python3)\s+-c\b|\b(?:pip|pip3|npm|pnpm|yarn)\s+install\b|"
    r"\bgit\s+(?:clone|push|reset|checkout)\b|\bexport\s+[A-Z_]+=|\|\s*(?:sh|bash)\b|"
    r"```[^`]*(?:sh|bash|shell)[^`]*```|`[^`]*(?:sudo|curl|wget|chmod|rm\s+-|pip\s+install|npm\s+install)[^`]*`)",
    re.I | re.S,
)


def normalize_claim(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def claim_fingerprint(topic: str, claim: str) -> str:
    return hashlib.sha256((topic + "\0" + normalize_claim(claim)).encode("utf-8")).hexdigest()


def contains_instructions(value: str) -> bool:
    return bool(INSTRUCTIONS.search(value))


def _text(value: object, name: str, *, maximum: int = 2000, optional: bool = False) -> str | None:
    if optional and value is None:
        return None
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise KnowledgeError("INVALID_CLAIMS", f"{name} must be non-empty text of at most {maximum} characters")
    return value.strip()


def _source(raw: object) -> dict:
    if raw is None:
        return {"url": None, "canonical": None, "retrieved_at": None, "published": None,
                "locator": None, "excerpt": None}
    if not isinstance(raw, dict):
        raise KnowledgeError("INVALID_SOURCE", "source must be an object")
    url = _text(raw.get("url"), "source.url", maximum=2048, optional=True)
    canonical = _text(raw.get("canonical"), "source.canonical", maximum=2048, optional=True) or url
    for value in (url, canonical):
        if value is None:
            continue
        try:
            parsed = urlsplit(value)
            hostname = parsed.hostname
            port = parsed.port
        except ValueError:
            raise KnowledgeError("INVALID_SOURCE_URL", "source URL is malformed") from None
        if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.username or parsed.password:
            raise KnowledgeError("INVALID_SOURCE_URL", "source URLs must be absolute HTTP(S) URLs without credentials")
        hostname = hostname.lower() if hostname else ""
        if ":" in hostname and not hostname.startswith("["):
            hostname = f"[{hostname}]"
        if port is not None and not ((parsed.scheme == "https" and port == 443) or
                                     (parsed.scheme == "http" and port == 80)):
            hostname = f"{hostname}:{port}"
        if value == canonical:
            canonical = f"{parsed.scheme.lower()}://{hostname}{parsed.path.rstrip('/') or '/'}"
            if parsed.query:
                canonical += f"?{parsed.query}"
    retrieved = _text(raw.get("retrieved_at"), "source.retrieved_at", maximum=10, optional=True)
    if retrieved is not None:
        try:
            from datetime import date
            if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", retrieved):
                raise ValueError
            date.fromisoformat(retrieved)
        except ValueError:
            raise KnowledgeError("INVALID_RETRIEVAL_DATE", "retrieved_at must be YYYY-MM-DD") from None
    published = _text(raw.get("published"), "source.published", maximum=100, optional=True)
    locator = _text(raw.get("locator"), "source.locator", maximum=500, optional=True)
    excerpt = _text(raw.get("excerpt"), "source.excerpt", maximum=300, optional=True)
    return {"url": url, "canonical": canonical, "retrieved_at": retrieved, "published": published,
            "locator": locator, "excerpt": excerpt}


def validate_claims(raw: object) -> dict:
    try:
        _secret_scan(raw)
    except KnowledgeError:
        raise
    except (TypeError, ValueError):
        raise KnowledgeError("INVALID_CLAIMS", "input contains a value that is not JSON-compatible") from None
    if not isinstance(raw, dict) or raw.get("schema") != "research-claims/1":
        raise KnowledgeError("INVALID_CLAIMS", "expected schema research-claims/1")
    project = _text(raw.get("project"), "project", maximum=100)
    contributor = _text(raw.get("contributor"), "contributor", maximum=200)
    claims = raw.get("claims")
    contradictions = raw.get("contradictions", [])
    if not isinstance(claims, list) or not isinstance(contradictions, list):
        raise KnowledgeError("INVALID_CLAIMS", "claims and contradictions must be arrays")
    normalized = {"schema": "research-claims/1", "project": project, "contributor": contributor,
                  "claims": [], "contradictions": []}
    for row in claims:
        if not isinstance(row, dict):
            raise KnowledgeError("INVALID_CLAIMS", "claim entries must be objects")
        topic = _text(row.get("topic"), "topic", maximum=300)
        claim = _text(row.get("claim"), "claim", maximum=2000)
        kind = row.get("kind")
        confidence = row.get("confidence")
        if not isinstance(kind, str) or kind not in KINDS:
            raise KnowledgeError("INVALID_KIND", "kind is not supported")
        if not isinstance(confidence, str) or confidence not in CONFIDENCE:
            raise KnowledgeError("INVALID_CONFIDENCE", "confidence must be high, medium or low")
        subplans, independent_of = row.get("subplans", []), row.get("independent_of", [])
        if not isinstance(subplans, list) or any(not isinstance(v, str) or not v for v in subplans):
            raise KnowledgeError("INVALID_CLAIMS", "subplans must be an array of non-empty strings")
        if not isinstance(independent_of, list) or any(not isinstance(v, str) or not v for v in independent_of):
            raise KnowledgeError("INVALID_CLAIMS", "independent_of must be an array of non-empty strings")
        source = _source(row.get("source"))
        text_flag = contains_instructions(claim) or contains_instructions(source["excerpt"] or "")
        normalized["claims"].append({"topic": topic, "claim": claim, "normalized_claim": normalize_claim(claim),
            "fingerprint": claim_fingerprint(topic, claim), "kind": kind, "source": source,
            "confidence": confidence, "subplans": sorted(set(subplans)),
            "independent_of": sorted(set(independent_of)), "contains_instructions": text_flag})
    for row in contradictions:
        if not isinstance(row, dict):
            raise KnowledgeError("INVALID_CLAIMS", "contradiction entries must be objects")
        ref = _text(row.get("claim_ref"), "claim_ref", maximum=2000)
        reason = _text(row.get("reason"), "reason", maximum=1000)
        source = _source(row.get("source"))
        normalized["contradictions"].append({"claim_ref": ref, "reason": reason, "source": source,
            "contains_instructions": contains_instructions(reason) or contains_instructions(source["excerpt"] or "")})
    return normalized
