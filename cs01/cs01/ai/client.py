"""
cs01.ai.client — Local LLM Client for Qwen 2.5 Coder & Ollama/vLLM.
Local-first, zero-cloud-egress client supporting streaming generation.
"""

from __future__ import annotations
import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Callable, Optional


class LocalLLMClient:
    """Client for local LLMs (Qwen 2.5 Coder via Ollama, vLLM, or llama.cpp)."""

    def __init__(
        self,
        model: str = "qwen2.5-coder:3b",
        endpoint: str = "http://localhost:11434",
        temperature: float = 0.2,
        timeout: float = 300.0,
    ) -> None:
        self.model = model
        self.endpoint = endpoint.rstrip("/")
        self.temperature = temperature
        self.timeout = timeout

        # Guard against accidental cloud endpoint leakage
        parsed = urllib.parse.urlparse(self.endpoint)
        hostname = (parsed.hostname or "").lower()
        if (
            hostname not in ("localhost", "127.0.0.1", "::1", "0.0.0.0")
            and not hostname.startswith("192.168.")
            and not hostname.startswith("10.")
            and not hostname.endswith(".local")
        ):
            raise ValueError(
                f"Security Guardrail: AI endpoint '{self.endpoint}' is not a local host. "
                "CS-01 requires a local zero-egress LLM server."
            )

    def get_available_models(self) -> list[str]:
        """Fetch list of models installed on the local server."""
        try:
            req = urllib.request.Request(f"{self.endpoint}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return [m["name"] for m in data.get("models", [])]
        except Exception:
            pass

        try:
            req = urllib.request.Request(f"{self.endpoint}/v1/models", method="GET")
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return [m.get("id", "") for m in data.get("data", [])]
        except Exception:
            pass

        return []

    def resolve_model(self) -> str:
        """Resolve requested model to best matching installed model in Ollama/vLLM."""
        installed = self.get_available_models()
        if not installed or self.model in installed:
            return self.model

        # If user asked for qwen2.5-coder without tag or tag mismatch
        base_name = self.model.split(":")[0].lower()
        candidates = [m for m in installed if base_name in m.lower()]
        if candidates:
            requested_tag = self.model.split(":")[1].lower() if ":" in self.model else "3b"
            exact_tag_matches = [c for c in candidates if requested_tag in c.lower()]
            if exact_tag_matches:
                self.model = exact_tag_matches[0]
                return self.model
            preferred = [c for c in candidates if "3b" in c] or [c for c in candidates if "7b" in c]
            chosen = preferred[0] if preferred else candidates[0]
            self.model = chosen
            return self.model

        return self.model

    def is_available(self) -> bool:
        """Check if the local LLM server is up and reachable."""
        try:
            req = urllib.request.Request(f"{self.endpoint}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            pass

        try:
            req = urllib.request.Request(f"{self.endpoint}/v1/models", method="GET")
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            pass

        return False

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        on_token: Optional[Callable[[str], None]] = None,
    ) -> str:
        """
        Generate completion from local Qwen 2.5 Coder model.
        Tries streaming from Ollama native /api/generate first, then fallback to /v1/chat/completions.
        """
        self.resolve_model()

        try:
            return self._call_ollama_stream(prompt, system_prompt, on_token)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                # Try OpenAI-compatible API (for vLLM or LM Studio)
                try:
                    return self._call_openai_compat(prompt, system_prompt)
                except urllib.error.HTTPError as err:
                    if err.code == 404:
                        installed = self.get_available_models()
                        raise RuntimeError(
                            f"Model '{self.model}' is not pulled in Ollama. "
                            f"Run 'ollama pull {self.model}'. Installed models: {', '.join(installed) or 'None'}"
                        ) from err
                    raise
            raise RuntimeError(f"Local LLM API error ({e.code}): {e.read().decode('utf-8', errors='ignore')}") from e
        except TimeoutError as e:
            raise TimeoutError(
                f"Local LLM generation timed out after {self.timeout}s. "
                "Consider using a smaller model (e.g. qwen2.5-coder:7b) or increasing timeout."
            ) from e
        except urllib.error.URLError as e:
            raise ConnectionError(
                f"Failed to connect to local LLM server at {self.endpoint}. "
                f"Ensure Ollama or vLLM is running (e.g. 'ollama run {self.model}'). Error: {e}"
            ) from e

    def _call_ollama_stream(
        self,
        prompt: str,
        system_prompt: Optional[str],
        on_token: Optional[Callable[[str], None]],
    ) -> str:
        combined_prompt = prompt
        if system_prompt:
            combined_prompt = f"System: {system_prompt}\n\nUser: {prompt}"

        payload = {
            "model": self.model,
            "prompt": combined_prompt,
            "stream": True,
            "options": {
                "temperature": self.temperature,
            },
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.endpoint}/api/generate",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        accumulated: list[str] = []
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            for line in resp:
                if not line:
                    continue
                try:
                    chunk = json.loads(line.decode("utf-8"))
                    text = chunk.get("response", "")
                    if text:
                        accumulated.append(text)
                        if on_token:
                            on_token(text)
                    if chunk.get("done", False):
                        break
                except Exception:
                    continue

        return "".join(accumulated).strip()

    def _call_openai_compat(self, prompt: str, system_prompt: Optional[str]) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "stream": False,
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.endpoint}/v1/chat/completions",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            choices = body.get("choices", [])
            if choices and "message" in choices[0]:
                return choices[0]["message"].get("content", "").strip()
            return ""
