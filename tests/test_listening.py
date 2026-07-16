from __future__ import annotations

from nokaman.data.loader import list_listening_pack_files, load_listening_pack
from nokaman.eval.listening import evaluate_listening_pack_file, score_listening_pack


def test_listening_loader_reads_fixture_packs() -> None:
    files = list_listening_pack_files()
    assert len(files) >= 2
    pack = load_listening_pack(files[0])
    assert pack["skill"] == "listening"
    assert pack["items"]


def test_score_listening_pack_supports_mcq_and_short_answer() -> None:
    result = score_listening_pack(
        {
            "id": "inline_pack",
            "language": "en",
            "difficulty_cefr": "B1",
            "questions": [
                {"id": "q1", "type": "mcq", "answer": "A", "response": "A"},
                {"id": "q2", "type": "mcq", "answer": "B", "response": "C"},
                {
                    "id": "q3",
                    "type": "short_answer",
                    "accepted_answers": ["by email"],
                    "keywords": ["email", "lunch"],
                    "response": "They send it by email before lunch.",
                    "weight": 2,
                },
            ],
        }
    )
    assert result["skill"] == "listening"
    assert result["accuracy"] == 75.0
    assert result["cefr"] == "B1"
    assert result["items"][2]["credit"] == 1.0


def test_evaluate_listening_fixture_includes_band_check() -> None:
    path = next(path for path in list_listening_pack_files() if path.name == "en_a2_commute.json")
    result = evaluate_listening_pack_file(path)
    assert result["language"] == "en"
    assert result["n_items"] == 3
    assert result["band_check"]["exact_match"]
    assert result["source"].endswith("en_a2_commute.json")
