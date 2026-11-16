from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseGrader(ABC):
    """
    Abstract base class for all NokaMan graders.
    """
    @abstractmethod
    def grade(self, submission: str, rubric: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Evaluates a submission based on a provided rubric.
        
        :param submission: The text or content to be graded.
        :param rubric: The CEFR-style rubric dictionary.
        :param context: Optional metadata (language, level, task type).
        :return: A dictionary containing scores, feedback, and CEFR level.
        """
        pass
