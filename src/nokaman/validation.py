"""Pydantic models for rubric and sample validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field, ValidationError


class RubricDimension(BaseModel):
    name: str = Field(..., min_length=1, description="Dimension name")
    weight: float = Field(..., ge=0.0, le=1.0, description="Dimension weight")
    description: str = Field("", description="Dimension description")


class RubricSkill(BaseModel):
    description: Optional[str] = Field(None, description="Skill description")
    dimensions: Optional[list[RubricDimension]] = Field(None, description="Scoring dimensions")
    weight: Optional[float] = Field(None, ge=0.0, description="Skill weight")


class Rubric(BaseModel):
    language: str = Field(..., min_length=1, description="Language code")
    name: str = Field("", description="Language name")
    meta: Optional[dict[str, Any]] = Field(None, description="Metadata")
    skills: dict[str, RubricSkill] = Field(..., description="Skill rubrics")


class Sample(BaseModel):
    text: str = Field(..., min_length=1, description="Sample text")
    skill: str = Field(..., min_length=1, description="Skill being assessed")
    expected_cefr: Optional[str] = Field(None, description="Expected CEFR level")
    language: str = Field(..., min_length=1, description="Language code")


def validate_rubric(data: dict) -> list[str]:
    errors = []
    try:
        Rubric(**data)
    except ValidationError as e:
        for err in e.errors():
            loc = " -> ".join(str(x) for x in err["loc"])
            errors.append(f"{loc}: {err['msg']}")
    return errors


def validate_sample(data: dict) -> list[str]:
    errors = []
    try:
        Sample(**data)
    except ValidationError as e:
        for err in e.errors():
            loc = " -> ".join(str(x) for x in err["loc"])
            errors.append(f"{loc}: {err['msg']}")
    return errors


def validate_rubric_file(path: Path) -> list[str]:
    import json
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        return [f"File read error: {e}"]
    return validate_rubric(data)


def validate_sample_file(path: Path) -> list[str]:
    import json
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        return [f"File read error: {e}"]
    if isinstance(data, list):
        all_errors = []
        for i, item in enumerate(data):
            for err in validate_sample(item):
                all_errors.append(f"[{i}] {err}")
        return all_errors
    return validate_sample(data)
