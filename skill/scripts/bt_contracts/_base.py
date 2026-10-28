"""Shared Pydantic bases for the canonical contracts.

`WireModel` is a camelCase wire contract with snake_case attributes; `SnakeWireModel` keeps the wire names as written.
Both refuse unknown fields and coerce nothing (strict), so a producer that drifts in name or type fails validation
instead of being silently accepted. Only aliases validate: a snake_case key on a camelCase contract is an unknown field.
"""
from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class WireModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, alias_generator=to_camel, serialize_by_alias=True,
                              validate_by_alias=True, validate_by_name=False)


class SnakeWireModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


# RFC 3339 timestamps travel as strings; the pattern catches non-timestamps without parsing every legacy variant.
Timestamp = Annotated[str, Field(pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}", json_schema_extra={"format": "date-time"})]
NonEmpty = Annotated[str, Field(min_length=1)]

__all__ = ["NonEmpty", "SnakeWireModel", "Timestamp", "WireModel"]
