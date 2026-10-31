"""Images the owner attaches to a rejection in «Probar» (D-258), so the agents that act on it can see them.

Owner, 2026-10-31: «let me attach images to the rejection comments so the agents can see them».

- `parse_form`: the panel's rejection form is `multipart/form-data` (a file input, several files; the note keeps its
  textarea). A small parser for what browsers send: text fields and file parts, nothing else;
- `accept`: 0..N images, checked by their first bytes (PNG, JPEG, WebP, GIF), never by the client's name or MIME type,
  against `rejections.max_images` / `max_image_mb` / `max_total_mb` (bt_config). A refusal is one Spanish sentence and
  nothing is recorded;
- `store`: `<rdir>/evidence/owner-rejected/<SP>-v<N>/<n>-<sha256[:12]>.<ext>`, the bytes as sent. The client's file
  name is never used. Images in the bitácora stay on this machine (`.gitignore`, owner 2026-10-19): the decision entry
  with each path and digest is versioned, the bytes are not;
- `served`: the one route that serves them back (`/p/<project>/doc/requirements/<REQ-dir>/evidence/owner-rejected/…`),
  only files under that folder whose bytes are an accepted image, with the type their bytes say;
- `instructions`: what every agent that acts on the rejection reads: the absolute paths and the instruction to open them
  with its image-reading tool before reproducing or repairing.

Standard library only.
"""
from __future__ import annotations

import hashlib
import os
import re
import tempfile
from pathlib import Path

FOLDER = "evidence/owner-rejected"
TYPES = {"png": "image/png", "jpg": "image/jpeg", "webp": "image/webp", "gif": "image/gif"}
DEFAULT_LIMITS = {"max_images": 8, "max_image_mb": 10, "max_total_mb": 30}
FORM_OVERHEAD = 256 * 1024          # the note, the token and the part headers around the images
SAFE_SID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,40}")
STORED = re.compile(r"[1-9][0-9]{0,2}-[0-9a-f]{12}\.(?:png|jpg|webp|gif)")
SERVED = re.compile(r"requirements/[A-Za-z0-9][A-Za-z0-9._-]{0,120}/evidence/owner-rejected/"
                    r"[A-Za-z0-9][A-Za-z0-9._-]{0,60}/[1-9][0-9]{0,2}-[0-9a-f]{12}\.(?:png|jpg|webp|gif)")


class Refused(ValueError):
    """The attachments cannot be accepted; the message is the owner's (Spanish)."""


def limits() -> dict[str, int]:
    try:
        import bt_config
        got = {k: bt_config.get(f"rejections.{k}", v) for k, v in DEFAULT_LIMITS.items()}
    except Exception:  # noqa: BLE001 - an unreadable configuration keeps the defaults
        got = dict(DEFAULT_LIMITS)
    return {k: int(v) if isinstance(v, int) and not isinstance(v, bool) and v > 0 else DEFAULT_LIMITS[k]
            for k, v in got.items()}


def max_body() -> int:
    """The largest rejection form the server reads (every image at most, plus the fields around them)."""
    lim = limits()
    return min(lim["max_total_mb"], lim["max_images"] * lim["max_image_mb"]) * 1024 * 1024 + FORM_OVERHEAD


def sniff(data: bytes) -> str:
    """The image type the bytes themselves say ("png", "jpg", "webp", "gif"), or ""."""
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if data[:3] == b"\xff\xd8\xff":
        return "jpg"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "gif"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    return ""


# ------------------------------------------------------------------ multipart/form-data

_PARAM = re.compile(r';\s*([A-Za-z0-9_*-]+)\s*=\s*(?:"((?:[^"\\]|\\.)*)"|([^;]*))')


def _params(header: str) -> dict[str, str]:
    return {m.group(1).lower(): (m.group(2) if m.group(2) is not None else m.group(3).strip()) for m in _PARAM.finditer(header)}


def parse_form(content_type: str, body: bytes, max_parts: int = 64) -> tuple[dict[str, str], list[tuple[str, bytes]]]:
    """Text fields (first value of each name) and file parts `(client name, bytes)` of a multipart/form-data body.
    Malformed input gives what could be read (the token check then refuses a form without its token)."""
    found = re.search(r'boundary=(?:"([^"]{1,200})"|([^;\s]{1,200}))', content_type or "", re.I)
    if not found:
        return {}, []
    boundary = b"--" + (found.group(1) or found.group(2)).encode("latin-1", "replace")
    fields: dict[str, str] = {}
    files: list[tuple[str, bytes]] = []
    chunks = (b"\r\n" + body).split(b"\r\n" + boundary)
    for chunk in chunks[1:max_parts + 1]:
        if chunk.startswith(b"--"):
            break
        head, sep, data = chunk.partition(b"\r\n\r\n")
        if not sep:
            continue
        headers = {}
        for line in head.decode("utf-8", "replace").split("\r\n"):
            name, colon, value = line.partition(":")
            if colon:
                headers[name.strip().lower()] = value.strip()
        disposition = headers.get("content-disposition", "")
        if not disposition.lower().startswith("form-data"):
            continue
        params = _params(disposition)
        name = params.get("name", "")
        if not name:
            continue
        if "filename" in params:
            if params["filename"] or data:          # an empty file input sends a nameless empty part: nothing chosen
                files.append((params["filename"], data))
        elif name not in fields:
            fields[name] = data.decode("utf-8", "replace")
    return fields, files


# ------------------------------------------------------------------ checking and storing

def _label(name: str, index: int) -> str:
    clean = re.sub(r"[^\w .()-]+", "", os.path.basename(str(name or "")))[:60].strip()
    return f"«{clean}»" if clean else f"la imagen {index}"


def accept(items: list[tuple[str, bytes]]) -> list[dict]:
    """The images to store, each {"ext", "type", "sha256", "bytes", "data"}; raises Refused with the owner's message."""
    lim = limits()
    items = [(n, d) for n, d in items or [] if d]
    if len(items) > lim["max_images"]:
        raise Refused(f"Adjuntaste {len(items)} imágenes; el máximo es {lim['max_images']} por rechazo. Quita alguna y "
                      "vuelve a rechazar: no guardé nada.")
    out, total = [], 0
    for i, (name, data) in enumerate(items, 1):
        ext = sniff(data)
        if not ext:
            raise Refused(f"{_label(name, i)} no es una imagen PNG, JPEG, WebP ni GIF (lo miro por su contenido, no por "
                          "su nombre). Quítala y vuelve a rechazar: no guardé nada.")
        if len(data) > lim["max_image_mb"] * 1024 * 1024:
            raise Refused(f"{_label(name, i)} pesa {len(data) / 1048576:.1f} MB; el máximo es {lim['max_image_mb']} MB "
                          "por imagen. Redúcela y vuelve a rechazar: no guardé nada.")
        total += len(data)
        out.append({"ext": ext, "type": TYPES[ext], "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data),
                    "data": data})
    if total > lim["max_total_mb"] * 1024 * 1024:
        raise Refused(f"Las imágenes pesan {total / 1048576:.1f} MB en total; el máximo es {lim['max_total_mb']} MB por "
                      "rechazo. Quita alguna y vuelve a rechazar: no guardé nada.")
    return out


def from_paths(paths: list[str | Path]) -> list[tuple[str, bytes]]:
    """The CLI's `--image` files, read once each (too large ones are refused before reading)."""
    lim, out = limits(), []
    for i, p in enumerate(paths or [], 1):
        path = Path(p).expanduser()
        try:
            if path.stat().st_size > lim["max_image_mb"] * 1024 * 1024:
                raise Refused(f"{path} pesa más de {lim['max_image_mb']} MB, el máximo por imagen: no guardé nada.")
            out.append((path.name, path.read_bytes()))
        except OSError as exc:
            raise Refused(f"No puedo leer {path} ({exc.strerror or exc}): no guardé nada.") from exc
    return out


def folder(rdir: Path, sid: str, version: object) -> Path:
    if not SAFE_SID.fullmatch(str(sid)) or not re.fullmatch(r"[0-9]{1,6}", str(version)):
        raise Refused("Subplan o versión no válidos para guardar imágenes.")
    return Path(rdir) / FOLDER / f"{sid}-v{version}"


def store(rdir: Path, sid: str, version: object, images: list[dict]) -> list[dict]:
    """Write the accepted images (atomically, the bytes as sent) and return their records for the decision entry:
    {"path" (relative to the requirement), "sha256", "type", "bytes"}."""
    if not images:
        return []
    target = folder(rdir, sid, version)
    target.mkdir(parents=True, exist_ok=True)
    out = []
    for n, img in enumerate(images, 1):
        name = f"{n}-{img['sha256'][:12]}.{img['ext']}"
        path = target / name
        if not (path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == img["sha256"]):
            fd, tmp = tempfile.mkstemp(prefix=".upload.", dir=target)
            try:
                with os.fdopen(fd, "wb") as stream:
                    stream.write(img["data"])
                os.replace(tmp, path)
            finally:
                if os.path.exists(tmp):
                    os.unlink(tmp)
        out.append({"path": path.relative_to(Path(rdir)).as_posix(), "sha256": img["sha256"], "type": img["type"],
                    "bytes": img["bytes"]})
    return out


def records(dec: dict) -> list[dict]:
    """The attachments of a decision entry that look like ours (anything else in the file is ignored)."""
    out = []
    for item in (dec or {}).get("attachments") or []:
        if isinstance(item, dict) and isinstance(item.get("path"), str) and isinstance(item.get("sha256"), str) and \
                item["path"].startswith(FOLDER + "/") and STORED.fullmatch(item["path"].rsplit("/", 1)[-1]) and \
                ".." not in item["path"].split("/"):
            out.append(item)
    return out


def digests(dec: dict) -> list[str]:
    return sorted(str(a["sha256"]) for a in records(dec))


def absolute(rdir: Path, dec: dict) -> list[Path]:
    return [Path(rdir).resolve() / a["path"] for a in records(dec)]


def project_relative(rdir: Path, dec: dict) -> list[str]:
    """Paths from the project folder (`requirements/<REQ-dir>/evidence/…`): what PENDING.md and the web links use."""
    return [f"requirements/{Path(rdir).name}/{a['path']}" for a in records(dec)]


def instructions(paths: list) -> list[str]:
    """For every agent that acts on the rejection: the images and how to look at them. Empty without attachments."""
    if not paths:
        return []
    return [f"The owner attached {len(paths)} image(s) to this rejection. Open every one with your image-reading tool "
            "before you reproduce or change anything (Claude Code: the `Read` tool on the path; Codex: view the local "
            "image) — they show what he saw:", *[f"- `{p}`" for p in paths]]


def markdown(rdir: Path, dec: dict, base: str = "") -> list[str]:
    """Markdown images for an evidence file under `<rdir>/evidence/owner-rejected/` (relative to that folder by
    default), so the web renders them."""
    return [f"![Imagen {i} del rechazo]({base}{a['path'][len(FOLDER) + 1:]})" for i, a in enumerate(records(dec), 1)]


def served(project_dir: Path, rel: str) -> tuple[Path, str] | None:
    """The stored image `rel` (from the project folder) and its type, or None: only that folder's names, inside the
    project, whose bytes are an accepted image."""
    if not SERVED.fullmatch(rel or ""):
        return None
    base = Path(project_dir).resolve()
    path = (base / rel).resolve()
    try:
        path.relative_to(base)
        with path.open("rb") as stream:
            ext = sniff(stream.read(16))
    except (ValueError, OSError):
        return None
    return (path, TYPES[ext]) if ext and path.is_file() else None


__all__ = ["FOLDER", "Refused", "accept", "absolute", "digests", "folder", "from_paths", "instructions", "limits",
           "markdown", "max_body", "parse_form", "project_relative", "records", "served", "sniff", "store"]
