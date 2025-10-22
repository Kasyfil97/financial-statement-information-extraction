import aiohttp
from typing import Dict, Any

class LLMClient:
    def __init__(self, config: Dict[str, Any]):
        self.api_endpoint = config['url']
        self.model = config['model']
        
    async def generate(self, prompt: str, temperature: float = 0.1) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "temperature": temperature
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_endpoint, json=payload) as resp:
                    resp.raise_for_status()
                    data = await resp.json()
                    return data.get("response", "")
        except aiohttp.ClientError as e:
            raise Exception(f"API request failed: {str(e)}")
        except ValueError as e:
            raise Exception(f"Invalid JSON response: {str(e)}")