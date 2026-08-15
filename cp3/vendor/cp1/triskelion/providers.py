from __future__ import annotations

import hashlib
import os
import time
from dataclasses import asdict, dataclass


@dataclass
class ModelResponse:
    text: str
    latency_ms: float
    prompt_sha256: str
    model: str
    seed: int
    output_tokens: int | None

    def to_dict(self):
        return asdict(self)


class RiverProvider:
    """Fail-loud adapter. Credentials are read only from the process environment."""

    def __init__(self, model: str, api_key_env: str = "RIVER_API_KEY"):
        try:
            import river_client as river
        except ImportError as exc:
            raise RuntimeError("river-client is not installed") from exc
        key = os.environ.get(api_key_env)
        if not key:
            raise RuntimeError(f"{api_key_env} is not configured")
        self.model = model
        self.client = river.Client(api_key=key)
        if not self.client.health_check():
            raise RuntimeError("River health check failed")
        available = list(self.client.get_capabilities())
        if model not in available:
            raise RuntimeError(f"frozen model {model!r} unavailable; enabled={available!r}")

    def sample(self, prompt: str, *, seed: int, max_tokens: int) -> ModelResponse:
        started = time.perf_counter()
        samples = self.client.sample(
            prompt, base_model=self.model, max_tokens=max_tokens,
            temperature=0.0, seed=seed,
        )
        if not samples:
            raise RuntimeError("River returned no samples")
        sample = samples[0]
        return ModelResponse(
            text=sample.text,
            latency_ms=round((time.perf_counter() - started) * 1000, 3),
            prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(),
            model=self.model, seed=seed,
            output_tokens=len(sample.tokens) if getattr(sample, "tokens", None) is not None else None,
        )
