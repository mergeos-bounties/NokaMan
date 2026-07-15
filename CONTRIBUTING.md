# Contributing to NokaMan

Thanks for helping improve NokaMan. This guide covers the local setup, validation commands, and MergeOS bounty flow for first-time contributors.

## Target Repository

Open pull requests against the public product repository:

https://github.com/mergeos-bounties/NokaMan

Do not target private mirrors or unrelated forks. Bounty work lands on the public `NokaMan` repository, normally against the `master` branch.

## Local Setup

NokaMan requires Python 3.11 or newer.

```bash
git clone https://github.com/mergeos-bounties/NokaMan.git
cd NokaMan
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e ".[dev]"
```

For the optional desktop GUI, install the GUI extra:

```bash
python -m pip install -e ".[dev,gui]"
```

## Run the Project

Use the CLI to confirm the package is installed correctly:

```bash
nokaman version
nokaman languages list
nokaman demo --lang en
```

For the optional GUI:

```bash
nokaman-gui
# or
nokaman gui
```

## Tests and Checks

Run the focused checks before opening a PR:

```bash
python3.11 -m compileall src tests
python3.11 -m pytest -q
python3.11 -m ruff check src tests
```

If the local `build` package is available, also run:

```bash
python3.11 -m build
```

For documentation-only changes, `pytest` and `ruff` are still useful because they catch accidental packaging or import regressions.

## Good First Issue Path

1. Pick an issue labeled `good first issue`, `help wanted`, or `bounty`.
2. Read the full issue description and acceptance criteria.
3. Comment `I claim this bounty` on the issue before starting.
4. Create a feature branch from the latest `master`.
5. Keep the change scoped to the issue. Avoid unrelated refactors, dependency changes, or CI changes.
6. Run the checks listed above.
7. Open a PR to `mergeos-bounties/NokaMan` and include `Fixes #<issue-number>`.

## MergeOS Bounty Claim Flow

For MergeOS MRG bounties:

1. Star `https://github.com/mergeos-bounties/NokaMan` and `https://github.com/mergeos-bounties/mergeos`.
2. Comment `I claim this bounty` on the NokaMan bounty issue.
3. Comment on MergeOS Claim Token #1 with a link to the bounty issue.
4. Open a PR to the public NokaMan repository.
5. Include a short summary, test output, and any required screenshots or artifacts from the issue.

Maintainers review the PR and credit MRG after merge according to the bounty policy.

## Pull Request Checklist

- The PR targets `mergeos-bounties/NokaMan`.
- The PR description links the issue with `Fixes #<issue-number>`.
- The change is limited to the requested scope.
- Tests and checks are listed in the PR description.
- Documentation, screenshots, or artifacts required by the issue are included.

## Development Notes

- Do not push directly to `master`.
- Do not force-push shared branches.
- Do not add new dependencies unless the issue explicitly requires them.
- Do not change CI, packaging, or release configuration for a documentation-only issue.
