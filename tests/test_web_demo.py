from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_static_web_demo_files_are_wired() -> None:
    web_dir = ROOT / "web"
    index = web_dir / "index.html"
    styles = web_dir / "styles.css"
    app = web_dir / "app.js"
    readme = web_dir / "README.md"

    for path in (index, styles, app, readme):
        assert path.exists(), f"missing {path.relative_to(ROOT)}"

    html = index.read_text(encoding="utf-8")
    script = app.read_text(encoding="utf-8")

    assert "styles.css" in html
    assert "app.js" in html
    assert "/health" in script
    assert "/assess/text" in script
    assert "/assess/demo/" in script
    assert "/assess/placement" in script
