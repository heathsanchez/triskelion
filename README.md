# Triskelion

Private experimental harness for Metalogic verified developmental-learning research.

The repository tests whether externally verified experience can grow an explicit algebra of capabilities/operators, scoped composition laws and constructor families; whether those capabilities can be retained, composed, revised and revoked; and whether selected verified capabilities can later be compiled into neural competence without making the neural checkpoint the source of truth.

Experiments are precommitted in source and run through GitHub Actions. Scientific negatives are retained rather than tuned away. Secrets are supplied only through GitHub Actions secrets and are never committed.

## Current status — 2026-08-14 NZST

The strongest bounded neural result remains **IKKF V1 portable capability compilation**: from a fresh Qwen base/fresh LoRA with no inherited capability checkpoint, two independent compilations of the exported verified capability each reached 100% on 32 source-distinct held-out cases; cold, matched decoy and uninstall were 0%; reload preserved 100%.

The routing frontier has now produced two clean negatives. **IKKF V2b** showed that one shared C+J LoRA collapsed onto C (`C=1, J=0, route=.5`). **IKKF V2c** kept C and J as separate explicit verified modules and trained only a C/J selector on the same semantic-valid held-out universe; the selector still collapsed onto C (`C=1, J=0, route=.5`), while the shuffled-label router collapsed onto J. Separating capability execution is therefore not sufficient: the learned activation/selection representation is itself a live obstruction.

**IKKF V3 is now scientifically resolved as a negative rather than infrastructure-blocked.** After fixing a self-triggering export-hygiene check without changing the frozen package or scientific gates, V51 explicit construction/export/ablation/counterevidence/revocation all passed. The frozen neural bridge failed: cold scored `.75`, two independent correct-scope compilations scored `0.0` and emitted `NOOP`, while the inverted-scope control scored `1.0`. Verdict: `FAIL_IKKF_V3_EXTERNAL_INVENTED_INSTINCT`.

The cross-domain grammar line remains: V70 multiscale motifs, V71 whole-scale transfer and V72 exact MDL motif basis pass; V73 finds no stable second-level hierarchy; V74 shows strong held-out mathematical ranking by operator-order grammar but no macro advantage over the primitive grammar and fails its frozen significance gate.

**V77 SorryDB preflight:** the official verifier prerequisite passes. The first end-to-end run exposed an exact-commit checkout plumbing defect for historical external repositories; the checkout was repaired without changing selection, solver budgets or verifier criteria. The repaired run `31761636184` is the current live preflight until its artifact is finalized.

## Canonical navigation

- [`RESEARCH_STATE.md`](RESEARCH_STATE.md) — current synthesis, claim boundaries and immediate priorities.
- [`results/CURRENT_FRONTIER_2026-08-14.md`](results/CURRENT_FRONTIER_2026-08-14.md) — concise audit ledger for the newest passes, negatives and blocked gates.
- [`results/IKKF_V3_EXTERNAL_INVENTED_INSTINCT_NEGATIVE_20260814.md`](results/IKKF_V3_EXTERNAL_INVENTED_INSTINCT_NEGATIVE_20260814.md) — frozen V3 whole-stack negative.
- [`results/IKKF_V2C_MODULAR_ROUTER_NEGATIVE_20260814.md`](results/IKKF_V2C_MODULAR_ROUTER_NEGATIVE_20260814.md) — frozen V2c modular-router negative.
- [`results/V45_V66_LEDGER.txt`](results/V45_V66_LEDGER.txt) — historical external quotient/refinement sequence.
- `results/` — experiment-specific immutable summaries where present.
- `protocols/` — frozen/precommitted scientific protocols.
- `experiments/` — executable experiment harnesses.
- `.github/workflows/` — reproducible CI execution paths.

## Research discipline

For a target `T`, test lawful closure before inventing anything. Only promote a new capability when the frozen old effective language cannot express the needed behavior and external verification supports the extension. Preserve provenance, scope, counterexamples, ablations and revision/removal conditions. Distinguish CI/infrastructure failure from scientific failure.

Current results are bounded mechanism evidence. They do **not** establish a universal cognitive algebra, unrestricted operator/constructor invention, universal installable intelligence, automatic neural modularity, reliable learned multi-capability routing, or open-ended self-improvement.
