# Contributing to NokaMan

Thanks for helping improve NokaMan. This guide covers the local setup, validation commands, and MergeOS bounty flow for first-time contributors.

## Target Repository

Open pull requests against the public product repository:

**https://github.com/mergeos-bounties/NokaMan**

Do not target private mirrors or unrelated forks. Bounty work lands on the public `NokaMan` repository, normally against the `master` branch.

## Local Setup

NokaMan requires **Python 3.11** or newer.

### Quick start

```bash
git clone https://github.com/mergeos-bounties/NokaMan.git
cd NokaMan
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e ".[dev]"
```

### With the optional desktop GUI

```bash
python -m pip install -e ".[dev,gui]"
```

### Verify installation

```bash
nokaman version
nokaman languages list
nokaman demo --lang en
nokaman rubrics list
```

For the optional GUI:

```bash
nokaman-gui
# or
nokaman gui
```

## Running Tests

Run the focused checks before opening a PR:

```bash
# Compile check (syntax validation)
python3.11 -m compileall src tests

# Unit tests
python3.11 -m pytest -q

# Linter
python3.11 -m ruff check src tests
```

If the local `build` package is available, also run:

```bash
python3.11 -m build
```

For documentation-only changes, `pytest` and `ruff` are still useful because they catch accidental packaging or import regressions.

### Test organization

| Test file | Coverage area |
|-----------|--------------|
| `test_cli.py` | CLI commands and output |
| `test_eval.py` | Evaluation pipeline and scoring |
| `test_api.py` | FastAPI endpoints |
| `test_contracts.py` | JSON schema and TypeScript contract validation |
| `test_rubric_explain.py` | Rubric explanation command |
| `test_multilingual_smoke.py` | Multi-language smoke tests |

## Project Structure

```text
src/nokaman/
  cli.py              # Typer CLI entry point
  gui/                # PySide6 desktop app (nokaman-gui)
  eval/               # Pipeline, metrics, placement
  rubrics/            # Language metadata + skill rubrics
  data/loader.py      # Sample data loading
  train/toy_train.py  # Toy calibration training
web/                  # Browser demo for FastAPI app
schemas/              # JSON Schema contracts
sdk/typescript/       # TypeScript interface contracts
tests/                # Pytest suite
docs/                 # Documentation and diagrams
```

## Contribution Workflow

### 1. Pick an issue

Look for issues labeled `good first issue`, `help wanted`, or `bounty`. Read the full description and acceptance criteria before starting.

### 2. Claim the bounty (MergeOS)

If the issue is a MergeOS bounty:

1. Star https://github.com/mergeos-bounties/NokaMan and https://github.com/mergeos-bounties/mergeos
2. Comment `I claim this bounty` on the issue
3. Comment on [MergeOS Claim Token #1](https://github.com/mergeos-bounties/mergeos/issues/1) with a link to the bounty issue

### 3. Create a branch

```bash
git fetch upstream
git checkout master
git pull upstream master
git checkout -b feat/your-feature-name
```

Branch naming conventions:
- `feat/description` — new features
- `fix/description` — bug fixes
- `docs/description` — documentation
- `data/description` — sample data additions

### 4. Implement and test

Keep changes scoped to the issue. Run all checks from the [Running Tests](#running-tests) section before committing.

### 5. Commit and push

```bash
git add <files>
git commit -m "type(scope): short description"
git push -u origin HEAD
```

Commit message format (Conventional Commits):
```
type(scope): short description

Longer explanation if needed.
```

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `data`, `chore`

### 6. Open a PR

Target: **mergeos-bounties/NokaMan** (base: `master`)

Include in your PR description:
- What changed and why
- Test output (paste the summary line from `pytest -q`)
- `Fixes #<issue-number>`
- Screenshots or artifacts if the issue requires them

## MergeOS Bounty Claim Flow

For MergeOS MRG bounties (25–200 MRG):

1. **Star** https://github.com/mergeos-bounties/NokaMan and https://github.com/mergeos-bounties/mergeos
2. **Claim** — Comment `I claim this bounty` on the NokaMan bounty issue
3. **Link** — Comment on MergeOS Claim Token #1 with a link to the bounty issue
4. **PR** — Open a pull request to the public NokaMan repository
5. **Evidence** — Include test output, screenshots, or artifacts required by the issue

Maintainers review the PR and credit MRG after merge according to the bounty policy.

## Pull Request Checklist

- [ ] PR targets `mergeos-bounties/NokaMan` (base: `master`)
- [ ] PR description links the issue with `Fixes #<issue-number>`
- [ ] Change is limited to the requested scope (no unrelated refactors)
- [ ] All tests pass: `python3.11 -m pytest -q`
- [ ] Linter passes: `python3.11 -m ruff check src tests`
- [ ] Documentation, screenshots, or artifacts required by the issue are included
- [ ] No new dependencies added unless explicitly required
- [ ] No changes to CI, packaging, or release configuration

## Development Notes

- Do not push directly to `master`.
- Do not force-push shared branches.
- Do not add new dependencies unless the issue explicitly requires them.
- Do not change CI, packaging, or release configuration for a documentation-only issue.
- Keep commits focused — one logical change per commit.

## Code Style

- Line length: 100 characters (configured in `pyproject.toml`)
- Linter: [ruff](https://docs.astral.sh/ruff/)
- Formatter: `ruff format src tests`
- Type hints: preferred for public functions
- Imports: use `isort` style (handled by ruff)

## Questions?

Open an issue on https://github.com/mergeos-bounties/NokaMan for discussion, or ask in the [MergeOS organization repo](https://github.com/mergeos-bounties/mergeos).