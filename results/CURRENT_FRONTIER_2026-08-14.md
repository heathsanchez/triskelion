# Current Frontier Audit — 2026-08-14 16:11 NZST

This is the concise current ledger. Historical result files remain immutable and authoritative for their own experiments. Branch-only work is recorded here so a ZIP of `main` does not silently lose the research state.

## Strongest current bounded positives

### V54 — two-generation developmental compounding — PASS

Branch: `v54-compounding-ratchet`  
Run: `31761530951`  
Head: `2dd5f41b6c7cec1004b8deaee4f976dd2a9ed21c`

Under the frozen one-new-generator search budget, the later target had zero cold one-rewrite survivors before O1. After lawful reuse of O1, exactly one new operator O2 (`and -> or`) became discoverable. Execution chain:

- `A0`: FAIL
- `A0 + O1`: FAIL
- `A0 + O1 + O2`: PASS
- `A0 + O2` with O1 ablated: FAIL

Bounded conclusion: acquired capability structure can causally change what capability becomes discoverable next.

### V51 — genuine effective-closure expansion — PASS

`< -> <=` is outside the frozen old token-position closure because the old transformations preserve token-value multisets. A generic emission substrate constructed the new operator from external obstructions, it transferred to sealed Requests, ablation restored failure, and later counterevidence triggered scope revision/revocation logic.

### IKKF V4b — verifier-induced invocation — PASS

Branch: `ikkf-v4b-verifier-induced-invocation`.

A coarse scope admitted two candidate Requests sites. External target+protected verification uniquely retained the real invocation and rejected the false positive. Repair passed, ablation failed, and later counterevidence revoked the capability. Applicability can therefore be verifier-refined in this bounded setting.

### IKKF V2d — Verified Capability OS comparison — PASS

Branch: `ikkf-v2d-verified-capability-os`.

Exact V2c held-out worlds and same C/J modules: verifier-controlled invocation reached 100% routing and 100% execution, versus the V2c learned router's 50% routing and 0% joint execution. This supports external/explicit invocation authority, not yet cheap learned routing.

### V18b — protected adaptive consolidation — ATTESTED

Primary artifact checked. New direct competence was consolidated while measured ancestors/composites remained passing and persisted through reload. Bounded protected consolidation only; no claim of arbitrary regression-free neural editing.

### IKKF V1 — reproducible fresh capability compilation — ATTESTED WITH CORRECTION

Primary harness/protocol/result inspected directly.

- B0, C1, C2, J, U and R are separately executed.
- C1 fresh compilation: held-out score 1.0.
- C2 second fresh compilation call: held-out score 1.0.
- decoy J: 0.0.
- fresh/uninstalled U: 0.0.
- reload R: 1.0.
- held-out worlds do not appear in gradient batches.

**Correction:** C1 and C2 have bit-identical training curves despite nominally different seeds, and the `independent_recompile` gate only checks that both scores pass. Therefore the supported wording is **reproducible fresh recompilation / separate second execution**, not yet genuine stochastic independence. A hardened independence gate must inspect effective config and/or adapter hashes/weights.

### V68 — incremental reversible Lawbook — PASS

Verifier distinctions refine scoped equivalence classes; local splits preserve unrelated classes/provenance, reversal restores the prior partition, and refinement can expose capability hidden by a coarser quotient.

### V70–V72 — grammar/motif sequence — PASS

- V70: held-out-domain compression 30.2817% vs 16.3162% shuffled mean.
- V71: whole-scale compression 23.9437% vs 12.3676% shuffled mean; next-op 48.3516% vs 23.0769% majority.
- V72: exact MDL raw cost 142 -> 120 including motif definitions; 15.493% saving vs 5.632% shuffled mean.

## Useful negatives / incompletes

### V55 — natural historical compounding — INCOMPLETE

Branch: `v55-natural-historical-compounding`.

Only two frozen BugsInPy worlds became usable, both from Black. Neither produced a unique O1 under the generic token-rewrite constructor. The V54-style cross-project mechanism was therefore never reached.

Interpretation: natural-world coverage/localization/constructor expressivity is the current obstruction. Do not label this as evidence against V54-style compounding.

### V52e / V53 — historical-world coverage — INCOMPLETE / NEGATIVE AT ADAPTER BOUNDARY

Historical environment reconstruction and source/localization coverage removed too many worlds. Preserve as evidence that natural-world replication remains open rather than silently broadening the protocol.

### IKKF V2b — routing negative

Shared C+J LoRA collapsed onto C: `C=1, J=0, route=.5`.

### IKKF V2c — modular selector negative

Separate explicit C/J modules with only the selector learned still collapsed to one label: 50% routing, 0% joint execution. Modular execution alone does not solve applicability selection.

### IKKF V3 — scope-preserving neural bridge negative

Explicit V51 construction/export/sealed transfer/ablation/counterevidence/revocation passed, but correct-scope neural compilations collapsed to `NOOP`; inverted-scope control activated everywhere. Preserve unchanged as evidence that verified applicability semantics were not preserved by the frozen compiler.

### V73 — hierarchy negative

Reifying the V72 motifs did not yield stable second-level recurrent motifs under the frozen hierarchy gates. No recursive/fractal-organ claim.

### V74 — mixed math transfer

Primitive operator-order structure trained without math ranks held-out math traces strongly, but the macro layer does not beat the primitive grammar and misses the frozen shuffle threshold (`p=.03498 > .01`).

### V77 — SorryDB preflight resolved as capability negative

The repaired exact-commit plumbing passes the official SorryDB verifier and prepares all three frozen external repositories. None of the five frozen solver arms solve any of the three selected tasks under the frozen budget. This is no longer an infrastructure block.

### V2f — explicit invocation-law experiment requires hardening

The first evaluator may consult both candidate modules before claiming selected-only execution. Do not promote any nominal pass from that evaluator. A successor must select before executing/consulting the nonselected capability.

## Current scientific picture

The evidence now separates several coupled layers:

1. **Capability algebra** — explicit operators can be composed, constructed outside old closure, retained and causally reused.
2. **Applicability/law algebra** — scope and equivalence are verifier-indexed, revisable and revocable.
3. **Ontology/quotient** — added verification can create new operational distinctions and refine equivalence classes.
4. **Constructor algebra** — verified instances can induce reusable constructor families; the next open gate is whether the constructor language itself can develop.
5. **Compilation** — explicit capability can be compiled into bounded neural competence, but scope-preserving and multi-capability neural routing remain unsolved.
6. **Developmental compounding** — V54 shows in bounded form that possessing O1 can make O2 discoverable under the same frozen search budget.

## Three capstone gates

1. **Natural development:** V54-shaped compounding on natural, heterogeneous, pre-existing worlds with solutions sealed.
2. **Economic compounding:** matched sequential A/B against base, episodic memory and ordinary adaptation; measure capability/cost curves, regressions, latency and uninstallability.
3. **Attested lifecycle:** primary evidence must mechanically back every Discover -> Verify -> Install -> Invoke -> Compile -> Revise claim. This is a precondition for the other two gates counting.

## Immediate next experiment

Use V55's repeated natural constructor/localization failures as pressure for a prospective constructor-development test:

`K0 --verified obstruction--> K1`

then require a later capability/family with `O2 ∉ Constructible(K0)` but `O2 ∈ Constructible(K1)`, plus K1 ablation. After that, retry natural historical compounding without changing V55 retrospectively.

## Evidence discipline

Classify every headline as **ATTESTED**, **BOUNDED PASS**, **NEGATIVE**, **INCOMPLETE/INFRASTRUCTURE**, or **REPORTED/NEEDS ATTESTATION**. A successful GitHub Actions job is not itself a scientific verdict. A gate name cannot claim more than the predicate implements.
