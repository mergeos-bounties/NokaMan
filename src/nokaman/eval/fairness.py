from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean

from nokaman.config import RUNS_DIR
from nokaman.models.toy import ToyAbilityModel

LANGUAGES = ("en", "ko", "ja")

LENGTH_MATCHED_TEXTS = {
    "en": [
        (
            "en_daily_notes",
            "I study each morning, review new words, and write a short diary after class.",
        ),
        (
            "en_weekend_plan",
            "On Saturday I meet a friend, buy groceries, and explain my plans clearly.",
        ),
    ],
    "ko": [
        (
            "ko_daily_notes",
            "\uc800\ub294 \ub9e4\uc77c \uc544\uce68 \uacf5\ubd80\ud558\uace0 \uc0c8 \ub2e8\uc5b4\ub97c \ubcf5\uc2b5\ud55c \ub4a4 \uc9e7\uc740 \uc77c\uae30\ub97c \uc501\ub2c8\ub2e4.",
        ),
        (
            "ko_weekend_plan",
            "\ud1a0\uc694\uc77c\uc5d0 \uce5c\uad6c\ub97c \ub9cc\ub098\uace0 \uc7a5\uc744 \ubcf4\uba70 \ub0b4 \uacc4\ud68d\uc744 \uc27d\uac8c \uc124\uba85\ud569\ub2c8\ub2e4.",
        ),
    ],
    "ja": [
        (
            "ja_daily_notes",
            "\u6bce\u671d\u52c9\u5f37\u3057\u3066\u3001\u65b0\u3057\u3044\u5358\u8a9e\u3092\u5fa9\u7fd2\u3057\u3001\u6388\u696d\u306e\u5f8c\u306b\u77ed\u3044\u65e5\u8a18\u3092\u66f8\u304d\u307e\u3059\u3002",
        ),
        (
            "ja_weekend_plan",
            "\u571f\u66dc\u65e5\u306b\u53cb\u9054\u3068\u4f1a\u3044\u3001\u8cb7\u3044\u7269\u3092\u3057\u3066\u3001\u81ea\u5206\u306e\u4e88\u5b9a\u3092\u308f\u304b\u308a\u3084\u3059\u304f\u8aac\u660e\u3057\u307e\u3059\u3002",
        ),
    ],
}


def build_fairness_report() -> dict:
    rows = []
    for language in LANGUAGES:
        model = ToyAbilityModel(language)
        for sample_id, text in LENGTH_MATCHED_TEXTS[language]:
            scored = model.score_text(text, skill="writing")
            rows.append(
                {
                    "id": sample_id,
                    "language": language,
                    "char_count": _content_chars(text),
                    "token_count": scored["features"]["tokens"],
                    "score": scored["score"],
                    "cefr": scored["cefr"],
                    "script_bonus": scored["features"]["script_bonus"],
                }
            )

    by_language = {}
    for language in LANGUAGES:
        lang_rows = [row for row in rows if row["language"] == language]
        by_language[language] = {
            "n": len(lang_rows),
            "mean_chars": round(mean(row["char_count"] for row in lang_rows), 2),
            "mean_tokens": round(mean(row["token_count"] for row in lang_rows), 2),
            "mean_score": round(mean(row["score"] for row in lang_rows), 2),
            "mean_script_bonus": round(mean(row["script_bonus"] for row in lang_rows), 2),
        }

    mean_scores = [item["mean_score"] for item in by_language.values()]
    mean_tokens = [item["mean_tokens"] for item in by_language.values()]
    metrics = {
        "score_spread": round(max(mean_scores) - min(mean_scores), 2),
        "token_spread": round(max(mean_tokens) - min(mean_tokens), 2),
        "max_mean_score_language": max(by_language, key=lambda lang: by_language[lang]["mean_score"]),
        "min_mean_score_language": min(by_language, key=lambda lang: by_language[lang]["mean_score"]),
    }
    return {
        "suite": "length_matched_en_ko_ja",
        "model": "ToyAbilityModel",
        "skill": "writing",
        "languages": list(LANGUAGES),
        "rows": rows,
        "by_language": by_language,
        "metrics": metrics,
        "bias_notes": _bias_notes(metrics),
        "mitigations": [
            "Track score spread on length-matched multilingual fixtures before releases.",
            "Review script-specific tokenization because CJK/Hangul characters are tokenized differently.",
            "Calibrate language-specific priors with labeled learner samples before production use.",
        ],
    }


def write_fairness_report(path: Path | None = None) -> Path:
    out_path = path or (RUNS_DIR / "fairness_report.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(build_fairness_report(), indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    return out_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate EN/KO/JA length-matched fairness report.")
    parser.add_argument("--out", type=Path, default=RUNS_DIR / "fairness_report.json")
    args = parser.parse_args(argv)
    path = write_fairness_report(args.out)
    print(path)
    return 0


def _bias_notes(metrics: dict) -> list[str]:
    notes = []
    if metrics["score_spread"] >= 10:
        notes.append(
            "Mean score spread is at least 10 points, so reviewers should inspect language priors."
        )
    if metrics["token_spread"] >= 10:
        notes.append(
            "Token counts vary despite matched content length, indicating tokenizer sensitivity."
        )
    if not notes:
        notes.append("No large spread detected in this small fixture; keep monitoring with more data.")
    return notes


def _content_chars(text: str) -> int:
    return len("".join(ch for ch in text if not ch.isspace()))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
