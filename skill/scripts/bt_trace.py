"""Trace graph derived from the IDs the bitácora already uses — no database, no LLM, regenerated on demand.

Nodes: REQ (requirement), US / R (user stories, EARS requirements of a REQ), T (plan tasks), D (decisions),
P (pending items), C (commits that cite an ID), F (files those commits touched).
Edges: REQ→US/R (defines), T→R/US (covers), REQ→T (plans), D→D (supersedes), X→Y (mentions, from any doc),
C→REQ/T/D/P (refs, from commit messages / `Refs:` trailers), C→F (touches).
`lint()` finds drift: requirements no task covers, tasks covering nothing or unknown IDs, references to
superseded decisions, IDs mentioned but never defined, done requirements with unticked tasks.
"""
from __future__ import annotations

import re
import subprocess

from bt_core import *  # noqa: F403
from bt_core import _front

ID_RE = re.compile(r"\b(REQ-\d{3,}|D-\d{3,}|P-\d{3,})\b")
LOCAL_RE = re.compile(r"\b(US-\d+|R\d+|T\d+)\b")


def _clean(text: str) -> str:
    return re.sub(r"<!--.*?-->", "", text, flags=re.S)


def _read(f: Path) -> str:
    try:
        return _clean(f.read_text(encoding="utf-8"))
    except Exception:
        return ""


class Graph:
    def __init__(self, project: str):
        self.project = project
        self.nodes: dict[str, dict] = {}
        self.edges: list[dict] = []

    def node(self, nid: str, kind: str, label: str = "", **attrs) -> dict:
        n = self.nodes.setdefault(nid, {"id": nid, "type": kind, "label": label or nid})
        if label:
            n["label"] = label
        n.update({k: v for k, v in attrs.items() if v not in (None, "")})
        return n

    def edge(self, src: str, dst: str, kind: str) -> None:
        e = {"source": src, "target": dst, "type": kind}
        if src != dst and e not in self.edges:
            self.edges.append(e)

    def to_dict(self) -> dict:
        return {"project": self.project, "nodes": list(self.nodes.values()), "edges": self.edges}


# ---------------------------------------------------------------- builders

def _requirements(g: Graph, pdir: Path) -> None:
    for spec in sorted((pdir / "requirements").glob("REQ-*/SPEC.md")):
        rdir = spec.parent
        rid = req_id(rdir)
        text = _read(spec)
        title = re.search(r"^# (.+)$", text, re.M)
        g.node(rid, "REQ", title.group(1) if title else rid, status=_front(spec, "status"),
               path=spec.relative_to(pdir).as_posix())
        for m in re.finditer(r"^###\s+(US-\d+)\b[^\n]*?(?:—|-)\s*(.+)$", text, re.M):
            nid = f"{rid}/{m.group(1)}"
            g.node(nid, "US", f"{m.group(1)} {m.group(2).strip()}", req=rid)
            g.edge(rid, nid, "defines")
        for m in re.finditer(r"^\s*-\s+(R\d+)\.\s+(.+)$", text, re.M):
            nid = f"{rid}/{m.group(1)}"
            g.node(nid, "R", f"{m.group(1)} {m.group(2).strip()[:80]}", req=rid)
            g.edge(rid, nid, "defines")
        plan = rdir / "PLAN.md"
        if not plan.exists():
            continue
        g.nodes[rid]["plan"] = _front(plan, "status")
        for m in re.finditer(r"^\s*-\s+\[( |x|X)\]\s+(T\d+)\b(.*)$", _read(plan), re.M):
            tid = f"{rid}/{m.group(2)}"
            rest = m.group(3)
            what = re.split(r"\s·\s", rest.strip(" —-"))[0][:80]
            g.node(tid, "T", f"{m.group(2)} {what}", req=rid, done=m.group(1).lower() == "x",
                   repo=(re.search(r"\[([a-z][\w-]*)\]", rest) or [None, None])[1])
            g.edge(rid, tid, "plans")
            covers = re.search(r"covers:\s*([^·]+)", rest)
            g.nodes[tid]["covers"] = []
            for ref in re.findall(r"\b(US-\d+|R\d+)\b", covers.group(1) if covers else ""):
                g.nodes[tid]["covers"].append(f"{rid}/{ref}")
                g.edge(tid, f"{rid}/{ref}", "covers")


def _decisions(g: Graph, pdir: Path) -> None:
    text = _read(pdir / "DECISIONS.md")
    blocks = re.split(r"^(?=## D-\d{3,})", text, flags=re.M)
    for b in blocks:
        m = re.match(r"## (D-\d{3,})\s*[—\-·:]\s*(.+)", b)  # tolerate "—", "-", "·" and ":" separators
        if not m:
            continue
        status = re.search(r"\*\*Status:\*\*\s*([^\n·]+)", b)
        g.node(m.group(1), "D", f"{m.group(1)} {m.group(2).strip()}", status=status.group(1).strip() if status else "")
        for old in re.findall(r"Supersedes:\s*(D-\d{3,})", b):
            g.edge(m.group(1), old, "supersedes")


def _pending(g: Graph, pdir: Path) -> None:
    section = ""
    for line in _read(pdir / "PENDING.md").splitlines():
        if line.startswith("## "):
            section = line[3:].strip()
        m = re.match(r"^\s*(?:[-*]\s+)?(?:~~)?(P-\d{3,})\s*·\s*([^·]+)", line)
        if m:
            g.node(m.group(1), "P", f"{m.group(1)} {m.group(2).strip()}", section=section)


def _mentions(g: Graph, pdir: Path) -> None:
    """Cross-references between IDs written anywhere in the project's docs."""
    for f in pdir.rglob("*.md"):
        if ".state" in f.parts:
            continue
        rel = f.relative_to(pdir).as_posix()
        text = "\n".join(l for l in _read(f).splitlines() if not l.lstrip().startswith("_"))  # skip template notes
        for para in re.split(r"\n\s*\n", text):
            ids = list(dict.fromkeys(ID_RE.findall(para)))
            for i in ids:
                g.nodes.setdefault(i, {"id": i, "type": i.split("-")[0], "label": i, "undefined": True})
                g.nodes[i].setdefault("mentioned_in", [])
                if rel not in g.nodes[i]["mentioned_in"]:
                    g.nodes[i]["mentioned_in"].append(rel)
            for a in ids:
                for b in ids:
                    if a < b:
                        g.edge(a, b, "mentions")


def _commits(g: Graph, project: str, limit: int = 400) -> None:
    for role, repo in ws.repos(ROOT, project, discover=False).items():
        if not (repo / ".git").exists() or repo.resolve() == ROOT.resolve().parent:
            continue
        try:
            out = subprocess.run(["git", "log", "--all", f"-n{limit}", "--date=short", "--name-only",
                                  "--format=\x1e%h\x1f%ad\x1f%s\x1f%b\x1d"], cwd=repo, capture_output=True, text=True,
                                 timeout=20, encoding="utf-8", errors="replace").stdout
        except Exception:
            continue
        for rec in out.split("\x1e")[1:]:
            head, _, files = rec.partition("\x1d")  # \x1d ends the body (which may contain blank lines)
            parts = head.split("\x1f")
            if len(parts) < 4:
                continue
            sha, date, subject, body = parts[0], parts[1], parts[2], parts[3]
            msg = f"{subject}\n{body}"
            refs = list(dict.fromkeys(ID_RE.findall(msg)))
            if not refs:
                continue
            cid = f"{role}@{sha}"
            g.node(cid, "C", f"{sha} {subject[:70]}", date=date, repo=role)
            reqs = [r for r in refs if r.startswith("REQ-")]
            for r in refs:
                g.edge(cid, r, "refs")
            for t in re.findall(r"\b(T\d+)\b", msg):
                for r in reqs:
                    if f"{r}/{t}" in g.nodes:
                        g.edge(cid, f"{r}/{t}", "refs")
            for path in [p for p in files.strip().splitlines() if p.strip()][:40]:
                fid = f"{role}:{path.strip()}"
                g.node(fid, "F", path.strip(), repo=role)
                g.edge(cid, fid, "touches")


def build(project: str, with_commits: bool = True) -> Graph:
    pdir = ROOT / project
    g = Graph(project)
    _requirements(g, pdir)
    _decisions(g, pdir)
    _pending(g, pdir)
    _mentions(g, pdir)
    if with_commits:
        _commits(g, project)
    return g


# ---------------------------------------------------------------- lint

def lint(g: Graph) -> list[dict]:
    out = []

    def add(level: str, code: str, node: str, msg: str) -> None:
        out.append({"level": level, "code": code, "node": node, "message": msg})

    covered = {e["target"] for e in g.edges if e["type"] == "covers"}
    for n in g.nodes.values():
        t = n["type"]
        if t in ("R", "US") and g.nodes.get(n["req"], {}).get("plan") and n["id"] not in covered:
            add("warn", "uncovered", n["id"], f"{n['id']} is not covered by any task of the plan")
        if t == "T":
            if not n.get("covers"):
                add("warn", "task-covers-nothing", n["id"], f"{n['id']} doesn't say which R/US it covers")
            for c in n.get("covers", []):
                if c not in g.nodes:
                    add("error", "unknown-ref", n["id"], f"{n['id']} covers {c}, which the spec doesn't define")
        if n.get("undefined") and t in ("REQ", "D", "P"):
            add("error", "dangling", n["id"], f"{n['id']} is mentioned in {', '.join(n['mentioned_in'][:3])} but never defined")
        if t == "D" and n.get("status", "").lower().startswith("superseded"):
            live = [f for f in n.get("mentioned_in", []) if f in ("SUMMARY.md", "ARCHITECTURE.md")]
            if live:
                add("warn", "superseded-in-use", n["id"], f"{n['id']} is superseded but still cited in {', '.join(live)}")
        if t == "REQ" and n.get("status") == "done":
            open_tasks = [e["target"] for e in g.edges if e["source"] == n["id"] and e["type"] == "plans"
                          and not g.nodes[e["target"]].get("done")]
            if open_tasks:
                add("warn", "done-with-open-tasks", n["id"], f"{n['id']} is done but {len(open_tasks)} task(s) are unticked")
    return out


# ---------------------------------------------------------------- queries

def neighborhood(g: Graph, start: str, depth: int = 2) -> set[str]:
    adj: dict[str, set[str]] = {}
    for e in g.edges:
        adj.setdefault(e["source"], set()).add(e["target"])
        adj.setdefault(e["target"], set()).add(e["source"])
    seen, frontier = {start}, {start}
    for _ in range(depth):
        frontier = {m for n in frontier for m in adj.get(n, set())} - seen
        seen |= frontier
    return seen


def files_impact(g: Graph, needle: str) -> dict[str, list[str]]:
    """Which requirements/decisions/pending items touched files matching `needle` (through commits)."""
    out: dict[str, list[str]] = {}
    for f in [n for n in g.nodes.values() if n["type"] == "F" and needle.lower() in n["label"].lower()]:
        commits = [e["source"] for e in g.edges if e["target"] == f["id"] and e["type"] == "touches"]
        ids = sorted({e["target"] for e in g.edges if e["source"] in commits and e["type"] == "refs"})
        out[f["id"]] = ids
    return out


def bundle(g: Graph, start: str, depth: int = 2, budget: int = 40) -> str:
    """Compact, linked context for a handoff or a subagent brief (non-obvious facts only, budgeted)."""
    ids = neighborhood(g, start, depth)
    order = {"REQ": 0, "US": 1, "R": 2, "T": 3, "D": 4, "P": 5, "C": 6, "F": 7}
    lines = [f"# Context bundle — {start} (depth {depth})"]
    for n in sorted((g.nodes[i] for i in ids if i in g.nodes), key=lambda n: (order.get(n["type"], 9), n["id"]))[:budget]:
        extra = n.get("status") or n.get("section") or n.get("date") or ("done" if n.get("done") else "")
        lines.append(f"- [{n['type']}] {n['label']}" + (f" ({extra})" if extra else ""))
    return "\n".join(lines)
