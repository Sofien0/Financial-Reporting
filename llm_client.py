import requests
import json
import time
import logging
from typing import Dict, Any, Optional
from config import LLM_CONFIG

class LLMClient:
    """Client for communicating with Ollama LLM"""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.model = LLM_CONFIG["model"]
        self.logger = logging.getLogger(__name__)
        
    def check_model_availability(self) -> bool:
        """Check if the specified model is available"""
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                available_models = [model["name"] for model in models]
                return self.model in available_models
            return False
        except Exception as e:
            self.logger.error(f"Error checking model availability: {e}")
            return False
    
    def generate_response(self, prompt: str, max_retries: int = 3) -> Optional[str]:
        """Generate response from LLM with retry logic"""
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": LLM_CONFIG["temperature"],
                "top_p": LLM_CONFIG["top_p"],
                "num_predict": LLM_CONFIG["max_tokens"]
            }
        }
        
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=600  # 2 minutes timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get("response", "")
                else:
                    self.logger.warning(f"Attempt {attempt + 1}: HTTP {response.status_code}")
                    
            except requests.exceptions.Timeout:
                self.logger.warning(f"Attempt {attempt + 1}: Timeout")
            except Exception as e:
                self.logger.error(f"Attempt {attempt + 1}: Error - {e}")
            
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
        
        self.logger.error("All retry attempts failed")
        return None
    
    def test_connection(self) -> bool:
        """Test if Ollama is running and accessible"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False 