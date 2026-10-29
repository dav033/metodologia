"""Generate the published JSON Schemas and the phone's TypeScript types from the Pydantic contracts.

    uv run python -m bt_contracts.schemas          # rewrite remote/contract/*.schema.json, contract.generated.ts
                                                   # and bt_contracts/schemas/plan.schema.json
    uv run python -m bt_contracts.schemas --check  # exit 1 when any generated file is stale

The TypeScript is derived from the same JSON Schema that is published, so the phone, the gateway docs and the
Python tests read one source. Only the JSON Schema subset Pydantic emits for these models is translated.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from pydantic.json_schema import models_json_schema

from bt_contracts import plan, remote

REPO = Path(__file__).resolve().parents[3]
CONTRACT_DIR = REPO / "remote" / "contract"
TS_PATH = REPO / "remote" / "web" / "src" / "contract.generated.ts"
SCHEMA_ID = "https://flow-remote.invalid/contract/v1/"
PLAN_SCHEMA_PATH = Path(__file__).resolve().parent / "schemas" / "plan.schema.json"
PLAN_SCHEMA_ID = "https://bitacora.invalid/contract/plan.schema.json"
_IDENTIFIER = re.compile(r"^[A-Za-z_$][A-Za-z0-9_$]*$")


def _strip_titles(value: Any) -> Any:
    """Pydantic's auto titles are noise for readers; keep only meaningful keys."""
    if isinstance(value, dict):
        return {key: _strip_titles(item) for key, item in value.items()
                if not (key == "title" and isinstance(item, str))}
    if isinstance(value, list):
        return [_strip_titles(item) for item in value]
    return value


def model_schema(name: str, model: type) -> dict[str, Any]:
    schema = _strip_titles(model.model_json_schema(by_alias=True))
    doc = (model.__doc__ or "").strip()
    head = {"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": SCHEMA_ID + name,
            "title": f"Bitácora remote {model.__name__} v{remote.SCHEMA_VERSION}"}
    if doc and "description" not in schema:
        head["description"] = " ".join(doc.split())
    return {**head, **schema}


def json_files() -> dict[Path, str]:
    return {CONTRACT_DIR / name: json.dumps(model_schema(name, model), indent=2, ensure_ascii=False) + "\n"
            for name, model in remote.SCHEMA_FILES.items()}


def _drop_null_defaults(value: Any) -> Any:
    """`X = None` fields may be absent but never null; a `default: null` next to a non-null type only misleads."""
    if isinstance(value, dict):
        return {key: _drop_null_defaults(item) for key, item in value.items()
                if not (key == "default" and item is None)}
    if isinstance(value, list):
        return [_drop_null_defaults(item) for item in value]
    return value


def plan_schema() -> dict[str, Any]:
    """PLAN.json 1.0.0-1.3.0 as one document: one definition per schema version, chosen by `schema_version`."""
    schema = _drop_null_defaults(_strip_titles(plan.PLAN_ADAPTER.json_schema(by_alias=True)))
    head = {"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": PLAN_SCHEMA_ID,
            "title": f"Bitácora PLAN.json, schema {' / '.join(plan.SCHEMA_VERSIONS)}",
            "description": "Generated from the Pydantic models of bt_contracts/plan.py; do not edit. Rules across "
                           "objects (unique ids, references that resolve, an acyclic `after`, consumed contracts "
                           "produced by the subplan they name, a stage listing the revision's subplans, text that is "
                           "not blank, relative paths) are enforced by the models' validators and are not all "
                           "expressible here. Text and evidence quality, coverage totality, task roles and ordering "
                           "remain the planner's authoring rules."}
    return {**head, **schema}


def plan_file() -> dict[Path, str]:
    return {PLAN_SCHEMA_PATH: json.dumps(plan_schema(), indent=2, ensure_ascii=False) + "\n"}


# ---- TypeScript ----

def _literal(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def _wrap(text: str) -> str:
    return f"({text})" if " | " in text else text


def ts_type(schema: dict[str, Any]) -> str:
    if "$ref" in schema:
        return schema["$ref"].rsplit("/", 1)[-1]
    for key in ("anyOf", "oneOf"):
        if key in schema:
            parts = list(dict.fromkeys(ts_type(item) for item in schema[key]))
            return " | ".join(parts)
    if "const" in schema:
        return _literal(schema["const"])
    if "enum" in schema:
        return " | ".join(_literal(item) for item in schema["enum"])
    kind = schema.get("type")
    if isinstance(kind, list):
        return " | ".join(ts_type({**schema, "type": item}) for item in kind)
    if kind == "string":
        return "string"
    if kind in ("integer", "number"):
        return "number"
    if kind == "boolean":
        return "boolean"
    if kind == "null":
        return "null"
    if kind == "array":
        return f"{_wrap(ts_type(schema.get('items') or {}))}[]"
    if kind == "object" or "properties" in schema:
        return _object(schema)
    return "unknown"


def _object(schema: dict[str, Any], indent: str = "") -> str:
    properties = schema.get("properties") or {}
    extra = schema.get("additionalProperties")
    if not properties:
        value = ts_type(extra) if isinstance(extra, dict) and extra else "unknown"
        return f"Record<string, {value}>"
    required = set(schema.get("required") or ())
    lines = ["{"]
    for name, prop in properties.items():
        key = name if _IDENTIFIER.match(name) else _literal(name)
        if prop.get("description"):
            lines.append(f"{indent}  /** {' '.join(prop['description'].split())} */")
        lines.append(f"{indent}  {key}{'' if name in required else '?'}: {ts_type(prop)};")
    lines.append(indent + "}")
    return "\n".join(lines)


def typescript() -> str:
    models = list(remote.SCHEMA_FILES.values())
    _, combined = models_json_schema([(model, "validation") for model in models], by_alias=True,
                                     ref_template="#/$defs/{model}")
    definitions = _strip_titles(combined.get("$defs", {}))
    out = ["// Generated by `uv run python -m bt_contracts.schemas` from skill/scripts/bt_contracts/remote.py.",
           "// Do not edit: change the Pydantic models and regenerate (a test fails when this file is stale).", ""]
    for name in sorted(definitions):
        schema = definitions[name]
        if schema.get("description"):
            out.append(f"/** {' '.join(schema['description'].split())} */")
        out.append(f"export type {name} = {ts_type(schema)};")
        out.append("")
    for name, value in remote.TS_CONSTANTS.items():
        out.append(f"export const {name} = {json.dumps(value, ensure_ascii=False)} as const;")
    out.append("")
    return "\n".join(out)


def generated() -> dict[Path, str]:
    return {**json_files(), TS_PATH: typescript(), **plan_file()}


def stale() -> list[Path]:
    paths = [path for path, text in generated().items()
             if not path.is_file() or path.read_text(encoding="utf-8") != text]
    published = set(json_files())
    paths += [path for path in CONTRACT_DIR.glob("*.schema.json") if path not in published]
    return sorted(paths)


def write() -> list[Path]:
    for path in CONTRACT_DIR.glob("*.schema.json"):
        if path not in json_files():
            path.unlink()
    written = []
    for path, text in generated().items():
        if not path.is_file() or path.read_text(encoding="utf-8") != text:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
            written.append(path)
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="fail when a generated file is stale")
    args = parser.parse_args(argv)
    if args.check:
        paths = stale()
        for path in paths:
            print(f"stale: {path.relative_to(REPO)}", file=sys.stderr)
        return 1 if paths else 0
    for path in write():
        print(f"wrote {path.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
