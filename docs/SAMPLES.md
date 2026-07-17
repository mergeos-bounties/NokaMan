# Language Sample Guide

NokaMan keeps offline evaluation samples in `data/samples/`. Each file is a
small, license-safe JSON document that the CLI and test suite can score without
network access.

## File naming

Use lowercase names in this form:

```text
<language>_<skill>_<cefr>[_description].json
```

For example, `en_writing_b1_email.json` describes an English writing sample
whose expected CEFR band is B1. The file stem should also be used as the `id`.

## Required fields

```json
{
  "id": "en_writing_b1_email",
  "language": "en",
  "skill": "writing",
  "expected_cefr": "B1",
  "text": "Hello, I am writing to ask about the course schedule."
}
```

| Field | Format | Purpose |
| --- | --- | --- |
| `id` | Unique lowercase string | Stable identifier in reports and tests |
| `language` | Lowercase language code | Selects the language metadata and rubric |
| `skill` | Built-in skill name | Selects the scoring dimension |
| `expected_cefr` | `A1`, `A2`, `B1`, `B2`, `C1`, or `C2` | Reference band for evaluation metrics |
| `text` | Non-empty UTF-8 string | Offline input scored by the toy model |

The built-in skill names are `vocabulary`, `grammar`, `reading`, `writing`,
`listening`, and `speaking`. Listening packs have a separate schema under
`data/listening/`; do not place question-based listening packs in this folder.

## How expected_cefr is used

`expected_cefr` is a reference label, not a model instruction. The evaluator
scores `text` first and then compares the predicted band with the reference:

- single-sample reports include a `band_check` result;
- batch reports calculate exact and adjacent-band hit rates;
- toy training reports calculate exact hit rate for labeled samples.

Choose the band from a reviewed learning objective or fixture design. Do not
change the label merely to match the current toy model output. These labels and
scores are approximate product signals, not certified language assessments.

## Add and verify a sample

1. Confirm the language is listed by `nokaman languages list`.
2. Add a license-safe JSON file under `data/samples/` using the fields above.
3. Keep personal data, copied exam questions, and proprietary course content
   out of fixtures.
4. Run the sample and batch evaluation paths:

```powershell
nokaman eval text --file data/samples/en_writing_b1_email.json
nokaman eval batch --out data/out/batch.json
pytest -q
ruff check src tests
```

If the language is new, also follow the registry and rubric steps in the
[supported language catalog](LANGUAGES.md#add-a-new-language-pack).
