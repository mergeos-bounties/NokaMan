# CEFR Mapping Notes

## Overview

NokaMan uses the Common European Framework of Reference (CEFR) for language proficiency levels.

## Levels

| Level | Description | Can Do |
|-------|-------------|--------|
| A1 | Beginner | Basic phrases, simple interactions |
| A2 | Elementary | Routine tasks, simple descriptions |
| B1 | Intermediate | Main points, travel situations |
| B2 | Upper Intermediate | Complex texts, fluent interaction |
| C1 | Advanced | Wide range, flexible language use |
| C2 | Proficient | Near-native, spontaneous expression |

## expected_cefr Field

The `expected_cefr` field in evaluation samples indicates the target proficiency level.

### Limits

- Toy model uses simplified scoring
- Actual CEFR assessment requires certified examiners
- Scores are approximate indicators, not definitive

### Usage

```json
{
  "id": "writing_b1_01",
  "prompt": "Write about your travel experience...",
  "expected_cefr": "B1",
  "word_count_target": "120-180"
}
```

## Scoring

The evaluation rubric considers:
- Vocabulary range and accuracy
- Grammar complexity
- Coherence and cohesion
- Task completion

Scores map to CEFR levels with ±0.5 tolerance.
