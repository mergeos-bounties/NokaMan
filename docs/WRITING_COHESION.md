# Offline Writing Cohesion / Coherence Rubric

`nokaman.rubrics.writing_cohesion` provides deterministic stub dimensions for
product demos and tests that cannot use a paid writing API or human rater. It
scores two surface-level dimensions from 0 to 100:

| Dimension | Offline signal |
| --- | --- |
| `cohesion` | Connector density plus adjacent-sentence content-word overlap |
| `coherence` | Paragraph structure relative to sentence count plus paragraph topic continuity |

Samples can add optional observations without changing the normal sample
loader:

```json
{
  "skill": "writing",
  "text": "First I outline the idea. Then I explain the evidence. Therefore the conclusion is clear.",
  "cohesion_observations": {
    "paragraph_count": 1,
    "connector_count": 3
  }
}
```

Use `score_writing_cohesion()` for raw text or `score_writing_sample()` for a
sample dictionary. Both paths run locally and make no network requests.

## Limitations

- These stubs do not perform discourse parsing, coreference resolution, or
  semantic entailment. They only inspect connectors, overlap, and paragraph
  boundaries.
- The connector list is intentionally small and English-oriented. Non-English
  text may under-count cohesive devices.
- Blank-line paragraph detection fails for single-block essays, markdown lists,
  and HTML fragments unless `paragraph_count` is supplied.
- Adjacent lexical overlap can reward repetition rather than genuine progression.
- The weighted score is a product-development signal. It must not be presented
  as a certified CEFR / IELTS writing result or used for consequential decisions.

The result repeats these limitations so downstream interfaces cannot silently
drop the rubric's scope warning.
