# V107 Inferred Natural-Code Quotient Relation — PRECOMMIT

Date: 2026-08-15 NZST

Status: frozen after V106B and before V107 execution.

## Question

V106B showed that a **supplied** invertible comparison dualization makes a strict-bound repair transfer across every qualifying QuixBugs source family while literal repair identity fails.

V107 removes that hand-specified identity relation from the learner:

> Can the equivalence relation itself be selected from a generic candidate transformation family using acquisition-side external verifier evidence only, then causally transfer a repair to source-distinct held-out code?

The candidate transformation meta-language remains supplied.

## External corpus and qualification

Exactly the V106B corpus and qualification procedure:

- QuixBugs commit `4257f44b0ff1181dedaedee6a447e133219fcebf`;
- same frozen non-graph program list;
- first three eligible strict comparison sites per program;
- source only from `correct_python_programs/`;
- unchanged upstream `python_testcases/` verifier;
- retain a task only when strict LT and strict GT coordinate presentations both pass, their inclusive relaxations both fail, and tightening restores both.

Do not hard-code the V106B qualified program list; recompute qualification.

## Candidate coordinate meta-language

For a canonical strict source comparison `a < b`, generate the following eight candidate presentations mechanically:

1. `a < b` — `ID_LT`
2. `b > a` — `SWAP_GT`
3. `a > b` — `GT_ONLY`
4. `b < a` — `SWAP_LT`
5. `a <= b` — `LE_ONLY`
6. `b >= a` — `SWAP_GE`
7. `a >= b` — `GE_ONLY`
8. `b <= a` — `SWAP_LE`

The learner is not told which candidates preserve semantics.

Each candidate is a reversible syntactic coordinate rewrite inside this local meta-language, but only verifier-preserving candidates may enter the learned identity relation.

## Inference rule

Use leave-one-qualified-program-out folds exactly as V106B.

For each fold, on acquisition programs only:

1. evaluate each of the eight candidate coordinate presentations at every qualified acquisition site under the unchanged upstream verifier;
2. retain candidates that pass **all** acquisition sites;
3. require `ID_LT` to survive;
4. among non-identity candidates, require exactly one survivor;
5. derive the repair conjugacy from that survivor mechanically: apply the same coordinate rewrite to the relaxed acquisition form `a <= b`; observe its resulting inclusive operator/orientation; pair its strict target with that inclusive source to obtain the held-out literal repair.

No held-out verifier result may influence candidate selection or action conjugacy.

## Frozen held-out test

Each held-out program is presented only in canonical-GT relaxed coordinates.

Compare:

- **literal baseline:** retain `LE_TO_LT` only;
- **inferred quotient arm:** use the acquisition-inferred non-identity coordinate relation and mechanically conjugated repair action.

## Frozen gates

### G1 — qualification floor
At least 8 tasks across at least 4 programs.

### G2 — unique acquisition-side relation
In every LOPO fold:
- `ID_LT` survives acquisition verification;
- exactly one non-identity candidate survives all acquisition tasks.

### G3 — relation stability
The same non-identity candidate is selected independently in every LOPO fold.

### G4 — harmful candidates rejected
Every candidate not in `{ID_LT, selected_nonidentity}` must fail at least one acquisition verifier in every fold. No candidate is rejected using held-out evidence.

### G5 — conjugacy inferred without label
The held-out repair literal is derived mechanically from the selected coordinate rewrite applied to relaxed/strict forms; it is not hard-coded as `GE_TO_GT` in the selection rule.

### G6 — source-distinct transfer
Across all held-out tasks over all LOPO folds:
- literal baseline solves 0%;
- inferred quotient repair solves 100%.

### G7 — foldwise universality
Every held-out program fold individually satisfies 0% literal and 100% inferred-quotient repair.

### G8 — causal ablation
Removing the inferred quotient repair restores failure on every held-out task.

### G9 — no source leakage
Held-out program absent from acquisition in every fold.

## Primary verdict

`PASS_V107_INFERRED_NATURAL_CODE_QUOTIENT` only if G1–G9 all pass.

## Allowed interpretation

A pass supports:

> Within a supplied generic local comparison-transformation meta-language, acquisition-side external verification uniquely identifies a nontrivial semantics-preserving coordinate relation; that inferred relation mechanically induces the correct conjugate repair and transfers across every qualifying source-distinct QuixBugs program under unchanged tests.

It does not establish arbitrary relation invention, unrestricted natural operator discovery, historical bug repair, or representation-independent identity.

## Next-step trigger

If V107 passes, the next test should widen the candidate transformation language and/or move to a fresh code corpus/mutation family so the relation cannot be recovered from this same comparison-specific substrate alone.
