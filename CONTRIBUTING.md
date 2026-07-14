# Contributing to NokaMan

Thanks for contributing! NokaMan is a multi-language learning ability assessment tool built with Python.

## Quick Start

```bash
git clone https://github.com/mergeos-bounties/NokaMan.git
cd NokaMan
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Development Loop

1. **Pick an issue** — browse [open bounties](https://github.com/mergeos-bounties/NokaMan/issues?q=is%3Aissue+is%3Aopen+label%3Abounty) labelled `bounty`
2. **Claim it** — comment `I claim this bounty` on the issue AND on [MergeOS Claim Token #1](https://github.com/mergeos-bounties/mergeos/issues/1)
3. **Create a branch** — `git checkout -b fix/issue-NN-short-description`
4. **Implement** — write code + tests
5. **Verify locally**:
   ```bash
   ruff check src tests
   ruff format --check src tests
   pytest -q --cov=src --cov-report=term
   ```
6. **Push and open PR** — target `master`, reference the issue with `Closes #NN`
7. **Update PROGRESS.md** — add your completed item

## Acceptance Gates

All PRs must pass:

| Gate | Command | Notes |
|------|---------|-------|
| Type check | `python -m compileall src tests` | No syntax errors |
| Tests | `pytest -q` | All tests pass |
| Lint | `ruff check src tests` | No lint errors |
| Format | `ruff format --check src tests` | Consistent formatting |
| Coverage | `pytest --cov=src --cov-report=term` | CI enforces threshold |

## Good First Issues

Look for issues labelled [`good first issue`](https://github.com/mergeos-bounties/NokaMan/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22). These are small, self-contained tasks ideal for new contributors:

- Documentation improvements
- Test coverage additions
- Small CLI features
- Sample data contributions

## MergeOS Bounty Flow

NokaMan bounties follow the MergeOS payment system:

1. **Claim** on the issue + MergeOS Claim Token #1
2. **Submit PR** to `mergeos-bounties/NokaMan` (NOT a personal fork)
3. PRs must target the public `mergeos-bounties/NokaMan` repository only
4. After merge, MRG tokens are awarded through the MergeOS ledger

## Need Help?

- Comment on the issue you're working on
- Check existing PRs for examples of accepted contributions
- Read `AGENTS.md` for automated contribution rules
