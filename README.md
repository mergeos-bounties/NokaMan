# NokaMan

**NokaMan** is a training and inference toolkit for **language-learning ability assessment**:

| Mode | Description |
| --- | --- |
| **Skill scoring** | Vocabulary, grammar, reading, writing, listening, speaking proxies |
| **CEFR-style band** | Map multi-skill scores → levels (A1–C2 scaffold) |
| **Multi-language** | English, Korean, Japanese, Vietnamese, Chinese (+ extend) |
| **App integration** | JSON report for embedding into language-learning products |

Built under [mergeos-bounties](https://github.com/mergeos-bounties) so delivery can be funded as MergeOS tasks with MRG payouts.


## Screenshots

Real captures from running the product demo (NokaMan).

![English multi-skill evaluation demo](docs/screenshots/demo-eval-en.png)

*English multi-skill evaluation demo*

![Supported languages](docs/screenshots/demo-languages.png)

*Supported languages*

## Stack

- Python 3.11+
- CLI: `typer` + `rich`
- Rubric-driven toy assessor (offline, no LLM required)
- Optional LLM / torch / FastAPI extras via bounties

## Quick start

```bash
cd NokaMan
python -m venv .venv

# Windows
.venv\Scripts\activate

pip install -e ".[dev]"
nokaman --help
```

## Commands (runnable)

```bash
nokaman version
nokaman demo --lang en                 # multi-skill report + save JSON
nokaman languages list
nokaman eval text --lang en --file data/samples/en_writing_b1.json
nokaman eval text --lang ko --text "안녕하세요. 저는 학생입니다."
nokaman eval batch --out data/runs/batch_eval.json
nokaman eval placement --lang en -a "I study every day." -a "Hello!"
nokaman train toy --epochs 3
```

## Layout

```
src/nokaman/
  cli.py
  config.py
  data/             # loaders for samples + rubrics
  models/           # toy ability model + CEFR mapping
  eval/             # scoring pipelines
  rubrics/          # skill rubrics per language
  train/            # calibration stubs
  integrations/     # app SDK sketch
  api/              # optional FastAPI
data/samples/       # learner response fixtures
data/rubrics/       # CEFR-ish skill descriptors
docs/BOUNTY.md
```

## MergeOS bounties

1. Star this repo + [mergeos](https://github.com/mergeos-bounties/mergeos)
2. Claim an issue labeled `bounty`
3. Also claim on MergeOS [issue #1](https://github.com/mergeos-bounties/mergeos/issues/1)
4. Open a PR with tests/evidence to **this public repo**
5. Maintainer merges and credits MRG (25/50/100/200)

See [docs/BOUNTY.md](docs/BOUNTY.md).

## Privacy

- Prefer consented learner data and public corpora with clear licenses.
- Do not ship private student PII without permission.
- Document dataset licenses in every PR that adds data.

## License

MIT
