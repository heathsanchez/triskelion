# DEVELOPMENTAL IR V1 — prospective precommit

Status: **FROZEN BEFORE IMPLEMENTATION OR OUTCOME EXECUTION**

## Original goal

The governing question remains:

[
oxed{	extbf{What is the smallest nucleus from which warranted development can regenerate every form it needs?}}
]

The immediately preceding experiments reduced the bounded Boolean developmental substrate to one asymmetric equivalence class represented by

[
D(a,b)=
eg aland b
]

together with one appropriate ground/reference and external verification.

This experiment asks whether that nucleus can serve as an **efficient executable intermediate language** whose verified results become reusable instructions.

It does **not** ask whether a Python prototype is faster than LLVM, machine code, Lean, or a production JIT in wall-clock time.

The primary efficiency metric is exact abstract execution cost under a frozen machine model.

## Candidate language

The kernel IR has only these semantic primitives:

1. `GROUND` — the single fixed anchor (1).
2. `INPUT i` — an encounter/input bit-vector supplied by the environment.
3. `D a b` — directed difference:
   [
   D(a,b)=
eg aland b.
   ]
4. `VERIFY x target` — external exact authority checks whether x has the protected target consequence.
5. `PROMOTE x name` — only after VERIFY succeeds, x becomes a reusable capability instruction.

A promoted capability may subsequently be invoked as a unit-cost leaf.

The verifier is outside the developmental nucleus.

## Derived source language

A human-facing Boolean DSL is compiled into the kernel IR.

The source DSL contains:

- NOT
- AND
- OR
- XOR
- IMP
- NAND
- NOR
- EQ

None of these is primitive in the kernel.

Before benchmarking, the implementation must mechanically derive each source operator from (D) and `GROUND=1`, then exhaustively verify all four input rows.

Gate U1 requires all 16 two-input Boolean relations to be expressible by recursive (D)+GROUND composition.

This is an exact finite functional-completeness bridge, not a claim of Turing universality.

## Execution universe

Use 12 independent Boolean environmental inputs.

The exact carrier contains:

[
2^{12}=4096
]

rows.

Every semantic value is a complete 4096-bit truth vector.

Semantic equality in this V1 is exact.

## Three execution arms

Every task has one fully expanded semantic source expression. The three arms execute the same target consequences.

### TREE

Conventional immutable expression tree.

Every source operator is lowered to (D)+GROUND and every primitive D node is executed whenever encountered.

No sharing.

### LOCAL_DAG

Within one task only, identical kernel subexpressions are hash-consed and evaluated once.

No cross-task state survives.

This is the ordinary common-subexpression / DAG control.

### DEVELOPMENTAL

Uses the same local hash-consing plus a persistent verified capability archive.

After a result is externally verified, eligible subgraphs may be promoted.

A future occurrence of a promoted capability may compile to a unit-cost `CAP` leaf rather than replaying its internal D graph.

Promotion is content-addressed by exact protected semantics in this finite V1, so semantically equivalent source forms may reuse the same verified capability even when their syntax differs.

A semantic hit is legal only because exact authority has already certified that protected consequence.

## Cost model

Primary costs are integers.

- INPUT leaf: 0 primitive operations.
- GROUND leaf: 0 primitive operations.
- primitive D execution: 1.
- local hash lookup: not charged to semantic execution cost but counted separately.
- promoted CAP invocation: 1.
- VERIFY: counted separately as verifier work and never hidden inside execution cost.
- PROMOTE bookkeeping: counted separately and never hidden inside execution cost.

Report both:

[
C_{	ext{exec}}
]

and

[
C_{	ext{total}}=
C_{	ext{exec}}+C_{	ext{verify}}+C_{	ext{promotion}}.
]

The frozen verifier cost is one unit per complete exact target verification. This is a deliberately conservative abstraction: the full 4096-row check is implemented but represented as one authority call for amortization accounting.

Promotion bookkeeping costs one unit per newly promoted capability.

## Developmental workload

Generate a deterministic stream of 20,000 exact tasks.

### Phase 0 — seed

Start with only the 12 INPUTs and GROUND.

No derived capability is initially installed.

### Phase 1 — curriculum (tasks 1–1,000)

Mechanically generate source expressions of depth 3–8 over the rich source DSL.

Each task must denote a semantic function not previously used as a top-level target whenever the finite generator can supply one.

After exact verification, the DEVELOPMENTAL arm may promote the target if its fully expanded kernel cost is at least 5.

### Phase 2 — descendants (tasks 1,001–10,000)

Each task is mechanically generated from:

- one or two previously verified target semantics;
- one source-language relation;
- zero to two fresh environmental inputs.

For DEVELOPMENTAL, previously verified ancestors may be invoked as CAP leaves.

TREE and LOCAL_DAG receive the fully expanded ancestral definitions, so all arms compute the same denotation from the same historical definitions.

At least one parent must be a generated capability.

### Phase 3 — semantic twins (tasks 10,001–15,000)

Generate syntax-distinct expressions that are exactly equivalent to existing promoted capabilities using only frozen Boolean identities:

- double negation;
- De Morgan expansion;
- implication expansion;
- commuted AND/OR;
- XOR canonical alternative.

The DEVELOPMENTAL arm may quotient these to the already verified capability by exact semantic identity.

TREE and LOCAL_DAG must execute the presented expanded syntax.

This phase measures semantic quotient value beyond exact syntax memoization.

### Phase 4 — recombinant stream (tasks 15,001–20,000)

Mechanically choose two capabilities from distinct ancestry regions and form a new target relation over them.

The child is externally verified and may itself be promoted.

Record whether later tasks reuse recombinant descendants.

No manually selected favorable targets are allowed.

## Promotion policy

A verified target is promoted iff:

1. exact verification succeeds;
2. expanded minimum kernel execution cost >= 5;
3. its protected semantics are not already represented by a capability.

If semantics already exist, reuse the existing capability instead of duplicating it.

This is QCK-style semantic quotienting in the exact finite V1.

## Controls

### NO_PROMOTION

Persistent archive metadata exists but promoted capabilities may not be invoked.

### SYNTAX_ONLY

Cross-task capability reuse is keyed only by canonical kernel syntax, not exact semantics.

This separates ordinary macro/cache reuse from semantic quotienting.

### NO_WARRANT

Forbidden as a positive arm. Proposals may be generated but cannot be installed without VERIFY. Report archive growth = 0.

### COLD_ARCHIVE

Clear all promoted capabilities before every task.

### NO_RECOMBINATION

Phase-4 children verify but are not promoted.

This tests whether recombinant children themselves contribute to later amortization.

## Exact correctness gates

For every one of 20,000 tasks:

[
	ext{TREE semantics}
=
	ext{LOCAL_DAG semantics}
=
	ext{DEVELOPMENTAL semantics}
=
	ext{external target}.
]

Zero wrong answers are permitted.

The exact verifier must reject an intentionally corrupted target in a sealed negative probe.

## Efficiency gates

E1. All 16 binary Boolean relations are derivable from D+GROUND.

E2. Zero semantic disagreements across 20,000 tasks.

E3. DEVELOPMENTAL total primitive execution cost is < 50% of TREE over the full stream.

E4. DEVELOPMENTAL total primitive execution cost is < 75% of LOCAL_DAG over the full stream.

E5. Including VERIFY+PROMOTE accounting, DEVELOPMENTAL cumulative total cost eventually becomes lower than TREE; report the exact break-even task.

E6. The marginal mean DEVELOPMENTAL execution cost over the last 1,000 tasks is lower than over tasks 1–1,000.

E7. At least 80% of descendant tasks after task 5,000 invoke at least one promoted ancestor.

E8. Semantic-twin phase DEVELOPMENTAL cost is < 50% of SYNTAX_ONLY.

E9. COLD_ARCHIVE loses at least 80% of DEVELOPMENTAL execution savings versus TREE.

E10. NO_PROMOTION loses at least 80% of DEVELOPMENTAL execution savings versus TREE.

E11. NO_WARRANT installs zero capabilities.

E12. Sealed corrupted-target probe is rejected.

E13. At least 100 recombinant Phase-4 children are later reused by another task.

E14. NO_RECOMBINATION has strictly higher Phase-4 execution cost than DEVELOPMENTAL after the first 1,000 Phase-4 tasks.

E15. Semantic archive contains no duplicate protected semantics.

E16. Re-running the frozen stream from empty state yields the identical capability ledger hash and cost vector.

## Outputs

Record:

- exact derived formula for each source operator;
- exhaustive 16-relation derivability table;
- total and per-phase TREE cost;
- total and per-phase LOCAL_DAG cost;
- total and per-phase DEVELOPMENTAL cost;
- total verifier calls;
- promotions;
- semantic reuse hits;
- syntax reuse hits;
- exact cumulative break-even task;
- first-1k and last-1k marginal costs;
- capability count;
- ancestry depth;
- recombinant children and later reuse count;
- control-arm costs;
- deterministic capability-ledger SHA-256;
- all E1–E16 gates.

## Verdicts

- `PASS_DEVELOPMENTAL_IR_V1`
- `PARTIAL_DEVELOPMENTAL_IR_V1`
- `VALID_NEGATIVE_DEVELOPMENTAL_IR_V1`

PASS requires E1–E16.

## Claim boundary

A PASS would establish only that, in this exact finite Boolean workload and frozen abstract cost model:

- the one-anchor directed-difference nucleus can host a richer derived Boolean language;
- verified promoted capabilities can act as reusable instructions;
- persistent semantic quotienting can amortize repeated related computation beyond tree execution and task-local DAG sharing;
- semantic reuse can beat syntax-only reuse on deliberately syntax-diverse but consequence-equivalent tasks.

It would **not** establish:

- lower real wall time than LLVM, native machine code, Lean, Rust, C, Python, or production JITs;
- Turing universality;
- superiority to lambda calculus or type theory;
- open-ended intelligence;
- that exact truth-vector semantic quotienting is available in unrestricted real domains.

The purpose is to test whether the nucleus can support the first honest version of a **verified developmental intermediate language**.
