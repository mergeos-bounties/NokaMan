# NokaMan Placement Test Pack

This directory contains placement test packs for multiple languages. Each pack includes:

- **Prompts**: 5 writing prompts covering CEFR levels A1-C1
- **Scoring**: Weighted average scoring method
- **Report**: JSON format output suitable for embedding in language apps

## Available Packs

- `en_placement.json` - English placement test
- `ko_placement.json` - Korean placement test  
- `ja_placement.json` - Japanese placement test

## Usage

### CLI

```bash
# Run placement test with answers
nokaman eval placement --lang en --answer "I like reading books." --answer "I will go shopping."
```

### Python API

```python
from nokaman.eval.metrics import placement_test

result = placement_test(
    language="en",
    answers=[
        "I like reading books.",
        "I will go shopping.",
        "I prepare by researching the company."
    ]
)
print(result)
```

### API Endpoint

```bash
POST /assess/placement
{
  "language": "en",
  "answers": ["answer1", "answer2", "answer3"]
}
```

## Report Format

The placement test returns a JSON report with:

```json
{
  "language": "en",
  "n_items": 3,
  "overall": 65.2,
  "cefr": "B1",
  "items": [
    {
      "item": 1,
      "text": "I like reading books.",
      "overall": 55.3,
      "cefr": "A2",
      "skills": {
        "vocabulary": 50.1,
        "grammar": 52.5,
        "writing": 55.3
      }
    }
  ],
  "ready_for_ui": true
}
```

## Framework Bands

The report includes framework-specific bands:

- **English**: IELTS, TOEIC approximations
- **Japanese**: JLPT levels (N5-N1)
- **Korean**: TOPIK levels (1-6)

## License

All prompts and content are license-safe for commercial use.
