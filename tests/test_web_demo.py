from __future__ import annotations

import re
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


def test_static_web_demo_allows_mobile_grid_children_to_shrink() -> None:
    css = (ROOT / "web" / "styles.css").read_text(encoding="utf-8")

    for selector in (".panel", ".workspace > *", ".visual-grid > *", ".summary > div"):
        pattern = rf"{re.escape(selector)}[^\{{]*\{{[^}}]*min-width:\s*0;"
        assert re.search(pattern, css), f"{selector} should not force mobile overflow"

    pre_rule = re.search(r"pre\s*\{[^}]*\}", css)
    assert pre_rule is not None
    assert re.search(r"max-width:\s*100%;", pre_rule.group(0))
    assert re.search(r"overflow-x:\s*auto;", pre_rule.group(0))
