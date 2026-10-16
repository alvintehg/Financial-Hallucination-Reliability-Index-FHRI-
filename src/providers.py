# src/providers.py
"""
Provider adapter layer for LLM backends.

Provides a unified interface for calling different LLM providers:
- DeepSeek (via OpenRouter or direct API)
- OpenAI (GPT models)
- Anthropic (Claude models)
- Demo (fallback without API keys)

Each provider returns a normalized result with:
- text: The generated response
- usage: Token counts (if available)
- model: Model name used
- finish_reason: Completion status
- raw: Original provider response (for debugging)
"""

import os
import logging
from typing import Dict, Any, Optional, Tuple
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger("providers")


def create_session_with_retries(retries: int = 2, backoff_factor: float = 0.3,
                                  status_forcelist: Tuple[int, ...] = (500, 502, 504)) -> requests.Session:
    """Create a requests session with retry logic."""
    session = requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


class ProviderResult:
    """Normalized result from any provider."""
    def __init__(self, text: str, usage: Optional[Dict[str, int]] = None,
                 model: Optional[str] = None, finish_reason: Optional[str] = None,
                 raw: Optional[Dict] = None):
        self.text = text
        self.usage = usage or {}
        self.model = model or "unknown"
        self.finish_reason = finish_reason or "stop"
        self.raw = raw or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "usage": self.usage,
            "model": self.model,
            "finish_reason": self.finish_reason
        }


class BaseProvider:
    """Base class for LLM providers."""

    def __init__(self, api_key: Optional[str] = None, timeout: int = 30):
        self.api_key = api_key
        self.timeout = timeout
        self.session = create_session_with_retries()

    def is_available(self) -> bool:
        """Check if provider is configured and available."""
        return bool(self.api_key)

    def generate(self, prompt: str, max_tokens: int = 400, temperature: float = 0.0) -> ProviderResult:
        """Generate response from provider. Must be implemented by subclasses."""
        raise NotImplementedError


class DeepSeekProvider(BaseProvider):
    """DeepSeek provider (works with OpenRouter or direct API)."""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None,
                 model_name: Optional[str] = None, timeout: int = 30):
        super().__init__(api_key, timeout)
        self.base_url = base_url or os.environ.get("DEEPSEEK_URL", "https://api.deepseek.com/v1/chat/completions")
        self.model_override = model_name

    def generate(self, prompt: str, max_tokens: int = 400, temperature: float = 0.0) -> ProviderResult:
        """Generate response from DeepSeek."""
        logger.info("Calling DeepSeek API")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Use different model name for OpenRouter vs direct API
        if "openrouter" in self.base_url.lower():
            # Allow model override from environment or constructor
            model_name = self.model_override or os.environ.get("DEEPSEEK_MODEL", "deepseek/deepseek-chat")
            headers["HTTP-Referer"] = "https://github.com/llm-fin-chatbot"
            headers["X-Title"] = "LLM Financial Chatbot"
        else:
            model_name = self.model_override or "deepseek-chat"

        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        try:
            r = self.session.post(self.base_url, headers=headers, json=payload, timeout=self.timeout)
            r.raise_for_status()
            raw_resp = r.json()

            # Parse response
            text = self._parse_response(raw_resp)
            usage = raw_resp.get("usage", {})
            model = raw_resp.get("model", model_name)
            finish_reason = raw_resp.get("choices", [{}])[0].get("finish_reason", "stop")

            return ProviderResult(text=text, usage=usage, model=model, finish_reason=finish_reason, raw=raw_resp)

        except requests.exceptions.Timeout:
            logger.error("DeepSeek API timeout")
            raise TimeoutError("DeepSeek API timeout")
        except requests.exceptions.RequestException as e:
            logger.error(f"DeepSeek API request failed: {e}")
            raise RuntimeError(f"DeepSeek API error: {e}")

    def _parse_response(self, raw_resp: Dict) -> str:
        """Parse DeepSeek response to extract text."""
        if "choices" in raw_resp and len(raw_resp["choices"]) > 0:
            choice = raw_resp["choices"][0]
            if isinstance(choice, dict):
                if "message" in choice and isinstance(choice["message"], dict):
                    content = choice["message"].get("content")
                    if content:
                        return str(content).strip()
                if "text" in choice:
                    return str(choice["text"]).strip()

        for field in ["content", "text", "generated_text", "result", "output"]:
            if field in raw_resp and raw_resp[field]:
                return str(raw_resp[field]).strip()

        logger.warning(f"Could not parse DeepSeek response: {raw_resp}")
        return str(raw_resp)


class OpenAIProvider(BaseProvider):
    """OpenAI provider (GPT models)."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-3.5-turbo", timeout: int = 30):
        super().__init__(api_key, timeout)
        self.model = model

    def generate(self, prompt: str, max_tokens: int = 400, temperature: float = 0.0) -> ProviderResult:
        """Generate response from OpenAI."""
        logger.info("Calling OpenAI API")

        try:
            import openai
            openai.api_key = self.api_key

            resp = openai.ChatCompletion.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=self.timeout
            )

            text = resp["choices"][0]["message"]["content"].strip()
            usage = resp.get("usage", {})
            model = resp.get("model", self.model)
            finish_reason = resp["choices"][0].get("finish_reason", "stop")

            return ProviderResult(text=text, usage=usage, model=model, finish_reason=finish_reason, raw=dict(resp))

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise RuntimeError(f"OpenAI API error: {e}")


class AnthropicProvider(BaseProvider):
    """Anthropic provider (Claude models)."""

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-5-sonnet-20241022", timeout: int = 30):
        super().__init__(api_key, timeout)
        self.model = model
        self.base_url = "https://api.anthropic.com/v1/messages"

    def generate(self, prompt: str, max_tokens: int = 400, temperature: float = 0.0) -> ProviderResult:
        """Generate response from Anthropic Claude."""
        logger.info("Calling Anthropic API")

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }

        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}]
        }

        try:
            r = self.session.post(self.base_url, headers=headers, json=payload, timeout=self.timeout)
            r.raise_for_status()
            raw_resp = r.json()

            # Parse Anthropic response format
            text = ""
            if "content" in raw_resp and isinstance(raw_resp["content"], list):
                for block in raw_resp["content"]:
                    if block.get("type") == "text":
                        text += block.get("text", "")

            usage = {
                "prompt_tokens": raw_resp.get("usage", {}).get("input_tokens", 0),
                "completion_tokens": raw_resp.get("usage", {}).get("output_tokens", 0),
                "total_tokens": raw_resp.get("usage", {}).get("input_tokens", 0) + raw_resp.get("usage", {}).get("output_tokens", 0)
            }

            model = raw_resp.get("model", self.model)
            finish_reason = raw_resp.get("stop_reason", "end_turn")

            return ProviderResult(text=text.strip(), usage=usage, model=model, finish_reason=finish_reason, raw=raw_resp)

        except requests.exceptions.Timeout:
            logger.error("Anthropic API timeout")
            raise TimeoutError("Anthropic API timeout")
        except requests.exceptions.RequestException as e:
            logger.error(f"Anthropic API request failed: {e}")
            raise RuntimeError(f"Anthropic API error: {e}")


class DemoProvider(BaseProvider):
    """Demo provider that returns placeholder responses without API calls."""

    def __init__(self):
        super().__init__(api_key="demo", timeout=0)

    def is_available(self) -> bool:
        """Demo is always available."""
        return True

    def generate(self, prompt: str, max_tokens: int = 400, temperature: float = 0.0) -> ProviderResult:
        """Generate demo response."""
        logger.info("Using demo mode (no API keys provided)")
        text = "Demo answer: No LLM API key provided. This is a placeholder response. Please set DEEPSEEK_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY in your .env file."
        return ProviderResult(text=text, usage={}, model="demo", finish_reason="stop", raw={"mode": "demo"})


class ProviderManager:
    """Manages multiple providers and handles fallback logic."""

    def __init__(self):
        self.providers: Dict[str, BaseProvider] = {}
        self._initialize_providers()

    def _initialize_providers(self):
        """Initialize all configured providers from environment."""
        # DeepSeek
        deepseek_key = os.environ.get("DEEPSEEK_API_KEY")
        deepseek_url = os.environ.get("DEEPSEEK_URL", "https://api.deepseek.com/v1/chat/completions")
        deepseek_model = os.environ.get("DEEPSEEK_MODEL")  # Optional model override
        if deepseek_key:
            self.providers["deepseek"] = DeepSeekProvider(
                api_key=deepseek_key,
                base_url=deepseek_url,
                model_name=deepseek_model
            )

        # OpenAI
        openai_key = os.environ.get("OPENAI_API_KEY")
        if openai_key:
            self.providers["openai"] = OpenAIProvider(api_key=openai_key)

        # Anthropic
        anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
        if anthropic_key:
            anthropic_model = os.environ.get("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
            self.providers["anthropic"] = AnthropicProvider(api_key=anthropic_key, model=anthropic_model)

        # Demo is always available
        self.providers["demo"] = DemoProvider()

        logger.info(f"Initialized providers: {list(self.providers.keys())}")

    def get_provider(self, name: str) -> Optional[BaseProvider]:
        """Get provider by name."""
        return self.providers.get(name)

    def generate(self, prompt: str, provider: str = "auto", max_tokens: int = 400,
                 temperature: float = 0.0, timeout: Optional[int] = None) -> Tuple[str, str, ProviderResult]:
        """
        Generate response using specified provider or auto-fallback.

        Returns: (provider_name, answer_text, ProviderResult)
        """
        # Set timeout on provider if specified
        if provider == "auto":
            # Auto fallback order: deepseek -> openai -> anthropic -> demo
            fallback_order = ["deepseek", "openai", "anthropic", "demo"]
            for prov_name in fallback_order:
                prov = self.providers.get(prov_name)
                if prov and prov.is_available():
                    try:
                        if timeout:
                            prov.timeout = timeout
                        result = prov.generate(prompt, max_tokens, temperature)
                        return prov_name, result.text, result
                    except Exception as e:
                        logger.warning(f"Provider {prov_name} failed: {e}, trying next...")
                        continue
            # Should not reach here as demo is always available
            raise RuntimeError("All providers failed including demo")
        else:
            # Use specific provider
            prov = self.providers.get(provider)
            if not prov:
                raise ValueError(f"Unknown provider: {provider}")
            if not prov.is_available() and provider != "demo":
                raise ValueError(f"Provider {provider} is not configured (missing API key)")

            if timeout:
                prov.timeout = timeout
            result = prov.generate(prompt, max_tokens, temperature)
            return provider, result.text, result
