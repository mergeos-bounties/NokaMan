# Supported Languages

NokaMan uses ISO-style language codes in the CLI, API payloads, sample files, and rubric registry. The current implementation is a toy/offline assessment scaffold: CEFR and regional exam labels are approximate product signals, not certified exam results.

## Catalog

| Code | Language | Registry frameworks | Rubric JSON | Sample count |
| --- | --- | --- | --- | ---: |
| `en` | English | CEFR, TOEIC, IELTS | `data/rubrics/en.json` | 6 |
| `ko` | Korean | CEFR, TOPIK | `data/rubrics/ko.json` | 3 |
| `ja` | Japanese | CEFR, JLPT | `data/rubrics/ja.json` | 5 |
| `vi` | Vietnamese | CEFR | `data/rubrics/vi.json` | 4 |
| `zh` | Chinese (Mandarin) | CEFR, HSK | `data/rubrics/zh.json` | 2 |
| `es` | Spanish | CEFR, DELE | fallback rubric | 4 |
| `fr` | French | CEFR, DELF | fallback rubric | 3 |
| `de` | German | CEFR, Goethe | fallback rubric | 4 |

Run the live catalog with:

```powershell
nokaman languages list
nokaman rubrics list
nokaman stats
```

## Skill Rubrics

Rubrics cover the same six skills for each full language pack:

| Skill | Purpose |
| --- | --- |
| `vocabulary` | Vocabulary range and lexical variety |
| `grammar` | Grammar complexity and control |
| `reading` | Reading comprehension proxy score |
| `writing` | Written production proxy score |
| `listening` | Listening comprehension proxy score |
| `speaking` | Spoken production proxy score |

The bundled full rubric JSON files weight `writing` at `1.2` and the other skills at `1.0`. Languages without a rubric JSON use the fallback rubric from `nokaman.rubrics.registry.load_language_rubric`.

## CEFR Score Bands

NokaMan maps its 0-100 toy model score to CEFR-style bands in `nokaman.models.cefr.score_to_cefr`.

| Score range | CEFR band |
| --- | --- |
| `0-34.99` | A1 |
| `35-49.99` | A2 |
| `50-64.99` | B1 |
| `65-79.99` | B2 |
| `80-89.99` | C1 |
| `90-100` | C2 |

Sample files may include `expected_cefr`; batch evaluation reports exact and adjacent CEFR hit rates against that field.

## Regional Framework Adapters

Regional labels are lightweight mappings used for demo UX and app contracts.

| CEFR | JLPT | TOPIK | HSK |
| --- | --- | --- | --- |
| A1 | N5 | 1 | 1 |
| A2 | N4 | 2 | 2 |
| B1 | N3 | 3 | 3 |
| B2 | N2 | 4 | 4 |
| C1 | N1 | 5 | 5 |
| C2 | N1+ | 6 | 6 |

English additionally emits approximate IELTS and TOEIC values from the raw score. These values are intentionally labeled approximate in the JSON payload.

## Add A New Language Pack

1. Add metadata to `SUPPORTED_LANGUAGES` in `src/nokaman/rubrics/registry.py`.
2. Add `data/rubrics/<code>.json` with `language`, `name`, `skills`, and `bands`.
3. Add at least one `data/samples/<code>_<skill>_<band>.json` file with `language`, `skill`, `text`, and `expected_cefr`.
4. Run `nokaman languages list`, `nokaman rubrics list -l <code>`, and `nokaman eval text -l <code> --text "..."`
5. Run `pytest -q` and `ruff check src tests`.

Keep the code value lowercase and reuse the six built-in skill names unless the scoring pipeline is updated at the same time.
