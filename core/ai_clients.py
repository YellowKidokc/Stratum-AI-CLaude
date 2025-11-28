from __future__ import annotations

import asyncio
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
import openai
import anthropic


@dataclass
class AIResponse:
    """Standardized response from AI providers."""
    content: str
    model: str
    provider: str
    usage: Optional[Dict[str, Any]] = None
    raw_response: Optional[Any] = None


class AIClient(ABC):
    """Abstract base class for AI API clients."""

    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model

    @abstractmethod
    async def chat_completion(self, messages: List[Dict[str, str]],
                           temperature: float = 0.7, max_tokens: Optional[int] = None) -> AIResponse:
        """Send a chat completion request."""
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Get the provider name."""
        pass


class OpenAIClient(AIClient):
    """OpenAI API client."""

    def __init__(self, api_key: str, model: str = "gpt-4"):
        super().__init__(api_key, model)
        self.client = openai.AsyncOpenAI(api_key=api_key)

    def get_provider_name(self) -> str:
        return "openai"

    async def chat_completion(self, messages: List[Dict[str, str]],
                           temperature: float = 0.7, max_tokens: Optional[int] = None) -> AIResponse:
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            content = response.choices[0].message.content or ""
            usage = {
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0,
            }

            return AIResponse(
                content=content,
                model=self.model,
                provider=self.get_provider_name(),
                usage=usage,
                raw_response=response
            )
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")


class ClaudeClient(AIClient):
    """Anthropic Claude API client."""

    def __init__(self, api_key: str, model: str = "claude-3-sonnet-20240229"):
        super().__init__(api_key, model)
        self.client = anthropic.AsyncAnthropic(api_key=api_key)

    def get_provider_name(self) -> str:
        return "claude"

    async def chat_completion(self, messages: List[Dict[str, str]],
                           temperature: float = 0.7, max_tokens: Optional[int] = None) -> AIResponse:
        try:
            # Convert messages to Claude format
            claude_messages = []
            system_message = None

            for msg in messages:
                if msg["role"] == "system":
                    system_message = msg["content"]
                else:
                    claude_messages.append(msg)

            kwargs = {
                "model": self.model,
                "messages": claude_messages,
                "temperature": temperature,
                "max_tokens": max_tokens or 4096,
            }

            if system_message:
                kwargs["system"] = system_message

            response = await self.client.messages.create(**kwargs)

            content = ""
            if response.content:
                for block in response.content:
                    if hasattr(block, 'text'):
                        content += block.text

            usage = {
                "input_tokens": response.usage.input_tokens if response.usage else 0,
                "output_tokens": response.usage.output_tokens if response.usage else 0,
                "total_tokens": (response.usage.input_tokens + response.usage.output_tokens) if response.usage else 0,
            }

            return AIResponse(
                content=content,
                model=self.model,
                provider=self.get_provider_name(),
                usage=usage,
                raw_response=response
            )
        except Exception as e:
            raise Exception(f"Claude API error: {str(e)}")


class AIClientManager:
    """Manages multiple AI clients and provides unified interface."""

    def __init__(self):
        self.clients: Dict[str, AIClient] = {}

    def add_client(self, provider: str, api_key: str, model: str) -> None:
        """Add an AI client."""
        if provider.lower() == "openai":
            self.clients[provider] = OpenAIClient(api_key, model)
        elif provider.lower() == "claude":
            self.clients[provider] = ClaudeClient(api_key, model)
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    def get_client(self, provider: str) -> Optional[AIClient]:
        """Get a client by provider name."""
        return self.clients.get(provider.lower())

    def get_available_providers(self) -> List[str]:
        """Get list of available providers."""
        return list(self.clients.keys())

    async def chat_completion(self, provider: str, messages: List[Dict[str, str]],
                           temperature: float = 0.7, max_tokens: Optional[int] = None) -> AIResponse:
        """Send chat completion using specified provider."""
        client = self.get_client(provider)
        if not client:
            raise ValueError(f"No client configured for provider: {provider}")

        return await client.chat_completion(messages, temperature, max_tokens)

    async def simple_query(self, provider: str, prompt: str,
                         temperature: float = 0.7, max_tokens: Optional[int] = None) -> str:
        """Simple single-prompt query."""
        messages = [{"role": "user", "content": prompt}]
        response = await self.chat_completion(provider, messages, temperature, max_tokens)
        return response.content


# Convenience function for synchronous usage
def create_ai_manager_from_settings(settings_manager) -> AIClientManager:
    """Create AI manager from settings."""
    manager = AIClientManager()

    # Add OpenAI client if key exists
    openai_key = settings_manager.config.get("openai", "api_key", fallback="")
    openai_model = settings_manager.config.get("openai", "model", fallback="gpt-4")
    if openai_key:
        manager.add_client("openai", openai_key, openai_model)

    # Add Claude client if key exists
    claude_key = settings_manager.config.get("claude", "api_key", fallback="")
    claude_model = settings_manager.config.get("claude", "model", fallback="claude-3-sonnet-20240229")
    if claude_key:
        manager.add_client("claude", claude_key, claude_model)

    return manager
