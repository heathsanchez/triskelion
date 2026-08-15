# V108 Generic Verifier-Induced Quotient Relation — PRECOMMIT

Date: 2026-08-15 NZST

Status: frozen before execution.

## Motivation

V107 selected `SWAP_AND_FLIP` from a supplied three-template invertible family and transferred a repair 13/13 across eight leave-one-program-out QuixBugs folds. The next attack surface is that the candidate family itself already named the relevant structural alternatives.

V108 widens the meta-language to a generic local comparison-coordinate grammar and asks whether acquisition verifier behavior uniquely induces the same quotient transport without being handed a `DUAL_CMP`/`SWAP_AND_FLIP` template.

This remains bounded relation induction inside a supplied AST edit grammar. It is not arbitrary program-transformation invention.

## External corpus

Same QuixBugs commit, frozen program list, maximum three sites per program, unchanged upstream pytest verifiers, and causal qualification procedure as V106B/V107:

`4257f44b0ff1181dedaedee6a447e133219fcebf`

Evaluation is leave-one-qualified-program-out.

## Generic action grammar

Start each qualified source site in a canonical LT coordinate frame (`left < right`) and its causal relaxed counterpart (`left <= right`).

A local coordinate action is generated only from two generic syntax choices:

1. operand position: `KEEP` or `SWAP`;
2. comparator token chosen from the six Python binary comparison tokens:
   - `<`
   - `>`
   - `<=`
   - `>=`
   - `==`
   - `!=`

No action named `DUAL_CMP`, `SWAP_AND_FLIP`, strict-order duality, or expected semantic mapping is supplied.

A candidate relation is a pair:

`(swap_bit, strict_target_token, relaxed_target_token)`

with distinct target tokens. The strict and relaxed actions must use the same operand-coordinate choice. The literal identity pair `(KEEP, <, <=)` is excluded because it creates no presentation change.

This yields a frozen generic candidate space of 59 nonidentity relation pairs.

## Evidence signature

For each acquisition task:

- the transformed strict/correct source must pass the unchanged upstream verifier;
- the transformed relaxed source must reproduce the **exact set of failing pytest node IDs** produced by the canonical LT relaxed mutation on that same task.

A mere fail/pass bit is intentionally insufficient: candidate relations must preserve the verifier-visible failure pattern, not just make something fail.

Python bytecode caches are purged between source variants; the harness invokes Python with `-B` to avoid the V107 stale-bytecode failure mode.

## Fold-local selection

For each held-out program:

1. compute candidate evidence only on acquisition programs;
2. a candidate is `PERFECT` iff both conditions above hold for every acquisition task;
3. require exactly one nonidentity perfect candidate;
4. freeze that candidate before evaluating held-out tasks.

No held-out result may break a tie or select a candidate.

## Transport

The acquisition repair is only the canonical LT transition:

`<= -> <`.

For a selected generic relation `(s, strict_target, relaxed_target)`, transport that repair to the target coordinate as:

`relaxed_target -> strict_target`

under the same operand-coordinate convention.

Held-out evaluation starts only from the transformed relaxed target presentation. No held-out search over repair tokens is allowed.

## Frozen gates

### G1 — natural qualification
At least 8 causal tasks across at least 4 programs.

### G2 — generic-space reality
Exactly 59 nonidentity candidate relation pairs are enumerated from the declared grammar; no special-case dual relation is inserted.

### G3 — unique fold-local induction
Every LOPO fold has exactly one acquisition-perfect relation under exact verifier/failure-signature matching.

### G4 — cross-fold stability
The independently induced relation is identical across all folds. Cross-fold agreement is reported only after independent selection and cannot break ties.

### G5 — literal identity baseline
Literal acquisition repair `<= -> <` with no coordinate transport solves 0 held-out target-presentation tasks.

### G6 — induced transport
The fold-local induced relation transports the repair and solves 100% of held-out tasks with unchanged upstream tests.

### G7 — causal ablation
Removing the transported repair restores the target relaxed failure on 100% of held-out tasks.

### G8 — acquisition-only selection
No held-out program result contributes to candidate scoring in its fold.

### G9 — nontrivial rejection
In every fold, at least 90% of the 59 generic candidates are rejected by acquisition verifier evidence.

### G10 — representative correctness
The induced strict target and relaxed target must each be empirically validated on held-out source before/after repair; the repaired target presentation must pass and the relaxed target must fail.

## Primary verdict

`PASS_V108_GENERIC_VERIFIER_QUOTIENT_INDUCTION` only if G1–G10 all pass.

## Allowed interpretation

A pass supports:

> On source-distinct externally authored QuixBugs programs, a repair-transport quotient relation can be induced uniquely from acquisition verifier behavior within a generic 59-relation comparison-edit grammar, then transfer causally to held-out programs where literal repair identity fails.

It does not establish arbitrary transformation invention, generic natural-code ontology discovery, historical bug repair, or representation-independent conceptual identity.
