from __future__ import annotations

from nokaman.integrations.sdk import assess_for_app, demo_payload


def test_assess_for_app() -> None:
    result = assess_for_app("en", "Hello, I am learning English.", skill="writing")
    assert result["integration_version"] == "nokaman.sdk.v1"
    assert result["ready_for_ui"] is True


def test_demo_payload() -> None:
    result = demo_payload("ja")
    assert result["language"] == "ja"
    assert "overall" in result
