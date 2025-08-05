import requests
import json
import time
import logging
import os
from typing import Dict, Any, Optional
from .config import LLM_CONFIG

class LLMClient:
    """Client for communicating with various LLM providers (Ollama, Grok Cloud, Croq Cloud)"""
    
    def __init__(self, provider: str = None, base_url: str = None, api_key: str = None):
        self.provider = provider or LLM_CONFIG.get("provider", "ollama")
        self.base_url = base_url or LLM_CONFIG.get("base_url", "http://localhost:11434")
        self.api_key = api_key or LLM_CONFIG.get("api_key")
        self.model = LLM_CONFIG["model"]
        self.logger = logging.getLogger(__name__)
        self.performance_stats = {
            "total_requests": 0,
            "total_tokens": 0,
            "total_time": 0,
            "avg_response_time": 0
        }
        
        # Provider-specific configurations
        self.provider_configs = {
            "ollama": {
                "generate_endpoint": "/api/generate",
                "models_endpoint": "/api/tags",
                "headers": {"Content-Type": "application/json"},
                "timeout": 300
            },
            "grok_cloud": {
                "generate_endpoint": "/openai/v1/chat/completions",
                "models_endpoint": "/openai/v1/models",
                "headers": {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                },
                "timeout": 120
            },
            "croq_cloud": {
                "generate_endpoint": "/v1/chat/completions",
                "models_endpoint": "/v1/models",
                "headers": {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                },
                "timeout": 120
            }
        }
        
    def check_model_availability(self) -> bool:
        """Check if the specified model is available"""
        try:
            config = self.provider_configs.get(self.provider)
            if not config:
                self.logger.error(f"Unsupported provider: {self.provider}")
                return False
                
            response = requests.get(
                f"{self.base_url}{config['models_endpoint']}", 
                headers=config['headers'],
                timeout=10
            )
            
            if response.status_code == 200:
                if self.provider == "ollama":
                    models = response.json().get("models", [])
                    available_models = [model["name"] for model in models]
                else:
                    # For cloud providers, models are typically available
                    available_models = [self.model]
                
                if self.model in available_models:
                    self.logger.info(f"Using {self.provider} model: {self.model}")
                    return True
                else:
                    self.logger.error(f"Model {self.model} not found. Available models: {available_models}")
                    return False
            return False
        except Exception as e:
            self.logger.error(f"Error checking model availability: {e}")
            return False
    
    def _build_ollama_payload(self, prompt: str) -> Dict[str, Any]:
        """Build payload for Ollama"""
        options = {
            "temperature": LLM_CONFIG["temperature"],
            "top_p": LLM_CONFIG["top_p"],
            "num_predict": LLM_CONFIG["max_tokens"],
            "num_ctx": LLM_CONFIG["num_ctx"],
            "num_gpu": LLM_CONFIG["num_gpu"],
            "num_thread": LLM_CONFIG["num_thread"],
            "repeat_penalty": LLM_CONFIG["repeat_penalty"],
            "seed": LLM_CONFIG["seed"],
            "tfs_z": LLM_CONFIG["tfs_z"],
            "top_k": LLM_CONFIG["top_k"],
            "use_mlock": LLM_CONFIG["use_mlock"],
            "use_mmap": LLM_CONFIG["use_mmap"],
            "rope_freq_base": LLM_CONFIG["rope_freq_base"],
            "rope_freq_scale": LLM_CONFIG["rope_freq_scale"]
        }
        
        return {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": options
        }
    
    def _build_cloud_payload(self, prompt: str) -> Dict[str, Any]:
        """Build payload for cloud providers (Grok, Croq, etc.)"""
        return {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a sustainability reporting expert specializing in SASB standards and ESG metrics."},
                {"role": "user", "content": prompt}
            ],
            "temperature": LLM_CONFIG["temperature"],
            "max_tokens": LLM_CONFIG["max_tokens"],
            "top_p": LLM_CONFIG["top_p"],
            "frequency_penalty": LLM_CONFIG.get("frequency_penalty", 0.1),
            "presence_penalty": LLM_CONFIG.get("presence_penalty", 0.1)
        }
    
    def _extract_response(self, response_data: Dict[str, Any]) -> str:
        """Extract response text based on provider format"""
        if self.provider == "ollama":
            return response_data.get("response", "")
        else:
            # Cloud providers use OpenAI-compatible format
            choices = response_data.get("choices", [])
            if choices:
                message = choices[0].get("message", {})
                return message.get("content", "")
            return ""
    
    def generate_response(self, prompt: str, max_retries: int = 1) -> Optional[str]:
        """Generate response from LLM with retry logic and performance tracking"""
        
        config = self.provider_configs.get(self.provider)
        if not config:
            self.logger.error(f"Unsupported provider: {self.provider}")
            return None
        
        # Build payload based on provider
        if self.provider == "ollama":
            payload = self._build_ollama_payload(prompt)
        else:
            payload = self._build_cloud_payload(prompt)
        
        start_time = time.time()
        
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    f"{self.base_url}{config['generate_endpoint']}",
                    json=payload,
                    headers=config['headers'],
                    timeout=config['timeout']
                )
                
                if response.status_code == 200:
                    result = response.json()
                    response_text = self._extract_response(result)
                    
                    # Update performance stats
                    end_time = time.time()
                    response_time = end_time - start_time
                    self.performance_stats["total_requests"] += 1
                    self.performance_stats["total_time"] += response_time
                    self.performance_stats["avg_response_time"] = (
                        self.performance_stats["total_time"] / self.performance_stats["total_requests"]
                    )
                    
                    # Log performance metrics less frequently for speed
                    if self.performance_stats["total_requests"] % 20 == 0:
                        self.logger.info(f"Performance: Avg response time: {self.performance_stats['avg_response_time']:.2f}s, "
                                        f"Total requests: {self.performance_stats['total_requests']}")
                    
                    return response_text
                else:
                    self.logger.warning(f"Attempt {attempt + 1}: HTTP {response.status_code} - {response.text}")
                    
            except requests.exceptions.Timeout:
                self.logger.warning(f"Attempt {attempt + 1}: Timeout after {config['timeout']}s, moving to next topic")
            except Exception as e:
                self.logger.error(f"Attempt {attempt + 1}: Error - {e}")
            
            if attempt < max_retries - 1:
                time.sleep(1)  # Short backoff
        
        self.logger.error("All retry attempts failed")
        return None
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get current performance statistics"""
        return self.performance_stats.copy()
    
    def test_connection(self) -> bool:
        """Test if the LLM service is running and accessible"""
        try:
            config = self.provider_configs.get(self.provider)
            if not config:
                self.logger.error(f"Unsupported provider: {self.provider}")
                return False
                
            response = requests.get(
                f"{self.base_url}{config['models_endpoint']}", 
                headers=config['headers'],
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False 