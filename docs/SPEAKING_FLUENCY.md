# Offline Speaking Fluency Rubric

`nokaman.rubrics.speaking_fluency` provides a deterministic placeholder for
product demos and tests that cannot use a recording, speech service, or paid
API. It scores four transcript-level dimensions from 0 to 100:

| Dimension | Offline signal |
| --- | --- |
| `pace` | Words per minute when duration is available |
| `continuity` | Explicit pause count or punctuation-based estimate |
| `filler_control` | Explicit count or a small built-in filler-word list |
| `phrase_length` | Average words between punctuation boundaries |

Samples can add optional observations without changing the normal sample
loader:

```json
{
  "skill": "speaking",
  "text": "I practiced my presentation and explained the main result.",
  "fluency_observations": {
    "duration_seconds": 12.0,
    "pause_count": 1,
    "filler_count": 0
  }
}
```

Use `score_speaking_fluency()` for a transcript or `score_speaking_sample()`
for a sample dictionary. Both paths run locally and make no network requests.

## Limitations

- A transcript cannot measure pronunciation, stress, intonation, hesitation
  length, turn-taking, or recording quality.
- Punctuation is only a rough pause proxy. Supply an observed `pause_count`
  when a trusted offline collection process provides one.
- The built-in filler list is intentionally small and English-oriented.
- Token counts are least reliable for languages that do not separate words
  with spaces.
- The weighted score is a product-development signal. It must not be presented
  as a certified CEFR speaking result or used for consequential decisions.

The result repeats these limitations so downstream interfaces cannot silently
drop the rubric's scope warning.
