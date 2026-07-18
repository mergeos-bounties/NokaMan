"""Test placement test functionality."""
from pathlib import Path

from nokaman.data.loader import list_placement_files, load_placement_pack
from nokaman.eval.metrics import placement_test


def test_placement_files_exist():
    """Test that placement files are created."""
    files = list_placement_files()
    assert len(files) >= 3, f"Expected at least 3 placement packs, got {len(files)}"
    
    pack_ids = {f.stem for f in files}
    assert "en_placement" in pack_ids, "English placement pack not found"
    assert "ko_placement" in pack_ids, "Korean placement pack not found"
    assert "ja_placement" in pack_ids, "Japanese placement pack not found"


def test_placement_pack_structure():
    """Test placement pack structure."""
    files = list_placement_files()
    
    for path in files:
        pack = load_placement_pack(path)
        assert "id" in pack, f"Pack {path.stem} missing 'id'"
        assert "language" in pack, f"Pack {path.stem} missing 'language'"
        assert "prompts" in pack, f"Pack {path.stem} missing 'prompts'"
        assert len(pack["prompts"]) == 5, f"Pack {path.stem} should have 5 prompts"
        
        for prompt in pack["prompts"]:
            assert "id" in prompt, f"Prompt missing 'id' in {path.stem}"
            assert "text" in prompt, f"Prompt missing 'text' in {path.stem}"
            assert "cefr" in prompt, f"Prompt missing 'cefr' in {path.stem}"


def test_placement_test_execution():
    """Test placement test execution."""
    # Test English
    result_en = placement_test("en", [
        "I like reading books.",
        "I will go shopping this weekend.",
        "I prepare for interviews by researching the company."
    ])
    assert result_en["language"] == "en"
    assert result_en["n_items"] == 3
    assert "cefr" in result_en
    assert "overall" in result_en
    assert result_en["ready_for_ui"] is True
    
    # Test Korean
    result_ko = placement_test("ko", [
        "저는 책을 읽는 것을 좋아합니다.",
        "이번 주말에 쇼핑을 갈 예정입니다."
    ])
    assert result_ko["language"] == "ko"
    assert result_ko["n_items"] == 2
    
    # Test Japanese
    result_ja = placement_test("ja", [
        "私は本を読むのが好きです。",
        "今週末は買い物に行く予定です。"
    ])
    assert result_ja["language"] == "ja"
    assert result_ja["n_items"] == 2


def test_placement_report_structure():
    """Test placement report structure."""
    result = placement_test("en", [
        "I like reading books.",
        "I will go shopping this weekend."
    ])
    
    assert "language" in result
    assert "n_items" in result
    assert "overall" in result
    assert "cefr" in result
    assert "items" in result
    assert "ready_for_ui" in result
    
    for item in result["items"]:
        assert "item" in item
        assert "text" in item
        assert "overall" in item
        assert "cefr" in item
        assert "skills" in item
