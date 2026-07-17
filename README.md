# NokaMan

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-0.3.0-0E8A16.svg)](pyproject.toml)
[![Qt GUI](https://img.shields.io/badge/GUI-PySide6-41CD52.svg)](src/nokaman/gui/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![MergeOS](https://img.shields.io/badge/MergeOS-bounties-5319E7.svg)](https://github.com/mergeos-bounties)

**NokaMan** assesses **language-learning ability** across multiple skills and languages — CEFR-style bands, rubrics, and JSON reports ready for learning apps.

**Product:** [mergeos-bounties/NokaMan](https://github.com/mergeos-bounties/NokaMan)

---

## Table of contents

- [Highlights](#highlights)
- [Desktop GUI (Qt)](#desktop-gui-qt)
- [Screenshots](#screenshots)
- [Quick start](#quick-start)
- [CLI reference](#cli-reference)
- [App integration contracts](#app-integration-contracts)
- [Languages & rubrics](#languages--rubrics)
- [Supported language catalog](docs/LANGUAGES.md)
- [Offline speaking fluency rubric](docs/SPEAKING_FLUENCY.md)
- [Diagrams](#diagrams)
- [Repository layout](#repository-layout)
- [Development](#development)
- [Contributing](#contributing)
- [Docs: CEFR expected_cefr field mapping table](docs/CEFR_MAPPING.md#cefr-mapping-notes)
- [MergeOS bounties](#mergeos-bounties)
- [License](#license)

---

## Highlights

| Mode | Description |
| --- | --- |
| **Multi-skill eval** | Vocabulary, grammar, reading, writing, listening, speaking proxies |
| **CEFR-style bands** | Map scores → A1–C2 style levels (scaffold) |
| **Multi-language** | EN, KO, JA, VI, ZH (+ extend via rubrics) |
| **JSON reports** | Save under `OUT_DIR` for app integration |
| **Offline demo** | `nokaman demo --lang en` end-to-end |
| **Desktop GUI** | Modern **PySide6** app (`nokaman-gui`) |

---

## Desktop GUI (Qt)

Modern dark **PySide6** demo — multi-skill evaluation, languages, free-text scoring, samples, rubrics, toy calibration.

```powershell
pip install -e ".[gui]"
nokaman-gui
# or: nokaman gui
```

<p align="center">
  <img src="docs/screenshots/gui-demo.png" alt="NokaMan GUI — Full demo" width="100%" />
</p>
<p align="center"><em>Full multi-skill demo</em></p>

<p align="center">
  <img src="docs/screenshots/gui-languages.png" alt="NokaMan GUI — Languages" width="100%" />
</p>
<p align="center"><em>Supported languages & frameworks</em></p>

<p align="center">
  <img src="docs/screenshots/gui-evaluate.png" alt="NokaMan GUI — Evaluate" width="100%" />
</p>
<p align="center"><em>Evaluate free text / samples / placement</em></p>

<p align="center">
  <img src="docs/screenshots/gui-samples.png" alt="NokaMan GUI — Samples" width="100%" />
</p>
<p align="center"><em>Bundled samples + batch metrics</em></p>

<p align="center">
  <img src="docs/screenshots/gui-rubrics.png" alt="NokaMan GUI — Rubrics" width="100%" />
</p>
<p align="center"><em>Skill rubrics</em></p>

<p align="center">
  <img src="docs/screenshots/gui-train.png" alt="NokaMan GUI — Train" width="100%" />
</p>
<p align="center"><em>Toy calibration</em></p>

---

## Screenshots

CLI / terminal captures:

| Evaluation demo | Languages |
| :---: | :---: |
| ![Eval EN](docs/screenshots/demo-eval-en.png) | ![Languages](docs/screenshots/demo-languages.png) |
| *English multi-skill demo* | *Supported languages registry* |

---

## Quick start

```powershell
cd NokaMan
python -m venv .venv
.\.venv\Scripts\activate
pip install -e ".[dev,gui]"

nokaman version
nokaman languages list
nokaman demo --lang en
nokaman rubrics list
nokaman-gui
```

For a browser demo that talks to the local FastAPI app, see [`web/README.md`](web/README.md).

---

## CLI reference

| Command | Purpose |
| --- | --- |
| `nokaman version` | Version + language codes |
| `nokaman demo -l en` | Full multi-skill evaluation demo |
| `nokaman languages list` | Supported languages + frameworks |
| `nokaman languages coverage` | Language x skill sample coverage matrix |
| `nokaman rubrics list [-l en]` | Skill rubrics |
| `nokaman rubrics explain -l en` | Print rubric skill weights, notes, frameworks, and bands |
| `nokaman eval text …` | Evaluate free text |
| `nokaman eval batch --out data/out/batch.json` | Score every sample and write a JSON CEFR hit-rate report |
| `nokaman train …` | Toy calibration with config/report exports |
| `nokaman gui` / `nokaman-gui` | **Qt desktop app** (needs `.[gui]`) |
| `nokaman serve` | Optional FastAPI |

```powershell
nokaman demo -l vi
nokaman demo -l ko
nokaman eval batch --out data/out/batch.json
nokaman train toy --config configs/example.yaml
nokaman-gui
```

---

## App integration contracts

NokaMan publishes stable contracts for mobile and web apps under `schemas/` and `sdk/typescript/`.
They mirror the real FastAPI and SDK payloads, so app teams can validate data and type responses without
reverse-engineering demo output.

| Contract | Runtime source |
| --- | --- |
| `schemas/assess_text_request.schema.json` | `POST /assess/text` request body |
| `schemas/assess_text_response.schema.json` | `POST /assess/text` and `assess_for_app(..., multi_skill=false)` |
| `schemas/demo_response.schema.json` | `GET /assess/demo/{lang}` and `demo_payload()` |
| `sdk/typescript/index.ts` | TypeScript interfaces for request and response payloads |

Optional FastAPI endpoints:

| Endpoint | Purpose |
| --- | --- |
| `GET /languages` | List supported language codes, display names, and frameworks |
| `POST /assess` | App-facing text assessment alias |
| `POST /assess/text` | Text assessment with language, text, and skill |
| `GET /assess/demo/{lang}` | Multi-skill demo payload |
| `POST /assess/placement` | Placement score from multiple answers |

Example TypeScript use:

```typescript
import type { AssessTextRequest, AssessTextResponse } from "./sdk/typescript";

const body: AssessTextRequest = {
  language: "en",
  text: "I practice English every morning.",
  skill: "writing",
};

const response = await fetch("/assess/text", {
  method: "POST",
  headers: { "content-type": "application/json" },
  body: JSON.stringify(body),
});

const assessment = (await response.json()) as AssessTextResponse;
console.log(assessment.cefr, assessment.score, assessment.framework_bands);
```

---

## Languages & rubrics

Rubrics and samples live under `data/`. Extend by adding rubric JSON + samples, then register in `nokaman.rubrics.registry`.
See [docs/LANGUAGES.md](docs/LANGUAGES.md) for the supported language catalog, CEFR/JLPT/TOPIK/HSK mappings, and language-pack extension steps.
See [docs/SPEAKING_FLUENCY.md](docs/SPEAKING_FLUENCY.md) for the transcript-only speaking rubric and its limitations.

| Code | Typical use |
| --- | --- |
| `en` | English (default demo) |
| `vi` | Vietnamese |
| `ko` / `ja` / `zh` | East Asian tracks |

---

## Diagrams

System architecture and workflow — full width. Open the HTML files for **dark/light theme** and export (PNG/SVG).

### Architecture

[Open interactive diagram](docs/diagrams/architecture.html)

<p align="center">
  <img src="docs/diagrams/architecture.svg" alt="NokaMan architecture" width="100%" />
</p>

### Workflow

[Open interactive diagram](docs/diagrams/workflow.html)

<p align="center">
  <img src="docs/diagrams/workflow.svg" alt="NokaMan workflow" width="100%" />
</p>

*Generated with [archify](https://github.com/tt-a1i).*

---

## Repository layout

```text
src/nokaman/
  cli.py
  gui/            # PySide6 desktop demo (nokaman-gui)
  eval/           # pipeline, metrics, placement
  rubrics/        # language metadata + skills
  data/loader.py
  train/toy_train.py
web/              # no-build browser demo for the FastAPI app
docs/screenshots/
docs/diagrams/
```

---

## Development

```powershell
pytest -q
ruff check src tests
nokaman demo -l en
python scripts/capture_gui_shots.py   # refresh GUI screenshots
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for local setup, test commands, the good-first-issue path, and the MergeOS bounty claim flow.

---

## MergeOS bounties

Star + claim bounty → PR to **master** with demo JSON / screenshots → MRG **25–200**.  
See [CONTRIBUTING.md](CONTRIBUTING.md) for the contributor path and org policy on [mergeos](https://github.com/mergeos-bounties/mergeos).

---

## License

MIT · MergeOS / ThanhTrucSolutions
