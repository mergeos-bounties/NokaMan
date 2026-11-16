import pytest
import os
from nokaman.grader.factory import get_grader
from nokaman.grader.toy import ToyGrader
from nokaman.grader.llm import LLMGrader

def test_toy_grader_logic():
    grader = ToyGrader()
    rubric = {"name": "General English"}
    
    # Test short submission
    res_a1 = grader.grade("Hello world.", rubric)
    assert res_a1["cefr_level"] == "A1"
    
    # Test long submission
    long_text = " ".join(["word"] * 101)
    res_b2 = grader.grade(long_text, rubric)
    assert res_b2["cefr_level"] == "B2"

def test_factory_defaults_to_toy():
    # Ensure environment doesn't interfere with this test
    if "NOKAMAN_LLM_API_KEY" in os.environ:
        del os.environ["NOKAMAN_LLM_API_KEY"]
    
    grader = get_grader()
    assert isinstance(grader, ToyGrader)

def test_llm_grader_requires_key():
    grader = LLMGrader(api_key=None)
    with pytest.raises(ValueError, match="API Key is missing"):
        grader.grade("test", {})

@pytest.mark.skipif(not os.getenv("NOKAMAN_LLM_API_KEY"), reason="Requires live API key")
def test_live_llm_grader():
    # This test only runs if a key is provided manually
    grader = LLMGrader()
    rubric = {"name": "Testing"}
    result = grader.grade("This is a test submission for the LLM grader.", rubric)
    assert "cefr_level" in result
    assert "overall_score" in result
