from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, StrictStr, ValidationError


class SamplePayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: StrictStr
    language: StrictStr = "en"
    skill: StrictStr = "writing"
    text: StrictStr = ""
    expected_cefr: StrictStr | None = None


class RubricSkillPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    weight: float = 1.0
    notes: StrictStr = ""


class RubricPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    language: StrictStr
    name: StrictStr | None = None
    skills: dict[str, RubricSkillPayload] = Field(default_factory=dict)
    bands: list[StrictStr] = Field(default_factory=list)


def _format_validation_error(kind: str, source: str, error: ValidationError) -> ValueError:
    details = []
    for item in error.errors():
        path = ".".join(str(part) for part in item["loc"]) or "<root>"
        details.append(f"{path}: {item['msg']}")
    return ValueError(f"Invalid {kind} JSON in {source}: {'; '.join(details)}")


def validate_sample_payload(payload: dict[str, Any], source: str = "<memory>") -> dict[str, Any]:
    try:
        return SamplePayload.model_validate(payload).model_dump(exclude_none=True)
    except ValidationError as exc:
        raise _format_validation_error("sample", source, exc) from exc


def validate_rubric_payload(payload: dict[str, Any], source: str = "<memory>") -> dict[str, Any]:
    try:
        return RubricPayload.model_validate(payload).model_dump(exclude_none=True)
    except ValidationError as exc:
        raise _format_validation_error("rubric", source, exc) from exc
