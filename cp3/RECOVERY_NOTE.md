# Checkpoint 3 recovery

Recovery lineage created 2026-08-15 from `private/verified-capability-runtime-cp1`.

Frozen protocol facts preserved:
- BugsInPy corpus: 501 bugs / 17 projects.
- Acquisition projects: pandas, youtube-dl, httpie, PySnooper, cookiecutter.
- Protected projects: ansible, spacy, sanic, keras, matplotlib, thefuck, black, scrapy, luigi, fastapi, tornado, tqdm.
- Corpus-lock SHA-256: `760b73f87bbe79b76c970c1b2ac4cdd83e5eb18ee3f4b9f2304a915fddbbd5ad`.
- Admission rule: fixed revision passes + buggy revision fails.
- Candidate/project ordering remains frozen; no semantic skipping or cherry-picking.
- Infrastructure failures are recorded as negatives and advance only according to the frozen ordering.
- Four protected arms: COLD / RAW MEMORY / ALWAYS-ON / VERIFIED; frozen Qwen3.5-9B, temperature 0, identical seeds/budgets, max 2 calls per case-arm, 2048 tokens/call; one protected evaluation per case-arm; no post-hoc exclusions/tuning.

Known qualified before recovery:
- Acquisition: httpie/5, youtube-dl/32.
- Protected: thefuck/32, keras/32, spacy/2, fastapi/5, black/18.

Unresolved at last durable checkpoint: pandas, scrapy, luigi.

This recovery branch must not inspect protected fixed implementations or protected outcomes before the frozen protected evaluation stage.
