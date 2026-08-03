# Placement packs for language apps

NokaMan ships **license-safe** placement packs under `data/placement/` for embedding
in a learning app. Minimum languages: **EN, KO, JA**.

## Single product path

CLI:

```bash
# Sample evidence reports (bundled demo answers)
nokaman eval placement-pack --lang en --demo
nokaman eval placement-pack --lang ko --demo
nokaman eval placement-pack --lang ja --demo

# Real learner answers (same order as pack prompts)
nokaman eval placement-pack --lang en \
  -a "I wake up early..." \
  -a "Hi, my name is..." \
  -a "The library is closed..." \
  -a "Yesterday I went..."
```

API (`nokaman[api]`):

```http
POST /assess/placement-pack
{"language":"en","use_demo_answers":true}
```

or with learner answers:

```http
POST /assess/placement-pack
{"language":"ko","answers":["...","...","...","..."]}
```

Reports include `pack_id`, `overall`, `cefr`, per-item `prompt`/`answer`/`score`,
and `ready_for_ui: true`. Sample demo runs set `sample_report: true`.

## Pack files

| File | Language |
| --- | --- |
| `data/placement/en.json` | English |
| `data/placement/ko.json` | Korean |
| `data/placement/ja.json` | Japanese |

Each pack lists prompts + synthetic `demo_answer` text (no scraped PII, MIT-safe).
