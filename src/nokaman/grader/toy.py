from typing import Any, Dict
from .base import BaseGrader

class ToyGrader(BaseGrader):
    """
    Default 'Toy' model for local testing and CI.
    Provides deterministic, rule-based grading based on string length and keyword matching.
    """
    def grade(self, submission: str, rubric: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        # Simple heuristic: longer text = higher CEFR potential in this toy model
        length = len(submission.split())
        
        if length > 100:
            level = "B2"
            score = 85
        elif length > 50:
            level = "B1"
            score = 70
        elif length > 20:
            level = "A2"
            score = 50
        else:
            level = "A1"
            score = 30

        return {
            "model": "ToyAbilityModel",
            "overall_score": score,
            "cefr_level": level,
            "feedback": "Graded by local toy model. Submission length: {} words.".format(length),
            "rubric_applied": rubric.get("name", "unknown")
        }
