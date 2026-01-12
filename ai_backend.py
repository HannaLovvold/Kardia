"""AI backend integration using Ollama for local LLM inference."""
import subprocess
import json
import requests
from typing import List, Dict, Optional
import threading


class OllamaBackend:
    """Handles communication with Ollama API for local LLM inference."""

    def __init__(self, model_name: str = "mistral", base_url: str = "http://localhost:11434"):
        """
        Initialize Ollama backend.

        Args:
            model_name: The Ollama model to use (mistral, llama2, etc.)
            base_url: The Ollama API base URL
        """
        self.model_name = model_name
        self.base_url = base_url
        self.api_url = f"{base_url}/api/generate"
        self.chat_url = f"{base_url}/api/chat"
        self._available = None

    def check_ollama_available(self) -> bool:
        """Check if Ollama is running and available."""
        if self._available is not None:
            return self._available

        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            self._available = response.status_code == 200
            return self._available
        except Exception:
            self._available = False
            return False

    def check_model_installed(self) -> bool:
        """Check if the model is installed in Ollama."""
        if not self.check_ollama_available():
            return False

        try:
            response = requests.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m.get("name", "") for m in models]
                return any(self.model_name in name for name in model_names)
            return False
        except Exception:
            return False

    def get_available_models(self) -> List[str]:
        """Get list of available Ollama models."""
        if not self.check_ollama_available():
            return []

        try:
            response = requests.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                return [m.get("name", "") for m in models]
            return []
        except Exception:
            return []

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
        if not self.check_ollama_available():
            return "Error: Ollama is not running. Please start Ollama first."

        if not self.check_model_installed():
            return f"Error: Model '{self.model_name}' is not installed. Run: ollama pull {self.model_name}"

        # Prepare the payload
        payload = {
            "model": self.model_name,
            "stream": stream,
            "messages": messages,
        }

        if system_prompt:
            # Add system prompt as first message
            messages.insert(0, {"role": "system", "content": system_prompt})

        try:
            if stream and callback:
                # Streaming response
                return self._stream_response(payload, callback)
            else:
                # Non-streaming response
                response = requests.post(self.chat_url, json=payload, timeout=120)
                response.raise_for_status()
                result = response.json()

                if "message" in result:
                    return result["message"].get("content", "")
                return ""
        except requests.exceptions.Timeout:
            return "Error: Request timed out. The model might be thinking too long."
        except requests.exceptions.RequestException as e:
            return f"Error communicating with Ollama: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"

    def _stream_response(self, payload: Dict, callback) -> str:
        """Handle streaming response from Ollama."""
        full_response = ""

        try:
            response = requests.post(
                self.chat_url,
                json=payload,
                stream=True,
                timeout=120,
            )

            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        if "message" in data:
                            content = data["message"].get("content", "")
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
    def get_installation_instructions() -> str:
        """Get instructions for installing Ollama."""
        return """
To install Ollama:

1. Install Ollama:
   curl -fsSL https://ollama.com/install.sh | sh

2. Start Ollama (it usually starts automatically):
   ollama serve

3. Pull a model (we recommend mistral):
   ollama pull mistral

4. Verify installation:
   ollama list

5. Run this app again!

For more information, visit: https://ollama.com/download
"""

    @staticmethod
    def pull_model(model_name: str, callback=None):
        """
        Pull a model from Ollama library.

        Args:
            model_name: Name of the model to pull
            callback: Optional callback for progress updates
        """
        def _pull():
            try:
                process = subprocess.Popen(
                    ["ollama", "pull", model_name],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                )

                output = []
                for line in process.stdout:
                    output.append(line)
                    if callback:
                        callback(line.strip())

                process.wait()
                return process.returncode == 0
            except FileNotFoundError:
                if callback:
                    callback("Error: Ollama not found. Please install it first.")
                return False
            except Exception as e:
                if callback:
                    callback(f"Error pulling model: {str(e)}")
                return False

        thread = threading.Thread(target=_pull, daemon=True)
        thread.start()
