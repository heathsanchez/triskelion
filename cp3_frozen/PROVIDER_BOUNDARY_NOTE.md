# CP3 Qwen3.5 provider-boundary correction

Status: **ACQUISITION-SIDE INTERFACE CORRECTION; PROTECTED SEMANTICS UNOPENED**

## Observation

After the source representation and edit transport were corrected, acquisition runs still exhausted the 2,048-token completion budget in free-form/thinking output instead of reliably producing the requested repair object.

The recovered CP1 `RiverProvider` passes its input string directly to `river.Client.sample(...)`. CP3 had been passing the bare task text as that input.

Qwen3.5 is a chat/instruction model whose official usage renders messages through its chat template; Qwen3.5 also operates in thinking mode by default. Its documented non-thinking mode is selected through the chat-template/API parameter `enable_thinking=False`, not the Qwen3 `/think` or `/nothink` text switch.

## Correction

`cp3/river_qwen35_provider.py` preserves the recovered River sampling call and its frozen scientific parameters but changes prompt serialization:

1. wrap the CP3 visible task as one user message;
2. render the official `Qwen/Qwen3.5-9B` chat template;
3. set `enable_thinking=False` in that template;
4. pass the resulting rendered string to the recovered CP1 River sampler with the same model, temperature, seed and maximum output tokens.

The acquisition workflow pins `river-client==0.6.1` for this candidate and records the installed Transformers version plus a hash/tail of a rendered probe prompt before any acquisition call.

## Scientific treatment

This is a provider/interface correction, not target-specific semantic tuning. It was inferred from acquisition-only behavior and the public model/provider interfaces. No protected case source, outcome, fixed implementation, developer patch or verifier feedback was used.

If this correction yields the final acquisition freeze, the same provider wrapper is already wired into `cp3/bugsinpy_four_arm_v7.py` for every protected arm, preserving equality of model-facing serialization across COLD, RAW MEMORY, ALWAYS-ON and VERIFIED.
