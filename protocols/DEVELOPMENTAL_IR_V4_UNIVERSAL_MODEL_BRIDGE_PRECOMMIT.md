# DEVELOPMENTAL IR V4 — UNIVERSAL MODEL BRIDGE — prospective precommit

Status: **FROZEN BEFORE IMPLEMENTATION OR OUTCOME EXECUTION**

## Governing question

[
oxed{	extbf{Can the same one-anchor directed-difference nucleus exactly host a known universal computational model, while closing the remaining V3 branch separator?}}
]

V3 produced exact state, RAM, bounded loops, and data-dependent PC semantics, with 19/20 frozen gates passing. Its only failed gate was a non-discriminating branch separator whose two arms happened to agree on the branch-taking lanes.

V4 preserves V3's result unchanged and performs two new prospective tests:

1. a corrected causal branch separator;
2. an exact bridge from D+GROUND to elementary cellular automata, including Rule 110.

Rule 110 is used because its universality is an external established result. V4 does **not** attempt to re-prove Rule 110 universality. It tests whether our nucleus can exactly instantiate the local rule and arbitrary finite bounded evolutions without adding a new trusted primitive.

## Kernel

Unchanged:

- GROUND = 1
- INPUT
- (D(a,b)=
eg aland b)
- VERIFY
- PROMOTE

No cellular-automaton rule, branch, tape operation, neighborhood operator, or universal-machine primitive is trusted.

## Part A — corrected branch separator

Use a frozen branch program over the V3 VM:

- R2 := R0
- R2 := R2 AND 1
- if R2 == 0 jump to EVEN
- R0 := R0 XOR R1
- jump DONE
- EVEN: R0 := R0 + 1
- DONE: HALT

The separator mutation replaces the conditional JZ with unconditional fallthrough to the XOR arm.

Required:

- original program exact against independent host semantics over all 65,536 A,B pairs;
- all lanes halt;
- mutated program differs on at least one protected R0 consequence.

This closes the causal branch question without altering V3.

## Part B — exhaustive three-input D algebra

Let p,q,r be independent Boolean inputs.

Exhaustively compute the minimum D+GROUND expression cost for all

[
2^{2^3}=256
]

three-input Boolean functions.

No rule is selected during synthesis.

For each of the 256 functions record:

- exact truth table in row order 000,001,...,111;
- minimum D count;
- one canonical minimum-cost D expression.

Gate U1 requires all 256 functions to be reachable.

## Part C — identify Rule 110

Using Wolfram elementary cellular-automaton numbering, Rule 110 has output bits

[
(000,ldots,111) = 0,1,1,1,0,1,1,0.
]

Equivalently:

[
R_{110}(p,q,r)=
eg(pland qland r)land(qlor r).
]

V4 must identify the corresponding synthesized D+GROUND expression from the exhaustive 256-function table.

The expression is then externally verified on all eight neighborhoods.

No hand-written shortcut may replace the synthesized expression for the scientific result.

## Part D — parametric capability promotion

After the eight-row verifier accepts the synthesized Rule-110 expression, promote it as a **parametric verified capability**:

[
operatorname{R110}(x,y,z)
]

whose implementation is the certified D+GROUND expression.

This differs from earlier extensional capability promotion: the capability is a verified three-argument operator schema, reusable on novel cell values and at novel positions.

Promotion is lawful here because the exact eight-row truth table proves the operator for every possible Boolean argument triple.

The parametric capability invocation cost is one abstract instruction.

## Part E — exact bounded Rule-110 evolution

For ring widths:

[
5, 7, 11, 16
]

represent **every possible initial configuration simultaneously**.

Thus each width w has (2^w) exact lanes.

For each width:

- simulate 64 Rule-110 time steps with the synthesized D expression;
- independently simulate 64 steps with a direct host-side Rule-110 evaluator;
- compare every cell at every step;
- require zero disagreement.

The width-16 run therefore covers all 65,536 possible 16-cell initial states.

Ring boundary conditions are used only for the bounded experiment. They are not part of the external universality claim.

## Part F — constructor transfer / efficiency

For the width-16, 64-step evolution compare:

### EXPANDED_DAG
Hash-consed unrolled D+GROUND circuit using the synthesized Rule-110 expression at every cell update.

### PARAMETRIC_R110
Each certified local update is one R110 capability invocation.

There are exactly:

[
16	imes64=1024
]

local updates.

Record:

- exact expanded D DAG node count;
- exact parametric capability invocation count;
- verifier and promotion overhead;
- ratio.

### ABLATE_R110
Remove the promoted parametric capability and require execution to return to the expanded D implementation.

This tests causal value of the acquired constructor.

## Part G — all elementary CA rules

Treat every one of the 256 synthesized three-input functions as an elementary binary radius-1 CA local rule.

This does not assert that all are universal.

It establishes that the same nucleus can instantiate the entire elementary-CA local-rule space, one member of which is externally known to be universal.

## Frozen gates

U1. All 256 three-input Boolean functions are derived from D+GROUND.

U2. Every synthesized canonical expression exactly matches its eight-row truth table.

U3. Corrected branch program matches independent VM semantics on all 65,536 input pairs.

U4. Corrected branch program halts on all lanes.

U5. Branch-separator mutation changes at least one protected R0 consequence.

U6. Rule 110 is found in the exhaustive table without special synthesis.

U7. Synthesized Rule-110 expression matches all eight neighborhoods exactly.

U8. Parametric R110 promotion occurs only after U7 verification.

U9. Width-5 64-step evolution is exact on all 32 initial states.

U10. Width-7 64-step evolution is exact on all 128 initial states.

U11. Width-11 64-step evolution is exact on all 2,048 initial states.

U12. Width-16 64-step evolution is exact on all 65,536 initial states.

U13. Zero cell-time disagreements across all four widths.

U14. PARAMETRIC_R110 execution cost <= 25% of EXPANDED_DAG on width 16.

U15. Including one VERIFY and one PROMOTE unit, PARAMETRIC_R110 total cost <= 30% of EXPANDED_DAG.

U16. ABLATE_R110 restores the expanded-D cost path.

U17. The width-independent promoted R110 operator is reused on every one of the 1,024 width-16 cell updates.

U18. The exhaustive 256-rule table contains exactly 256 unique local consequences.

U19. Deterministic replay reproduces the same 256-rule canonical table hash and Rule-110 evolution hash.

U20. No claim of unbounded universality is emitted by the experiment result; the result labels the bridge as bounded and cites Rule 110 universality as external theory.

## Verdicts

- PASS_DEVELOPMENTAL_IR_V4_UNIVERSAL_MODEL_BRIDGE
- PARTIAL_DEVELOPMENTAL_IR_V4_UNIVERSAL_MODEL_BRIDGE
- VALID_NEGATIVE_DEVELOPMENTAL_IR_V4_UNIVERSAL_MODEL_BRIDGE

PASS requires U1-U20.

## Claim boundary

A PASS would establish:

- exact causal branch semantics in the repaired V3 separator;
- exhaustive derivability of all 256 elementary binary radius-1 local rules from D+GROUND;
- exact derivation and bounded execution of Rule 110 from the same nucleus;
- exact transfer of a verified parametric local-rule capability across unseen positions, times, and tested widths;
- a bounded executable bridge into a computational model whose unbounded version is externally known to be universal.

It would **not** itself prove:

- that the finite ring experiments are universal;
- an unbounded tape or unbounded time implementation;
- Turing universality of the current finite runtime by experiment alone;
- superiority in wall-clock speed to optimized cellular-automaton or machine-code implementations.
