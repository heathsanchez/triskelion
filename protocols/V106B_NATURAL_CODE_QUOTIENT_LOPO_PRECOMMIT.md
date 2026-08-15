# V106B Natural-Code Quotient Bridge — Leave-One-Program-Out PRECOMMIT

Date: 2026-08-15 NZST

Status: frozen after V106's split-coverage failure and before V106B execution.

## Why a new experiment

V106 produced 13 qualified tasks across 8 external QuixBugs programs, but its precommitted one-shot hash split put 7 qualifying programs in acquisition and only 1 in held-out. Therefore V106 failed G1 and remains MIXED.

V106B does **not** change the qualification rule, external corpus, mutation, repair class, coordinate relation, program list, or first-three-site cap. It changes only the source-distinct evaluation design to remove dependence on one arbitrary partition.

## Frozen qualification

Exactly the V106 qualification procedure:

- QuixBugs commit `4257f44b0ff1181dedaedee6a447e133219fcebf`;
- same frozen non-graph program list;
- first three eligible single-comparator `<`/`>` AST sites per program;
- natural source is `correct_python_programs/`;
- unchanged `python_testcases/` verifier;
- `DUAL_CMP`: `a < b <-> b > a`;
- controlled mutation class `RELAX_STRICT`: `< -> <=`, `> -> >=`;
- repair class `TIGHTEN_STRICT`: `<= -> <`, `>= -> >`;
- retain a task only when both unmutated presentations pass, both relaxed presentations fail, and both repaired presentations pass.

No V106 task list is hard-coded into V106B. Qualification is recomputed from the pinned external corpus.

## Frozen source-distinct evaluation

Let `P` be the set of programs having at least one qualified task.

Evaluate **leave-one-qualified-program-out (LOPO)** folds:

For every `p in P`:
- held-out = all qualified tasks from program `p` in canonical-GT presentation;
- acquisition = all qualified tasks from programs `P - {p}` in canonical-LT presentation.

Every qualifying source family therefore serves as held-out exactly once.

## Arms

### Literal retention
Acquisition exposes only `LE_TO_LT`. The retained object is the literal edit `LE_TO_LT`; no coordinate conversion is permitted.

### Quotient retention
Acquisition retains `TIGHTEN_STRICT` modulo the supplied invertible `DUAL_CMP` relation, and may instantiate `GE_TO_GT` in the held-out GT presentation.

No extra candidate search is given to the quotient arm.

## Frozen gates

### G1 — natural qualification floor
At least 8 qualified tasks across at least 4 distinct programs.

### G2 — LOPO coverage
At least 4 LOPO folds and every qualifying program appears in exactly one held-out fold.

### G3 — literal failure under coordinate shift
Across all held-out tasks over all LOPO folds, literal `LE_TO_LT` solves 0 tasks.

### G4 — quotient transfer
Across all held-out tasks over all LOPO folds, quotient-instantiated `GE_TO_GT` repairs 100% of tasks under unchanged upstream tests.

### G5 — foldwise universality
Every individual held-out program fold has quotient repair rate 100% and literal repair rate 0%.

### G6 — causal ablation
For every held-out task, removing the quotient repair restores the relaxed failing state.

### G7 — representative equivalence
For every qualified task, repaired canonical-LT and canonical-GT presentations both pass unchanged upstream tests.

### G8 — no source leakage
Within every fold, the held-out program name is absent from acquisition.

### G9 — negative identity control
Non-invertible transformations remain excluded from capability identity and the reason is reported.

## Primary verdict

`PASS_V106B_NATURAL_CODE_QUOTIENT_LOPO` only if G1–G9 all pass.

## Allowed interpretation

A pass supports:

> Across every qualifying source family in this controlled natural-code bridge, representing a strict-bound repair as a quotient class under an invertible semantics-preserving source transformation transfers across source-distinct deliberate coordinate changes, while retaining the literal repair token alone does not.

It still does **not** establish:
- autonomous discovery of the quotient relation;
- historical natural bug repair;
- autonomous operator invention;
- a natural-code capability lattice;
- representation-independent novelty.

## Next-step trigger

If V106B passes, the next experiment must infer the equivalence relation itself from acquisition-side verifier behavior rather than supplying `DUAL_CMP` by hand.
