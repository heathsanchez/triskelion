from __future__ import annotations

import hashlib
from typing import Any

from triskelion.providers import ModelResponse, RiverProvider


class Qwen35ChatRiverProvider(RiverProvider):
    """River adapter that supplies Qwen3.5 its official chat-template boundary.

    River samples a rendered prompt string. CP3 previously sent the bare user
    text directly, which left a chat/instruct model without its conversation
    template and kept Qwen3.5 in its default thinking behavior. This wrapper
    changes only prompt serialization: model, temperature, seed and max-token
    budget remain those of the recovered CP1 RiverProvider.
    """

    def __init__(self, model: str, api_key_env: str = "RIVER_API_KEY"):
        super().__init__(model, api_key_env=api_key_env)
        try:
            from transformers import AutoTokenizer
        except ImportError as exc:
            raise RuntimeError("transformers is required to render Qwen3.5 chat prompts") from exc
        self.tokenizer = AutoTokenizer.from_pretrained(model, trust_remote_code=False)

    def render_prompt(self, prompt: str) -> str:
        messages = [{"role": "user", "content": prompt}]
        rendered = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False,
        )
        if not isinstance(rendered, str) or not rendered.strip():
            raise RuntimeError("Qwen3.5 chat template returned an empty prompt")
        return rendered

    def sample(self, prompt: str, *, seed: int, max_tokens: int) -> ModelResponse:
        rendered = self.render_prompt(prompt)
        response = super().sample(rendered, seed=seed, max_tokens=max_tokens)
        # Preserve the exact model-facing hash while also making the visible
        # pre-template prompt independently auditable by callers.
        response.prompt_sha256 = hashlib.sha256(rendered.encode()).hexdigest()
        return response
