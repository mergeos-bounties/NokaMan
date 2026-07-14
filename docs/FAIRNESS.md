# Fairness Pack

This pack is a lightweight regression suite for score stability across English, Korean, and Japanese writing-style inputs with similar content length.

Run:

```bash
python -m nokaman.eval.fairness --out data/fixtures/fairness_report.json
```

The generated report includes per-sample rows, per-language means, and two headline metrics:

- `score_spread`: difference between the highest and lowest language mean score.
- `token_spread`: difference between the highest and lowest language mean token count.

The current suite is intentionally small. It is designed to catch obvious regressions in script handling, tokenizer behavior, and language priors before release. It is not a production fairness audit.

Mitigation guidance:

- Keep length-matched multilingual fixtures in CI and review large score spreads before release.
- Inspect tokenizer behavior for Hangul and Japanese scripts because character-based token counts can diverge from English word counts.
- Replace heuristic priors with calibration from labeled learner samples when moving beyond the demo model.
