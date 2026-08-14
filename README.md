# Triskelion

Private experimental harness for Metalogic / LOGOS verified-learning research.

The project tests whether externally verified experience can change an explicit capability system: compose what already exists, construct a capability outside the old closure when necessary, learn when it applies, revise or revoke it under counterevidence, change what can be discovered next, and optionally compile verified competence into neural form without making the checkpoint the source of truth.

Experiments are frozen/precommitted where possible and run through GitHub Actions. Scientific negatives, infrastructure blocks and attestation defects are retained rather than tuned away.

## Current status — 2026-08-14 16:15 NZST

The strongest bounded developmental result is **V54 two-generation compounding** on branch `v54-compounding-ratchet`, run `31761530951`: an acquired `O1` was outside the frozen old closure; under the same one-new-generator budget `O2` had zero cold survivors before `O1`, became uniquely discoverable after lawful reuse of `O1`, and the final target required both. This supports the bounded causal statement `O2 ∉ Discoverable(A0)` but `O2 ∈ Discoverable(A0 + O1)`.

The external sealing sequence leading into that result is now also explicit in the repository record. **V49** committed a learned capability/category before the Requests target was opened, then demonstrated cold failure, warm success, ablation failure and later revocation. **V50** generated HELP/HARM labels from executable verifier transitions rather than supplying class labels. **V51** constructed `< -> <=` outside a frozen old token-permutation closure, transferred it to sealed Requests, passed the ablation gate and later revoked it under contradictory evidence.

**V55A natural historical compounding** is an honest incomplete, not a falsification of V54. On the frozen BugsInPy stream only two worlds became usable, both from Black, and neither produced a unique constructible `O1`; the natural compounding mechanism was therefore never reached. The current natural-world obstruction is coverage/localization/constructor expressivity.

**V55B constructor-level compounding** is a real negative for the tested insert-by-token-type meta-substrate. `K0` could not repair the deletion obstruction, but the frozen substrate failed to synthesize `K1`, so no `K2` lineage could be tested. **V56B** attempted a more robust retry but crashed on an intermediate malformed insertion that raised `IndentationError`; it therefore produced no scientific verdict and does not supersede the V55B negative.

**V55C naive model integration** was mixed: Qwen2.5-Coder-0.5B scored 6/12 with no memory, 5/12 with raw memory, and 5/12 with a verified capability card in the prompt. The card transferred to the helpful cases but failed all protected negatives, showing that describing scope to the model is not enough. **V56C then passed the architectural correction**: the same bounded decision setup scored 6/12 no-memory, 6/12 raw-memory, and **12/12 with a structurally verifier-controlled capability layer**. The model proposes; the explicit capability/scope layer plus external verifier decides whether the capability may fire.

**V56A historical blind-edit retry** did not reach a scientific verdict. It crashed on an `IndexError` from stale/out-of-range edit coordinates during the historical candidate search. Natural historical replication therefore remains open rather than failed.

The explicit applicability/invocation line advanced beyond the older V2c/V3 negatives. **IKKF V4b** (`ikkf-v4b-verifier-induced-invocation`) passed its frozen gates: a coarse learned scope admitted two Requests sites, external target+protected verification uniquely retained the true invocation, rejected the false positive, repair survived, ablation failed, and later counterevidence revoked the capability. **IKKF V2d** (`ikkf-v2d-verified-capability-os`) then used the exact V2c held-out worlds and the same C/J modules: verifier-controlled invocation reached 100% routing and 100% execution where the learned router had reached 50% routing and 0% joint execution. This supports verified invocation as authority; it does not yet prove cheap learned routing.

**IKKF V1 capability-to-neural compilation remains a bounded positive with an attestation correction.** The primary harness separately executes B0, C1, C2, J, U and R. C1 and C2 are separate fresh compilation calls and both pass held-out transfer; B0/U fail and reload R passes. However C1 and C2 produced bit-identical training trajectories despite nominally different seeds, and the gate named `independent_recompile` only checks that both scores pass. Therefore the supported claim is **reproducible fresh recompilation**, not yet genuine stochastic independence. `independent_recompile` is overstated until independence is directly tested (e.g. effective seed/config + adapter hashes/weights).

**V18b protected consolidation is attested separately.** Its primary artifact records adaptive consolidation of new direct competence while measured ancestors/composites remain passing through reload. This is bounded protected consolidation evidence, not proof of regression-free arbitrary compilation.

**V77 SorryDB preflight is resolved.** The repaired exact-commit plumbing passes the official SorryDB verifier and prepares all three frozen external repositories, but none of the five solver arms solve any of the three selected tasks under the frozen budget. Treat this as a bounded capability negative at the current solver/budget, not an infrastructure failure.

The V70–V74 grammar line remains mixed: V70–V72 pass multiscale/holdout/MDL compression gates; V73 finds no stable second-level motif hierarchy; V74 transfers operator-order structure strongly into held-out math but does not establish incremental value of the V72 macro layer over the primitive grammar.

## The current thesis

The best compact state is an explicit developmental system

`A_t = (O_t, L_t, S_t, Π_t, K_t, D_t, V)`

where `O` are verified capabilities, `L` scoped laws, `S` applicability/revision conditions, `Π` verifier-induced distinctions/quotients, `K` constructor machinery, `D` discovery policy and `V` external authority. Neural realizations are downstream compiled implementations rather than the authoritative state.

The central bounded result is no longer merely capability accumulation:

`verified experience -> changes capability structure -> changes what evidence/obstruction is reachable -> changes what new capability can subsequently be discovered`.

The model-layer result adds a practical control-path constraint:

`model proposes -> explicit capability/scope layer -> external verifier -> admit/block`.

Verified applicability must remain authoritative at execution time unless a later compiler is itself shown to preserve that distinction.

## Three remaining capstone gates

1. **Natural development:** reproduce V54-shaped compounding on pre-existing heterogeneous historical/external worlds with solutions sealed until termination.
2. **Constructor development:** establish `Constructible(K0) ⊊ Constructible(K1)` and ideally a two-generation `K1 -> K2` causal lineage. V55B is a negative for one frozen meta-substrate; V56B did not reach a verdict.
3. **Scale / economic value:** move the V56C verifier-controlled model-layer result beyond the 12-case smoke benchmark to meaningful coding-agent workloads under matched budgets, measuring held-out solves, tokens/tool calls, latency/cost, regressions and uninstallability.

Every headline transition should remain mechanically backed by verifier output, scope, provenance, ablation and result hashes.

## Canonical navigation

- [`RESEARCH_STATE.md`](RESEARCH_STATE.md) — current synthesis, evidence boundaries and priorities.
- [`results/CURRENT_FRONTIER_2026-08-14.md`](results/CURRENT_FRONTIER_2026-08-14.md) — concise current audit ledger.
- [`results/PROGRESS_V49_V56_2026-08-14.md`](results/PROGRESS_V49_V56_2026-08-14.md) — explicit V49–V56 reconciliation, including branch-only passes, negatives, incompletes and harness failures.
- `results/` — immutable experiment-specific summaries where present.
- `protocols/` — frozen/precommitted scientific protocols.
- `experiments/` — executable harnesses currently merged on `main`.
- `.github/workflows/` — reproducible CI paths currently merged on `main`.

Some of the newest experiments remain on named branches rather than `main`; the current state/frontier/progress files deliberately record those branch names and run IDs so a ZIP of `main` still preserves the research record.

## Research discipline

Closure first. Do not invent what lawful composition already expresses. Distinguish reported results from primary-artifact-attested results. Preserve negatives. Do not infer scientific failure from infrastructure failure, or scientific success from CI success. Do not let a gate name claim more than its predicate actually tests.

Current evidence does **not** establish unrestricted constructor invention, general intelligence, universal/model-independent capability installation, reliable learned multi-capability routing, natural-world developmental compounding, or open-ended recursive self-improvement.
