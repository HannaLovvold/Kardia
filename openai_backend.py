"""OpenAI-compatible API backend for AI companion."""
import json
import requests
from typing import List, Dict, Optional
import threading


class OpenAIBackend:
    """Handles communication with OpenAI-compatible APIs."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-3.5-turbo",
        additional_params: str = None,
    ):
        """
        Initialize OpenAI backend.

        Args:
            api_key: API key for authentication
            base_url: API base URL (default: OpenAI)
            model: Model name to use
            additional_params: Optional JSON string with additional parameters
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.additional_params = additional_params
        self.chat_url = f"{self.base_url}/chat/completions"
        self._available = None

    def check_connection(self) -> bool:
        """Check if API is accessible."""
        if self._available is not None:
            return self._available

        try:
            # Try a minimal request to check connection
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            # Use models endpoint to check connection
            models_url = f"{self.base_url}/models"
            response = requests.get(models_url, headers=headers, timeout=10)

            self._available = response.status_code in [200, 401]  # 401 means server is up but key is invalid
            return self._available

        except Exception:
            self._available = False
            return False

    def generate_response(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        stream: bool = False,
        callback=None,
    ) -> str:
        """
        Generate a response from the AI.

        Args:
            messages: List of message dicts with 'role' and 'content'
            system_prompt: Optional system prompt to set context
            stream: Whether to stream the response
            callback: Optional callback for streaming updates

        Returns:
            The AI's response text
        """
        if not self.api_key:
            return "Error: No API key configured. Please set your API key in Settings."

        if not self.check_connection():
            return "Error: Cannot connect to API. Please check your internet connection and API URL."

        # Prepare the payload
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
        }

        # Add system prompt if provided
        if system_prompt:
            payload["messages"].insert(0, {"role": "system", "content": system_prompt})

        # Add additional parameters if provided
        if self.additional_params:
            try:
                import json
                additional_params = json.loads(self.additional_params)
                if isinstance(additional_params, dict):
                    # Merge additional parameters into payload
                    # Note: If there are conflicts, additional_params take precedence
                    payload.update(additional_params)
            except json.JSONDecodeError:
                # If JSON is invalid, just ignore it
                print(f"Warning: Invalid additional parameters JSON: {self.additional_params}")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            if stream and callback:
                # Streaming response
                return self._stream_response(payload, headers, callback)
            else:
                # Non-streaming response
                response = requests.post(self.chat_url, json=payload, headers=headers, timeout=120)
                response.raise_for_status()
                result = response.json()

                if "choices" in result and len(result["choices"]) > 0:
                    return result["choices"][0]["message"]["content"]
                return ""

        except requests.exceptions.HTTPError as e:
            error_msg = f"API Error: {e.response.status_code}"
            try:
                error_detail = e.response.json()
                if "error" in error_detail:
                    error_msg += f" - {error_detail['error'].get('message', 'Unknown error')}"
            except:
                pass
            return error_msg

        except requests.exceptions.Timeout:
            return "Error: Request timed out. The API might be busy."

        except requests.exceptions.RequestException as e:
            return f"Error communicating with API: {str(e)}"

        except Exception as e:
            return f"Unexpected error: {str(e)}"

    def _stream_response(self, payload: Dict, headers: Dict, callback) -> str:
        """Handle streaming response from API."""
        full_response = ""

        try:
            response = requests.post(
                self.chat_url,
                json=payload,
                headers=headers,
                stream=True,
                timeout=120,
            )

            response.raise_for_status()

            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data_str = line[6:]  # Remove 'data: ' prefix

                        if data_str.strip() == '[DONE]':
                            break

                        try:
                            data = json.loads(data_str)
                            if "choices" in data and len(data["choices"]) > 0:
                                delta = data["choices"][0].get("delta", {})
                                content = delta.get("content", "")
                                full_response += content
                                callback(content)
                        except json.JSONDecodeError:
                            continue

            return full_response

        except Exception as e:
            return f"Streaming error: {str(e)}"

    def generate_async(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        callback=None,
    ):
        """
        Generate a response asynchronously.

        Args:
            messages: List of message dicts
            system_prompt: Optional system prompt
            callback: Function to call with the result
        """
        def _generate():
            result = self.generate_response(messages, system_prompt)
            if callback:
                callback(result)

        thread = threading.Thread(target=_generate, daemon=True)
        thread.start()

    @staticmethod
    def get_popular_providers() -> Dict[str, Dict]:
        """Get popular OpenAI-compatible API providers."""
        return {
            "openai": {
                "name": "OpenAI",
                "base_url": "https://api.openai.com/v1",
                "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
                "key_url": "https://platform.openai.com/api-keys",
                "free_tier": False,
            },
            "groq": {
                "name": "Groq",
                "base_url": "https://api.groq.com/openai/v1",
                "models": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"],
                "key_url": "https://console.groq.com/keys",
                "free_tier": True,
            },
            "deepseek": {
                "name": "DeepSeek",
                "base_url": "https://api.deepseek.com/v1",
                "models": ["deepseek-chat", "deepseek-coder"],
                "key_url": "https://platform.deepseek.com/",
                "free_tier": True,
            },
            "together": {
                "name": "Together AI",
                "base_url": "https://api.together.xyz/v1",
                "models": ["meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo", "mistralai/Mixtral-8x7B-Instruct-v0.1"],
                "key_url": "https://api.together.xyz/settings/api-keys",
                "free_tier": True,
            },
            "openrouter": {
                "name": "OpenRouter",
                "base_url": "https://openrouter.ai/api/v1",
                "models": ["anthropic/claude-3-haiku", "meta-llama/llama-3-70b"],
                "key_url": "https://openrouter.ai/keys",
                "free_tier": True,
            },
        }

    @staticmethod
    def get_setup_instructions(provider: str = "openai") -> str:
        """Get instructions for setting up an API provider."""
        providers = OpenAIBackend.get_popular_providers()

        if provider in providers:
            p = providers[provider]
            return f"""
To set up {p['name']}:

1. Get your API key:
   Go to {p['key_url']}

2. Create or copy your API key

3. In the app:
   - Go to Settings > API
   - Select {p['name']} as the provider
   - Paste your API key
   - Choose a model

4. Click "Test Connection" to verify

{'Note: ' + p['name'] + ' has a free tier!' if p.get('free_tier') else 'Note: ' + p['name'] + ' requires a paid account.'}
"""
        else:
            return """
To set up a custom OpenAI-compatible API:

1. Get your API key and base URL from your provider

2. In the app:
   - Go to Settings > API
   - Select "Custom" as the provider
   - Enter your base URL
   - Paste your API key
   - Enter the model name

3. Click "Test Connection" to verify
"""


class APIBackendManager:
    """Manages switching between different AI backends."""

    def __init__(self):
        """Initialize backend manager."""
        self.backend_type = "ollama"  # "ollama" or "openai"
        self.ollama_backend = None
        self.openai_backend = None

    def set_ollama_backend(self, backend):
        """Set the Ollama backend."""
        self.ollama_backend = backend
        if self.backend_type == "ollama":
            self.current_backend = backend

    def set_openai_backend(self, backend):
        """Set the OpenAI backend."""
        self.openai_backend = backend
        if self.backend_type == "openai":
            self.current_backend = backend

    def use_ollama(self):
        """Switch to Ollama backend."""
        self.backend_type = "ollama"
        if self.ollama_backend:
            self.current_backend = self.ollama_backend

    def use_openai(self):
        """Switch to OpenAI backend."""
        self.backend_type = "openai"
        if self.openai_backend:
            self.current_backend = self.openai_backend

    def get_backend(self):
        """Get the current active backend."""
        return getattr(self, 'current_backend', None)
