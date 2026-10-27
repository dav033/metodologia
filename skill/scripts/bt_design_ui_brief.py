"""Deterministic, owner-readable UI brief for one UI subplan: the Designer's behavioural source.

Built from the subplan row (`bt_design_drafts.subplans`), SPEC.md and an optional Planner-authored `ui_brief` object
on the subplan in PLAN.json. It keeps what a UI design needs (outcome, requirement texts, product criteria, user
flows, screens and states, the existing surface to change) and drops engineering detail: tasks outside the UI,
verification commands, expected paths, shared resources, digests and harness/build/audit criteria.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

ENGINEERING = tuple(re.compile(p, re.IGNORECASE) for p in (
    r"\bharness\b", r"checksum", r"byte[- ]identical", r"\bnext (?:start|build|dev)\b", r"\bproduction build\b",
    r"\bindependent\b.{0,60}\baudit\b", r"\baudit\b.{0,80}\bfindings?\b", r"\bsetup step\b", r"\bprovision",
    r"\bportable blender\b", r"\bblender lts\b", r"\bexecutable\b",
    r"\bsystem[- ]package", r"\bloopback\b", r"\bunexecuted check", r"\bfixture\b", r"\bci\b", r"\blint",
    r"\btype-?check", r"\bunit tests?\b", r"\bmigrations?\b", r"\brepository contract\b", r"~/\.",
))
OMITTED = ("tasks outside the UI (ui:false, non-design/non-review)", "verification", "expected_paths",
           "shared_resources", "classification and estimates", "digest", "engineering-only acceptance criteria")
BRIEF_KEYS = ("flows", "screens_states", "existing_surface", "must_not_change", "copy_rules", "criteria")
SURFACE_KEYS = ("routes", "paths", "components", "screenshots")
_NO_INVENTION = ("Sin nombres, fechas, eslóganes, titulares ni copy de marketing inventados: usa el copy de los "
                 "requisitos o de la interfaz existente; los datos de ejemplo son neutrales, realistas, claramente de "
                 "ejemplo y solo los que necesitan los flujos.")
_RULE = ("El mockup es un CAMBIO sobre una superficie existente del producto, nunca una página nueva ni una landing: "
         "reproduce el shell, la navegación y la cabecera existentes y cambia solo lo que exigen los requisitos.")


def engineering(text: str) -> bool:
    """Whether an acceptance criterion is about build, tooling, harness or audit rather than product behaviour."""
    return any(p.search(text or "") for p in ENGINEERING)


def ui_tasks(row: dict) -> list[dict]:
    """The subplan's UI work: `ui: true` tasks plus its design and visual-review tasks; nothing with `ui: false`."""
    ui = row.get("ui") or {}
    keep = {ui.get("design_task"), ui.get("visual_review_task")} - {None}
    return [t for t in row.get("tasks") or [] if t.get("ui") is True or t.get("id") in keep]


def product_criteria(row: dict) -> list[str]:
    """Subplan criteria a UI design must honour; a Planner `ui_brief.criteria` list replaces the derived set."""
    override = _planner(row).get("criteria")
    if isinstance(override, list):
        return [c for c in override if isinstance(c, str) and c.strip()]
    carried_by_ui = {c for t in ui_tasks(row) for c in t.get("acceptance_criteria") or []}
    carried = {c for t in row.get("tasks") or [] for c in t.get("acceptance_criteria") or []}
    out = []
    for text in row.get("criteria") or []:
        if not isinstance(text, str) or text == row.get("outcome") or text in out or engineering(text):
            continue
        if text in carried and text not in carried_by_ui:
            continue  # carried only by non-UI tasks (harness, integration run, audit)
        out.append(text)
    return out


def requirement_texts(spec: str, ids: list[str]) -> dict[str, str]:
    """`R9` → its sentence in SPEC.md (`- R9. …`, `- **R9**: …`); unknown ids are left out."""
    out = {}
    for rid in ids:
        if not isinstance(rid, str):
            continue
        found = re.search(rf"^\s*[-*]\s*\**{re.escape(rid)}\**\s*[.:)—–-]\s*(.+)$", spec, re.MULTILINE)
        if found:
            out[rid] = found.group(1).strip()
    return out


def cloned_repos(project: str) -> dict[str, Path]:
    import bt_workspace
    from bt_core import ROOT
    try:
        found = bt_workspace.repos(ROOT, project, discover=False)
    except (OSError, SystemExit, ValueError, KeyError):
        return {}
    return {role: Path(path) for role, path in found.items() if Path(path).exists()}


def siblings(rdir: Path, ref: str) -> list[Path]:
    """Chosen/finalised contracts of the other UI subplans: the app shell and vocabulary this design must reuse."""
    import bt_design_drafts as drafts
    out = []
    for row in drafts.subplans(rdir):
        if row["ref"] and row["ref"] != ref:
            md = drafts.paths(rdir, row["ref"])[0]
            out += [p for p in (md, md.with_suffix(".html")) if p.is_file()]
    approved = Path(rdir) / drafts.DIR / "contracts"
    if approved.is_dir():
        out += sorted(p for p in approved.glob("*.md") if not p.name.startswith(ref + ".") and p.name != "CHANGELOG.md")
    return out


def _planner(row: dict) -> dict:
    value = row.get("ui_brief")
    return value if isinstance(value, dict) else {}


def _texts(value: object) -> list[str]:
    return [v.strip() for v in value if isinstance(v, str) and v.strip()] if isinstance(value, list) else []


def _bullets(items: list[str], empty: str) -> list[str]:
    return [f"- {i}" for i in items] or [f"- {empty}"]


def _flows(value: object) -> list[str]:
    lines = []
    for i, flow in enumerate(value if isinstance(value, list) else [], 1):
        if isinstance(flow, str) and flow.strip():
            lines.append(f"{i}. {flow.strip()}")
        elif isinstance(flow, dict) and _texts(flow.get("steps")):
            lines.append(f"{i}. {str(flow.get('name') or '').strip() or 'Flujo'}")
            lines += [f"   {n}. {s}" for n, s in enumerate(_texts(flow["steps"]), 1)]
    return lines


def _surface(row: dict, repos: dict[str, Path]) -> list[str]:
    given = _planner(row).get("existing_surface")
    given = given if isinstance(given, dict) else {}
    named = [(k, _texts(given.get(k))) for k in SURFACE_KEYS]
    lines = [_RULE, ""]
    if any(v for _, v in named):
        lines.append("Superficie indicada por el Planner (léela en el repositorio, solo lectura, antes de diseñar):")
        lines += [f"- {k}: " + ", ".join(f"`{v}`" for v in vals) for k, vals in named if vals]
    elif repos:
        lines.append("El Planner no nombró las pantallas actuales. No las adivines: localízalas en solo lectura en "
                     "estos repositorios y basa el mockup en ellas; si no las encuentras, dilo en CONCERNS.")
    else:
        lines.append("No hay repositorio clonado en esta máquina: dilo en CONCERNS y pregunta con `Q:` qué pantalla "
                     "existente cambia este subplan.")
    lines += [f"- repo {role}: `{path}`" for role, path in repos.items()]
    if isinstance(given.get("notes"), str) and given["notes"].strip():
        lines.append(f"- Notas: {given['notes'].strip()}")
    return lines


def digest(rdir: Path, row: dict) -> str:
    """What a design depends on: the machine-independent brief without its omitted-fields footer, so estimates,
    non-UI tasks and other engineering fields of the subplan never make a design stale."""
    text = build(rdir, row, {}).split("\n## Omitido a propósito", 1)[0]
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def build(rdir: Path, row: dict, repos: dict[str, Path] | None = None) -> str:
    """The UI brief markdown for `row`; deterministic for the same inputs."""
    try:
        spec = (Path(rdir) / "SPEC.md").read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        spec = ""
    planner = _planner(row)
    covers = [c for c in row.get("covers") or [] if isinstance(c, str)]
    texts = requirement_texts(spec, covers)
    mentions = [m.group(1).strip() for m in re.finditer(r"^#{2,4}\s+(.+)$", spec, re.MULTILINE)
                if re.search(rf"\b{re.escape(row['id'])}\b", m.group(1))]
    tasks = ui_tasks(row)
    dropped = [t.get("id") for t in row.get("tasks") or [] if t not in tasks]
    out = [f"# Brief de interfaz — {row['id']} · {row.get('title') or ''}".rstrip(), "",
           "Fuente de comportamiento compartida para el Designer. Lo que no está aquí no es alcance de diseño.", "",
           "## Resultado esperado", "", row.get("outcome") or "(sin resultado definido)", "",
           "## Requisitos que cubre", ""]
    out += [f"- {rid}: {texts.get(rid, '(texto no encontrado en SPEC.md)')}" for rid in covers] or ["- (ninguno)"]
    if mentions:
        out += ["", "Secciones de SPEC.md que nombran este subplan (léelas): " + "; ".join(f"«{m}»" for m in mentions)]
    out += ["", "## Criterios de producto", ""] + _bullets(product_criteria(row), "(ninguno declarado)")
    out += ["", "## Flujos de usuario", ""] + (_flows(planner.get("flows")) or [
        "- El Planner no los escribió: derívalos de los requisitos y de la superficie existente, sin inventar flujos."])
    out += ["", "## Pantallas y estados", ""] + _bullets(_texts(planner.get("screens_states")),
        "El Planner no los escribió: lista en el contrato las pantallas y estados que exigen los requisitos.")
    out += ["", "## Superficie existente a modificar", ""] + _surface(row, repos or {})
    out += ["", "## No debe cambiar", ""] + _bullets(_texts(planner.get("must_not_change")),
        "El resto de la superficie existente: shell, navegación, cabecera, tokens, fuentes y componentes.")
    out += ["", "## Reglas de copy", ""] + _bullets(_texts(planner.get("copy_rules")) + [_NO_INVENTION], "")
    out += ["", "## Tareas de interfaz", ""]
    criteria = set(product_criteria(row))
    for t in tasks:
        out.append(f"- {t.get('id')} — {t.get('title') or ''}".rstrip())
        objective = t.get("objective")
        if isinstance(objective, str) and objective and objective not in criteria and not engineering(objective):
            out.append(f"  - Objetivo: {objective}")
    if not tasks:
        out.append("- (aún sin tareas de interfaz)")
    out += ["", "## Omitido a propósito", "",
            "Campos del subplan que no se pasan al Designer: " + ", ".join(OMITTED)
            + (f". Tareas omitidas: {', '.join(map(str, dropped))}." if dropped else "."), ""]
    return "\n".join(out)
