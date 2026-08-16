from __future__ import annotations

import hashlib
import time

from triskelion.providers import ModelResponse, RiverProvider

TEMPERATURE = 0.7


class Qwen35ChatRiverProviderV152(RiverProvider):
    """Qwen3.5 chat adapter with one frozen nonzero sampling temperature."""

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
        started = time.perf_counter()
        samples = self.client.sample(
            rendered,
            base_model=self.model,
            max_tokens=max_tokens,
            temperature=TEMPERATURE,
            seed=seed,
        )
        if not samples:
            raise RuntimeError("River returned no samples")
        sample = samples[0]
        return ModelResponse(
            text=sample.text,
            latency_ms=round((time.perf_counter() - started) * 1000, 3),
            prompt_sha256=hashlib.sha256(rendered.encode()).hexdigest(),
            model=self.model,
            seed=seed,
            output_tokens=len(sample.tokens) if getattr(sample, "tokens", None) is not None else None,
        )
