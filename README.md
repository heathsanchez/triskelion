# Triskelion

Private experimental harness for Metalogic verified developmental-learning research.

The repository tests whether externally verified experience can grow an explicit algebra of capabilities/operators, scoped composition laws and constructor families; whether those capabilities can be retained, composed, revised and revoked; and whether selected verified capabilities can later be compiled into neural competence without making the neural checkpoint the source of truth.

Experiments are precommitted in source and run through GitHub Actions. Scientific negatives are retained rather than tuned away. Secrets are supplied only through GitHub Actions secrets and are never committed.

## Current status — 2026-08-14 NZST

The strongest bounded result is now **portable capability compilation**: IKKF V1 strict portability starts from a fresh Qwen base/fresh LoRA with no inherited capability checkpoint and compiles only an exported verified capability artifact. Cold performance was 0%; two independent fresh compilations each reached 100% on 32 source-distinct held-out cases; a matched decoy and uninstall arm were 0%; reload preserved 100%.

A crucial follow-up is negative: **IKKF V2b multi-capability routing failed**. A shared C+J LoRA learned C at 100% but J at 0%, with 50% route accuracy. This motivates a modular `CapabilityGraph -> router -> selected module -> verifier` architecture rather than assuming capabilities can simply be merged into one adapter.

The latest whole-stack bridge, **IKKF V3**, is not yet a scientific result: V51 external operator construction passed, but an export-hygiene guard failed before River compilation, so the neural/sealed-transfer gates never ran.

The cross-domain grammar line has also advanced: V70 multiscale motifs, V71 whole-scale transfer and V72 exact MDL motif basis pass; V73 finds no stable second-level hierarchy; V74 shows strong held-out mathematical ranking by operator-order grammar but no macro advantage over the primitive grammar and fails its frozen significance gate.

The current SorryDB V77 preflight reproduces the official verifier successfully but fails later in the Triskelion end-to-end preflight, so it remains infrastructure-blocked rather than scientifically interpreted.

## Canonical navigation

- [`RESEARCH_STATE.md`](RESEARCH_STATE.md) — current synthesis, claim boundaries and immediate priorities.
- [`results/CURRENT_FRONTIER_2026-08-14.md`](results/CURRENT_FRONTIER_2026-08-14.md) — concise audit ledger for the newest passes, negatives and blocked gates.
- [`results/V45_V66_LEDGER.txt`](results/V45_V66_LEDGER.txt) — historical external quotient/refinement sequence.
- `results/` — experiment-specific immutable summaries where present.
- `protocols/` — frozen/precommitted scientific protocols.
- `experiments/` — executable experiment harnesses.
- `.github/workflows/` — reproducible CI execution paths.

## Research discipline

For a target `T`, test lawful closure before inventing anything. Only promote a new capability when the frozen old effective language cannot express the needed behavior and external verification supports the extension. Preserve provenance, scope, counterexamples, ablations and revision/removal conditions. Distinguish CI/infrastructure failure from scientific failure.

Current results are bounded mechanism evidence. They do **not** establish a universal cognitive algebra, unrestricted operator/constructor invention, universal installable intelligence, automatic neural modularity, or open-ended self-improvement.
