import logging
import re
import json
from typing import Dict, Any
from src.llm_client import LLMClient

logger = logging.getLogger(__name__)


class Extractor:
    """
    Financial Statement Extractor using Ollama Llama3.1:8b
    Performs:
    - Text extraction from PDF
    - Automatic categorization
    - Key metrics extraction per section
    - Validation & structured JSON output
    """

    def __init__(self, llm_client: LLMClient, sections: Dict[str, str]):
        self.llm_client = llm_client
        self.sections = sections

    def _clean_json_text(self, text: str) -> str:
        """Clean common formatting issues from LLM JSON responses"""
        text = re.sub(r'(\d),(\d)', r'\1\2', text)
        text = re.sub(r',(\s*[}\]])', r'\1', text)
        text = re.sub(r'\bNone\b', 'null', text, flags=re.IGNORECASE)
        return text
    
    async def extract(self, prompt_input: str, sections: Dict[str, str], temperature: float = 0.1) -> Dict[str, Any]:
        """Extract key metrics for each financial section"""
        results = {}

        for category, text in sections.items():
            logger.info("Extracting key metrics for: %s", category)
            prompt = prompt_input.format(sections=category, text=text)
            response = await self.llm_client.generate(prompt=prompt,
                                                      temperature=temperature)
            cleaned = self._clean_json_text(response)
            
            try:
                parsed = json.loads(cleaned)
                if "metrics" in parsed and isinstance(parsed["metrics"], dict):
                    parsed["validation"] = self.validate_metrics(parsed["metrics"])
                results[category] = parsed
            except json.JSONDecodeError:
                logger.warning("Invalid JSON returned for %s (first 200 chars): %s", category, (response or '')[:200])
                results[category] = {"error": "Invalid JSON", "raw": response}

        return results
