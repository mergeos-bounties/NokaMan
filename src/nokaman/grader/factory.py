import os
from typing import Optional
from .base import BaseGrader
from .toy import ToyGrader
from .llm import LLMGrader

def get_grader(force_llm: bool = False) -> BaseGrader:
    """
    Factory to return the appropriate grader based on environment configuration.
    Defaults to ToyGrader if no API key is found or if not forced.
    """
    api_key = os.getenv("NOKAMAN_LLM_API_KEY")
    
    if (force_llm or api_key) and os.getenv("NOKAMAN_USE_LLM", "false").lower() == "true":
        return LLMGrader()
    
    return ToyGrader()
