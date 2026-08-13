import os, time, json
from pathlib import Path

import river_client as river
from transformers import AutoTokenizer

OUT = Path("artifacts/river_instrumented_smoke_v1")
OUT.mkdir(parents=True, exist_ok=True)
EVENTS = []

def mark(event, **extra):
    row = {"t": time.time(), "event": event, **extra}
    EVENTS.append(row)
    (OUT / "EVENTS.json").write_text(json.dumps(EVENTS, indent=2))
    print(f"[{time.strftime('%H:%M:%S')}] {event}", extra if extra else "", flush=True)

key = os.environ["RIVER_API_KEY"]
mark("client_start")
client = river.Client(api_key=key, timeout=180.0)
mark("health_before")
health = client.health_check()
mark("health_after", health=health)
mark("capabilities_before")
caps = list(client.get_capabilities())
mark("capabilities_after", count=len(caps), caps=caps)

preferred = ["Qwen/Qwen3.5-9B", "Qwen/Qwen3.6-35B-A3B-FP8"]
base = next((m for m in preferred if m in caps), None)
if base is None:
    raise RuntimeError(f"No preferred base model available: {caps}")
mark("base_selected", base=base)

mark("tokenizer_before")
tok = AutoTokenizer.from_pretrained(base, trust_remote_code=True)
mark("tokenizer_after", eos_token_id=tok.eos_token_id)
if tok.eos_token_id is None:
    raise RuntimeError("No EOS token")

prompt = "Policy A\ninput=amber\nReturn exactly the transformed string."
gold = "ka-amber"
pids = tok(prompt, add_special_tokens=False)["input_ids"]
cids = tok(" " + gold, add_special_tokens=False)["input_ids"] + [tok.eos_token_id]
ids = pids + cids
target_tokens = ids[1:] + [tok.eos_token_id]
n = max(0, len(pids) - 1)
weights = [0.0] * n + [1.0] * (len(target_tokens) - n)
datum = {"input_ids": ids, "target_tokens": target_tokens, "weights": weights}
mark("datum_ready", prompt_tokens=len(pids), completion_tokens=len(cids))

mark("session_before")
with client.session(project="metalogic-river-instrumented-smoke-v1", timeout=180.0) as sess:
    mark("session_after")
    mark("create_model_before")
    model = sess.create_model(base_model=base, lora=river.LoraConfig(rank=4, seed=20260813))
    mark("create_model_after")

    mark("sample_pre_before")
    pre = model.sample(prompt, max_tokens=20, temperature=0.0, stop=["\n"])
    mark("sample_pre_after", repr=repr(pre)[:1000])

    mark("forward_backward_before")
    fb = model.forward_backward(data=[datum], loss_fn="cross_entropy")
    mark("forward_backward_after", repr=repr(fb)[:1000])

    mark("optim_step_before")
    opt = model.optim_step(lr=2e-4, grad_clip_norm=1.0)
    mark("optim_step_after", repr=repr(opt)[:1000])

    mark("sample_post_before")
    post = model.sample(prompt, max_tokens=20, temperature=0.0, stop=["\n"])
    mark("sample_post_after", repr=repr(post)[:1000])

    mark("save_training_before")
    ckpt = model.save_weights("smoke_training", mode="training")
    mark("save_training_after", repr=repr(ckpt)[:1500])

result = {"status": "PASS_SMOKE", "base": base, "events": EVENTS}
(OUT / "FINAL_RESULT.json").write_text(json.dumps(result, indent=2))
mark("done")
