# Current Frontier Audit — 2026-08-14 16:15 NZST

This is the concise current ledger. Historical result files remain immutable and authoritative for their own experiments. Branch-only work is recorded here so a ZIP of `main` does not silently lose the research state. Detailed V49–V56 chronology: [`PROGRESS_V49_V56_2026-08-14.md`](PROGRESS_V49_V56_2026-08-14.md).

## Strongest current bounded positives

### V54 — two-generation developmental compounding — PASS

Branch: `v54-compounding-ratchet`  
Run: `31761530951`

Under the frozen one-new-generator search budget, the later target had zero cold one-rewrite survivors before O1. After lawful reuse of O1, exactly one new operator O2 (`and -> or`) became discoverable. Execution chain:

- `A0`: FAIL
- `A0 + O1`: FAIL
- `A0 + O1 + O2`: PASS
- `A0 + O2` with O1 ablated: FAIL

Bounded conclusion: acquired capability structure can causally change what capability becomes discoverable next.

### V51 — genuine effective-closure expansion — PASS

`< -> <=` is outside the frozen old token-position closure because the old transformations preserve token-value multisets. A generic emission substrate constructed the new operator from external obstructions, it transferred to sealed Requests, ablation restored failure, and later counterevidence triggered scope revision/revocation logic.

### V49 / V50 — sealed transfer and verifier-derived labels — PASS

V49 committed the learned category before Requests was opened, then demonstrated cold FAIL -> warm PASS -> ablation FAIL -> later contradiction -> revoke.

V50 generated HELP/HARM labels from executable verifier transitions rather than supplying class labels, then repeated sealed transfer and later revocation.

### V56C — structurally verifier-controlled model layer — PASS

Model: `Qwen/Qwen2.5-Coder-0.5B-Instruct`.

Frozen 12-case applicability benchmark:

- no memory: 6/12;
- raw memory: 6/12;
- verifier-controlled capability layer: **12/12**.

The model often proposed `KEEP`; the explicit verifier-controlled layer overrode it to `WIDEN` only on the six cases where executable boundary semantics allowed widening, while preserving all six protected cases.

Verdict: `PASS_V56C_VERIFIER_MODEL_LAYER`.

Architectural implication supported by this bounded test:

`model proposes -> explicit capability/scope layer -> external verifier -> admit/block`

Applicability authority should remain explicit unless a later compiler is itself shown to preserve it.

### IKKF V4b — verifier-induced invocation — PASS

A coarse scope admitted multiple candidate sites. External target+protected verification uniquely retained the real invocation and rejected the false positive. Repair passed, ablation failed, and later counterevidence revoked the capability.

### IKKF V2d — Verified Capability OS comparison — PASS

Exact V2c held-out worlds and same C/J modules: verifier-controlled invocation reached 100% routing and 100% execution, versus the V2c learned router's 50% routing and 0% joint execution. This supports external/explicit invocation authority, not yet cheap learned routing.

### V18b — protected adaptive consolidation — ATTESTED

Primary artifact checked. New direct competence was consolidated while measured ancestors/composites remained passing and persisted through reload. Bounded protected consolidation only; no claim of arbitrary regression-free neural editing.

### IKKF V1 — reproducible fresh capability compilation — ATTESTED WITH CORRECTION

- B0, C1, C2, J, U and R are separately executed.
- C1 fresh compilation: held-out score 1.0.
- C2 second fresh compilation call: held-out score 1.0.
- decoy J: 0.0.
- fresh/uninstalled U: 0.0.
- reload R: 1.0.

Correction: C1 and C2 have bit-identical training curves despite nominally different seeds, and the `independent_recompile` gate only checks that both scores pass. Supported wording is **reproducible fresh recompilation / separate second execution**, not yet genuine stochastic independence.

### V68 — incremental reversible Lawbook — PASS

Verifier distinctions refine scoped equivalence classes; local splits preserve unrelated classes/provenance, reversal restores the prior partition, and refinement can expose capability hidden by a coarser quotient.

### V70–V72 — grammar/motif sequence — PASS

- V70: held-out-domain compression 30.2817% vs 16.3162% shuffled mean.
- V71: whole-scale compression 23.9437% vs 12.3676% shuffled mean; next-op 48.3516% vs 23.0769% majority.
- V72: exact MDL raw cost 142 -> 120 including motif definitions; 15.493% saving vs 5.632% shuffled mean.

## Useful negatives / incompletes

### V55A — historical/natural replication — INCOMPLETE

Only two frozen BugsInPy worlds became usable, both from Black. Neither produced a unique O1 under the generic token-rewrite constructor. The V54-style cross-project mechanism was therefore never reached.

Interpretation: natural-world coverage/localization/constructor expressivity is the current obstruction. Do not label this as evidence against V54-style compounding.

### V56A — historical blind-edit retry — HARNESS FAILURE

The broader rewrite/delete/insert clean-room retry crashed with an `IndexError` from stale/out-of-range edit coordinates. No scientific verdict. Natural historical replication remains open.

### V55B — constructor-level compounding — FAIL under tested meta-substrate

`K0 = REWRITE_EXISTING_TOKEN` correctly could not repair a deletion-style obstruction, but the frozen insert-by-token-type constructor language failed to synthesize `K1`; therefore no `K2` lineage could be exposed.

Verdict: `FAIL_V55B_CONSTRUCTOR_LEVEL_COMPOUNDING`.

### V56B — robust constructor retry — HARNESS FAILURE

An intermediate insertion created temporarily invalid indentation and tokenization raised `IndentationError` instead of treating that candidate as a normal rejected construction. No scientific verdict. V55B remains the current scientific negative for constructor-level growth.

### V55C — naive prompt-level verified capability — MIXED / negative

Scores: no memory 6/12, raw memory 5/12, verified capability card 5/12. Helpful-transfer cases were solved, but protected negatives were 0%, showing that describing verified scope in prose is not sufficient.

Verdict: `MIXED_V55C_MODEL_LAYER_SMOKE`.

### V52e / V53 — historical-world coverage — INCOMPLETE / NEGATIVE AT ADAPTER BOUNDARY

Historical environment reconstruction and source/localization coverage removed too many worlds. Preserve as evidence that natural-world replication remains open rather than silently broadening the protocol.

### IKKF V2b / V2c / V3 — neural applicability negatives

- V2b: shared C+J LoRA collapsed onto C: `C=1, J=0, route=.5`.
- V2c: separate explicit C/J modules with only the selector learned still collapsed to one label: 50% routing, 0% joint execution.
- V3: explicit V51 construction/export/sealed transfer/ablation/counterevidence/revocation passed, but correct-scope neural compilations collapsed to `NOOP`; inverted-scope control activated everywhere.

These negatives motivated V56C's architecture: keep applicability authority explicit and verifier-controlled.

### V73 — hierarchy negative

Reifying the V72 motifs did not yield stable second-level recurrent motifs under the frozen hierarchy gates. No recursive/fractal-organ claim.

### V74 — mixed math transfer

Primitive operator-order structure trained without math ranks held-out math traces strongly, but the macro layer does not beat the primitive grammar and misses the frozen shuffle threshold (`p=.03498 > .01`).

### V77 — SorryDB preflight resolved as capability negative

The repaired exact-commit plumbing passes the official SorryDB verifier and prepares all three frozen external repositories. None of the five frozen solver arms solve any of the three selected tasks under the frozen budget. This is no longer an infrastructure block.

## Current scientific picture

The evidence now separates several coupled layers:

1. **Capability algebra** — explicit operators can be composed, constructed outside old closure, retained and causally reused.
2. **Applicability/law algebra** — scope and equivalence are verifier-indexed, revisable and revocable.
3. **Ontology/quotient** — added verification can create new operational distinctions and refine equivalence classes.
4. **Constructor algebra** — verified instances can induce reusable constructor families; whether the constructor language itself can developmentally compound remains open.
5. **Compilation** — explicit capability can be compiled into bounded neural competence, but unconstrained learned routing/scope preservation has strong negatives.
6. **Developmental compounding** — V54 shows in bounded form that possessing O1 can make O2 discoverable under the same frozen search budget.
7. **Verifier-controlled model augmentation** — V56C shows on a bounded 12-case test that explicit external applicability checking can turn the same fixed small model from 6/12 to 12/12.

## Three remaining capstone gates

1. **Natural development:** V54-shaped compounding on natural, heterogeneous, pre-existing worlds with solutions sealed.
2. **Constructor development:** establish `Constructible(K0) ⊊ Constructible(K1)`, ideally followed by a K1 -> K2 causal lineage. V55B is a negative for one meta-substrate; V56B did not reach a verdict.
3. **Scale/economic value:** matched sequential comparisons against base, episodic memory and ordinary adaptation on meaningful coding-agent workloads; measure held-out solves, tokens/tool calls, latency/cost, regressions, uninstallability and performance-vs-experience.

## Evidence discipline

Classify every headline as **ATTESTED**, **BOUNDED PASS**, **NEGATIVE**, **INCOMPLETE/INFRASTRUCTURE**, or **REPORTED/NEEDS ATTESTATION**. A successful GitHub Actions job is not itself a scientific verdict. A gate name cannot claim more than the predicate implements.

## Canonical navigation

- `RESEARCH_STATE.md` — long-form synthesis.
- `results/CURRENT_FRONTIER_2026-08-14.md` — this file.
- `results/PROGRESS_V49_V56_2026-08-14.md` — detailed newest ledger.
- `results/IKKF_V2C_MODULAR_ROUTER_NEGATIVE_20260814.md` — frozen modular-selector negative.
- `results/IKKF_V3_EXTERNAL_INVENTED_INSTINCT_NEGATIVE_20260814.md` — frozen whole-stack neural-bridge negative.
- `results/V45_V66_LEDGER.txt` — historical external quotient sequence; do not rewrite retrospectively.
