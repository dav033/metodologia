"""The bundled contract documents: the JSON Schema and a complete example plan."""
from __future__ import annotations

from pathlib import Path

DATA = Path(__file__).resolve().parent / "data"


def schema_text() -> str:
    return (DATA / "plan.schema.json").read_text(encoding="utf-8")


def example_text() -> str:
    return (DATA / "plan.example.json").read_text(encoding="utf-8")
