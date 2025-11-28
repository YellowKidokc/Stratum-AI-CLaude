"""
Adapters to make AI Hub tabs work with Stratum core systems.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Dict, Any, Optional

if TYPE_CHECKING:
    from core.ai_clients import AIClientManager
    from core.vault_manager import VaultManager
    from core.tts_engine import TTSEngine
    from core.command_registry import CommandRegistry


class OpenAIClientAdapter:
    """Adapter to make Stratum AI clients work like the old OpenAIClient."""

    def __init__(self, ai_manager: AIClientManager, provider: str = "openai"):
        self.ai_manager = ai_manager
        self.provider = provider
        self.client = ai_manager.get_client(provider)

    def chat(self, system: str, message: str) -> str:
        """Synchronous chat method for compatibility."""
        import asyncio
        import nest_asyncio
        nest_asyncio.apply()  # Allow nested event loops

        async def _chat():
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": message})

            response = await self.chat_completion(messages)
            return response["choices"][0]["message"]["content"]

        try:
            return asyncio.run(_chat())
        except Exception as e:
            return f"Error: {str(e)}"

    async def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """Adapt to old OpenAIClient interface."""
        if not self.client:
            raise Exception(f"No {self.provider} client configured")

        response = await self.client.chat_completion(messages, **kwargs)

        # Convert to old format
        return {
            "choices": [{"message": {"content": response.content}}],
            "usage": response.usage or {}
        }


class PromptManagerAdapter:
    """Adapter to make VaultManager work like the old PromptManager."""

    def __init__(self, vault_manager: VaultManager):
        self.vault = vault_manager

    def get_all_prompts(self) -> List[Dict[str, Any]]:
        """Get all prompts from vault."""
        prompts = self.vault.get_lane_items("prompts")
        return [
            {
                "id": p.id,
                "title": p.title,
                "content": p.content,
                "tags": p.tags,
                "category": "prompts"
            }
            for p in prompts
        ]

    def save_prompt(self, title: str, content: str, tags: Optional[List[str]] = None) -> str:
        """Save a prompt to vault."""
        return self.vault.add_item(title, content, "prompts", tags)

    def delete_prompt(self, prompt_id: str) -> bool:
        """Delete a prompt from vault."""
        return self.vault.delete_item(prompt_id)


class TTSAdapter:
    """Adapter to make TTSEngine work like the old TTS systems."""

    def __init__(self, tts_engine: TTSEngine):
        self.tts = tts_engine

    def speak(self, text: str) -> None:
        """Speak text."""
        self.tts.speak_text(text)

    def stop(self) -> None:
        """Stop speaking."""
        self.tts.stop_speaking()

    def get_voices(self) -> List[Dict[str, str]]:
        """Get available voices."""
        return self.tts.get_available_voices()

    def set_voice(self, voice_name: str) -> None:
        """Set voice."""
        self.tts.set_voice(voice_name)

    def save_to_file(self, text: str, file_path: str) -> bool:
        """Save TTS output as an audio file (MP3).

        Args:
            text: The text to convert to speech
            file_path: Path where to save the MP3 file

        Returns:
            True if successful, False otherwise
        """
        return self.tts.save_to_file(text, file_path)


class ShortcutsAdapter:
    """Adapter to make CommandRegistry work like the old shortcuts system."""

    def __init__(self, command_registry: CommandRegistry):
        self.registry = command_registry

    def get_all_shortcuts(self) -> List[Dict[str, Any]]:
        """Get all commands as shortcuts."""
        commands = self.registry.all()
        return [
            {
                "id": cmd.id,
                "label": cmd.label,
                "hotkey": cmd.hotkey,
                "hotstring": cmd.hotstring,
                "action": cmd.action,
                "tags": cmd.tags
            }
            for cmd in commands
        ]

    def add_shortcut(self, label: str, hotkey: str, action: str,
                    hotstring: str = "", tags: Optional[List[str]] = None) -> str:
        """Add a new shortcut/command."""
        # Generate ID from label
        shortcut_id = label.lower().replace(" ", "_")
        existing_ids = {cmd.id for cmd in self.registry.all()}
        counter = 1
        original_id = shortcut_id
        while shortcut_id in existing_ids:
            shortcut_id = f"{original_id}_{counter}"
            counter += 1

        from core.command_registry import Command
        cmd = Command(
            id=shortcut_id,
            label=label,
            action=action,
            hotkey=hotkey,
            hotstring=hotstring,
            tags=tags or []
        )

        self.registry.add_command(cmd)
        return shortcut_id

    def remove_shortcut(self, shortcut_id: str) -> bool:
        """Remove a shortcut."""
        return self.registry.remove_command(shortcut_id)
