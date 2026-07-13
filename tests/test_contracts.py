from __future__ import annotations

import json
from pathlib import Path

from nokaman.eval.pipeline import evaluate_demo, evaluate_text
from nokaman.integrations.sdk import assess_for_app, demo_payload

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"
TYPESCRIPT_CONTRACT = ROOT / "sdk" / "typescript" / "index.ts"


def _schema(name: str) -> dict:
    return json.loads((SCHEMAS / name).read_text(encoding="utf-8"))


def test_assess_text_response_schema_matches_api_payload_keys() -> None:
    payload = evaluate_text("en", "I practice English every morning.", skill="writing")
    schema = _schema("assess_text_response.schema.json")

    assert set(schema["required"]) == set(payload)
    assert set(payload).issubset(schema["properties"])


def test_demo_response_schema_matches_api_payload_keys() -> None:
    payload = evaluate_demo("en")
    schema = _schema("demo_response.schema.json")

    assert set(schema["required"]) == set(payload)
    assert set(payload).issubset(schema["properties"])


def test_sdk_optional_fields_are_in_response_schemas() -> None:
    text_payload = assess_for_app("en", "Hello, I am learning English.", skill="writing")
    demo = demo_payload("ja")

    text_schema = _schema("assess_text_response.schema.json")
    demo_schema = _schema("demo_response.schema.json")

    assert set(text_payload).issubset(text_schema["properties"])
    assert set(demo).issubset(demo_schema["properties"])


def test_typescript_contract_exports_expected_interfaces() -> None:
    source = TYPESCRIPT_CONTRACT.read_text(encoding="utf-8")

    for name in [
        "AssessTextRequest",
        "AssessTextResponse",
        "DemoResponse",
        "FrameworkBands",
        "TextFeatures",
    ]:
        assert f"export interface {name}" in source
