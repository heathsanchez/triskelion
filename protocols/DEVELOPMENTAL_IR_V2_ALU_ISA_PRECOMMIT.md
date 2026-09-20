# DEVELOPMENTAL IR V2 — EMERGENT ALU ISA — prospective precommit

Status: **FROZEN BEFORE IMPLEMENTATION OR OUTCOME EXECUTION**

## Governing question

[
oxed{	extbf{Can the one-anchor directed-difference nucleus grow a useful instruction set for exact arithmetic programs, not just Boolean toy expressions?}}
]

V1 established a partial but strong bounded result: exact correctness over 20,000 Boolean tasks, all 16 Boolean relations derived from (D(a,b)=
eg aland b) plus ground, persistent verified capability reuse, semantic quotienting beyond syntax caching, deterministic replay, and large abstract-cost reductions. Its only frozen gate failures were controls normalized against the huge TREE baseline rather than the already optimized LOCAL_DAG baseline.

V2 does not weaken V1 retroactively. It changes the workload and preregisters the causal comparison against LOCAL_DAG.

## Kernel

The developmental kernel remains:

- GROUND = 1
- INPUT
- (D(a,b)=
eg aland b)
- VERIFY
- PROMOTE

No arithmetic operator is primitive.

## Exact execution universe

Use two independent unsigned 8-bit words (A,B).

All (2^{16}=65,536) input pairs are represented simultaneously and exactly as truth vectors.

Every output bit is therefore a complete 65,536-row Boolean consequence.

## Derived source language

Mechanically derive from D+GROUND:

- NOT
- AND
- OR
- XOR
- NAND
- NOR
- EQ bit relation

Then build exact 8-bit operations solely from those derived bit relations:

- BITNOT
- BITAND
- BITOR
- BITXOR
- ADD8
- SUB8
- INC8
- ROL1
- ROR1
- MUX8

ADD8 and SUB8 are ripple-carry constructions; no host arithmetic is used to execute the IR.

An independent host-side exact bit-vector evaluator computes the protected target semantics for verification.

## Workload

Run 6,000 deterministic tasks.

### Phase 1 — arithmetic curriculum, tasks 1–1,000
Generate depth-2..4 programs over the 8-bit source operations from (A,B). Prefer top-level denotations not previously used.

### Phase 2 — capability descendants, tasks 1,001–3,500
Each task must use at least one previously verified task output as an operand and mechanically compose it with another capability or base input through one source operation.

### Phase 3 — semantic twins, tasks 3,501–4,500
Generate syntax-distinct programs with exactly the semantics of earlier verified outputs using frozen identities such as:

- double NOT
- XOR zero
- AND all-ones
- ADD zero
- ROL8 identity implemented as eight ROL1 applications

### Phase 4 — recombinant children, tasks 4,501–5,500
Mechanically select two verified capabilities from distinct ancestry regions, combine them with a source operation, verify the child, and permit promotion.

Track whether recombinant children are subsequently reused.

### Phase 5 — frozen learned ISA, tasks 5,501–6,000
Freeze the capability archive: no new promotion. Evaluate new held-out compositions using the learned instructions.

This directly tests whether the acquired ISA transfers after learning stops.

## Capability granularity

Capabilities are exact verified output-bit consequences.

A promoted output bit becomes a unit-cost CAP leaf in future tasks.

Promotion criterion:

1. exact verification succeeds;
2. expanded TREE cost of that output bit is at least 5 primitive D executions;
3. no existing capability has identical protected semantics.

Semantic equality is exact in this finite universe.

## Execution arms

### TREE
Fully expanded D expression tree. No sharing.

### LOCAL_DAG
Task-local syntax hash-consing. No cross-task persistence.

### SYNTAX_ISA
Persistent capability reuse only when canonical D syntax matches exactly.

### DEVELOPMENTAL_ISA
Persistent reuse by exact verified protected semantics.

The DEVELOPMENTAL archive is the candidate learned ISA.

## Primary cost model

- primitive D execution = 1
- CAP invocation = 1
- leaves = 0
- VERIFY = counted separately
- PROMOTE bookkeeping = counted separately

Report execution cost and total cost including authority/promotion.

The causal baseline for learned-ISA value is LOCAL_DAG, not TREE.

## Controls

- COLD_ISA: clear persistent capabilities before every task, therefore equivalent to LOCAL_DAG execution.
- NO_PROMOTION: verify but never install capabilities.
- SYNTAX_ISA: persistent syntax-only reuse.
- NO_WARRANT: install zero capabilities.
- NO_RECOMBINATION: Phase-4 children verify but cannot become capabilities.
- ABLATE_TOP32: before Phase 5 remove the 32 most reused capabilities and measure held-out cost increase.
- RANDOM32: replace those 32 ablated capabilities with 32 equally old but low-reuse capabilities; this controls for archive size rather than utility.

## Exact correctness

For all 6,000 tasks:

[
TREE = LOCAL_DAG = SYNTAX_ISA = DEVELOPMENTAL_ISA = 	ext{external exact target}.
]

Zero wrong answers allowed.

A sealed corrupted-target probe must be rejected.

## Frozen gates

F1. All 16 binary Boolean relations are derivable from D+GROUND.

F2. All listed 8-bit source operators pass exhaustive exact verification on all 65,536 input pairs for the direct base-input instances.

F3. Zero semantic disagreements across 6,000 tasks.

F4. DEVELOPMENTAL execution cost < 25% of LOCAL_DAG over the full stream.

F5. DEVELOPMENTAL total cost including VERIFY+PROMOTE < 40% of LOCAL_DAG execution cost.

F6. DEVELOPMENTAL execution cost < 50% of SYNTAX_ISA in the semantic-twin phase.

F7. Mean DEVELOPMENTAL execution cost over the final 500 frozen-ISA tasks < 50% of the first 500 curriculum tasks.

F8. At least 90% of Phase-5 tasks invoke a learned capability.

F9. COLD_ISA execution cost is at least 4x DEVELOPMENTAL execution cost over the full stream.

F10. NO_PROMOTION execution cost is at least 4x DEVELOPMENTAL execution cost over the full stream.

F11. NO_WARRANT installs zero capabilities.

F12. Corrupted target is rejected.

F13. At least 100 recombinant Phase-4 capabilities are reused by later tasks.

F14. NO_RECOMBINATION Phase-4+5 cost is strictly higher than DEVELOPMENTAL Phase-4+5 cost.

F15. ABLATE_TOP32 raises Phase-5 execution cost by at least 20%.

F16. RANDOM32 recovers less than half of the ABLATE_TOP32 cost increase.

F17. No duplicate protected semantics exist in the capability archive.

F18. Deterministic replay from empty state yields identical ledger hash and cost vector.

## Outputs

Record:

- derived formula/cost for all 16 Boolean relations;
- exact verification summaries for each 8-bit source operator;
- per-phase costs for TREE/LOCAL_DAG/SYNTAX_ISA/DEVELOPMENTAL;
- authority and promotion overhead;
- capability count;
- semantic and syntax reuse hits;
- learned-ISA hit rate;
- most reused capabilities;
- ancestry depth;
- recombinant children and reuse;
- frozen-ISA held-out cost;
- top-32 ablation and random-32 control;
- deterministic ledger SHA-256;
- F1–F18.

## Verdicts

- PASS_DEVELOPMENTAL_IR_V2_ALU_ISA
- PARTIAL_DEVELOPMENTAL_IR_V2_ALU_ISA
- VALID_NEGATIVE_DEVELOPMENTAL_IR_V2_ALU_ISA

PASS requires F1–F18.

## Claim boundary

A PASS would establish only that, in an exact finite two-word 8-bit arithmetic universe under the frozen abstract D-operation cost model:

- D+GROUND can host a nontrivial arithmetic source language;
- verified semantic capabilities can form a learned reusable instruction set;
- that instruction set can reduce exact execution cost beyond task-local DAG and syntax-only caching;
- learned instructions transfer to a frozen held-out phase;
- highly reused acquired instructions are causally useful under ablation.

It would not establish faster real wall-clock execution than production CPUs/LLVM, Turing universality, or general natural-world intelligence.
