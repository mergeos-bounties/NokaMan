# NokaMan

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-0.2.1-0E8A16.svg)](pyproject.toml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![MergeOS](https://img.shields.io/badge/MergeOS-bounties-5319E7.svg)](https://github.com/mergeos-bounties)

**NokaMan** assesses **language-learning ability** across multiple skills and languages — CEFR-style bands, rubrics, JSON reports for embedding in learning apps.

Product: [mergeos-bounties/NokaMan](https://github.com/mergeos-bounties/NokaMan)

---

## Table of contents

- [Highlights](#highlights)
- [Screenshots](#screenshots)
- [Quick start](#quick-start)
- [CLI reference](#cli-reference)
- [Languages & rubrics](#languages--rubrics)
- [Architecture](#architecture)
- [Development](#development)
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

---

## Screenshots

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
pip install -e ".[dev]"

nokaman version
nokaman languages list
nokaman demo --lang en
nokaman rubrics list
```

---

## CLI reference

| Command | Purpose |
| --- | --- |
| `nokaman version` | Version + language codes |
| `nokaman demo -l en` | Full multi-skill evaluation demo |
| `nokaman languages list` | Supported languages + frameworks |
| `nokaman rubrics list [-l en]` | Skill rubrics |
| `nokaman eval text …` | Evaluate free text |
| `nokaman train …` | Toy calibration |
| `nokaman serve` | Optional FastAPI |

```powershell
nokaman demo -l vi
nokaman demo -l ko
```

---

## Languages & rubrics

Rubrics and samples live under `data/`. Extend by adding rubric JSON + samples, then register in `nokaman.rubrics.registry`.

| Code | Typical use |
| --- | --- |
| `en` | English (default demo) |
| `vi` | Vietnamese |
| `ko` / `ja` / `zh` | East Asian tracks |

---

## Architecture

```text
src/nokaman/
  cli.py
  eval/           # pipeline, metrics, placement
  rubrics/        # language metadata + skills
  data/loader.py
  train/toy_train.py
docs/screenshots/
```

---

## Development

```powershell
pytest -q
ruff check src tests
nokaman demo -l en
```

---

## MergeOS bounties

Star + claim bounty → PR to **master** with demo JSON / screenshots → MRG **25–200**.  
See org policy on [mergeos](https://github.com/mergeos-bounties/mergeos).

---

## Tiếng Việt

**NokaMan** đánh giá năng lực học ngôn ngữ đa kỹ năng (EN/VI/…). Chạy: `nokaman demo -l en` hoặc `-l vi`.

---

## License

MIT · MergeOS / ThanhTrucSolutions
