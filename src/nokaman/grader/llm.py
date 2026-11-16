import os
import json
from typing import Any, Dict, Optional
from .base import BaseGrader

try:
    import httpx
except ImportError:
    httpx = None

class LLMGrader(BaseGrader):
    """
    LLM-backed grader using httpx. 
    Compatible with OpenAI-style chat completion endpoints (SpaceXAI, etc.).
    """
    def __init__(
        self, 
        api_key: Optional[str] = None, 
        base_url: Optional[str] = None, 
        model_name: str = "gpt-4o"
    ):
        self.api_key = api_key or os.getenv("NOKAMAN_LLM_API_KEY")
        self.base_url = base_url or os.getenv("NOKAMAN_LLM_BASE_URL", "https://api.openai.com/v1")
        self.model_name = model_name or os.getenv("NOKAMAN_LLM_MODEL", "gpt-4o")

    def grade(self, submission: str, rubric: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        if not httpx:
            raise ImportError("The 'httpx' library is required for LLMGrader. Install with: pip install 'nokaman[llm]'")
        
        if not self.api_key:
            raise ValueError("API Key is missing. Set NOKAMAN_LLM_API_KEY environment variable.")

        prompt = self._build_prompt(submission, rubric, context)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": "You are a professional CEFR language examiner. Output JSON only."},
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"}
        }

        with httpx.Client(timeout=30.0) as client:
            response = client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            
            content = result["choices"][0]["message"]["content"]
            return json.loads(content)

    def _build_prompt(self, submission: str, rubric: Dict[str, Any], context: Dict[str, Any]) -> str:
        return f"""
        Evaluate the following language learner submission based on the provided rubric.
        
        Rubric:
        {json.dumps(rubric, indent=2)}
        
        Context:
        {json.dumps(context or {}, indent=2)}
        
        Submission:
        \"\"\"{submission}\"\"\"
        
        Return a JSON object with:
        - overall_score (0-100)
        - cefr_level (A1-C2)
        - feedback (detailed string)
        - model (string: "{self.model_name}")
        """
