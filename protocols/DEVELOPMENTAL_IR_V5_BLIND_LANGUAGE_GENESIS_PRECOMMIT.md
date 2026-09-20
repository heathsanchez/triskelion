# DEVELOPMENTAL IR V5 — BLIND LANGUAGE GENESIS — prospective precommit

Status: **FROZEN BEFORE IMPLEMENTATION OR OUTCOME EXECUTION**

## Governing question

[
oxed{	extbf{Can the developmental nucleus discover and grow its own useful parametric instruction language from repeated verified structure, without being told which higher-level operators to install?}}
]

V4 established an exact bridge from D+GROUND to all 256 three-input Boolean functions and a bounded execution of Rule 110, including verified parametric capability promotion. V5 removes the hand-selection step.

The learner is not given operator names such as AND, XOR, ADD, Rule 110, branch, RAM, or any preferred macro list.

It receives only:

- primitive D+GROUND expressions,
- exact protected task consequences,
- an external verifier,
- occurrence history,
- the right to promote a verified repeated parametric schema.

The test is whether a useful instruction set emerges from workload structure itself.

## Kernel

Trusted primitives remain:

- GROUND = 1
- INPUT
- (D(a,b)=
eg aland b)
- VERIFY
- PROMOTE

No learned macro is primitive.

## Exact semantic universes

### Macro universe

Candidate parametric schemas have arity 3.

There are exactly

[
2^{2^3}=256
]

possible three-input Boolean consequences.

As in V4, the exact minimum D+GROUND expression for all 256 functions is computed exhaustively before the workload begins.

### Task universe

Tasks have four independent Boolean inputs:

[
x_0,x_1,x_2,x_3.
]

Each task is an expression tree whose internal nodes are hidden three-argument Boolean operators and whose leaves are the four inputs.

Task denotations are therefore exact 16-row truth tables.

## Blind hidden operator ecology

Create a latent pool of 64 distinct three-input operators.

The pool is selected only by this frozen deterministic procedure:

1. for slot (i=0,1,ldots), compute SHA256("DIR-V5-LATENT"|i);
2. map the first 16 hex digits modulo 256;
3. admit the rule if not already present;
4. continue until 64 distinct rules exist.

No rule number may be manually inserted, removed, promoted, or weighted after inspection.

The 64 latent operators receive Zipf-like hidden frequencies by their **latent slot rank**, not by rule identity:

[
w_i = rac{1}{(i+1)^{1.15}}.
]

Thus the workload contains frequent and rare recurring schemas, but which actual Boolean rules occupy those ranks is sealed by the precommitted hash construction.

The learner does not receive latent rule IDs or ranks.

## Workload

Generate 12,000 deterministic four-input tasks.

Every task has depth 2–5 and uses only latent operators, but the learner receives only the fully expanded D+GROUND tree.

### Phase 1 — acquisition, tasks 1–8,000

- tree shape and leaves chosen from a frozen deterministic SHA256 stream;
- internal hidden operators sampled from the latent Zipf distribution;
- fully expand every hidden operator into its canonical minimum D expression;
- present only the expanded D expression and exact 16-row protected consequence to the learner.

The learner must recover repeated parametric schemas by abstraction over D subtrees.

### Phase 2 — frozen transfer, tasks 8,001–10,000

Freeze the learned macro archive. No new promotions.

Generate new trees from the same latent ecology using unseen task seeds and different argument placements.

### Phase 3 — structural shift, tasks 10,001–12,000

Archive remains frozen.

Use the same latent operator ecology but alter tree-shape distribution:

- acquisition favors roughly balanced trees;
- shift phase favors left-deep / right-deep compositions and repeated-variable arguments.

This tests whether learned operator schemas transfer independently of original syntax context.

## Blind schema recovery

For each expanded internal operator subtree, recover its three-input abstract consequence by:

1. replace its three actual argument roots by abstract placeholders p,q,r;
2. evaluate the D+GROUND subtree on all eight p,q,r rows;
3. use the resulting exact 8-bit truth table as the schema identity.

The learner therefore infers:

[
	ext{expanded repeated structure}
ightarrow
	ext{abstract parametric consequence}.
]

It is forbidden to read hidden generator rule IDs when deciding promotion or execution.

## Verification

Before promotion of schema (f):

- compare the recovered candidate to its exact eight-row consequence;
- independently evaluate the canonical D expression;
- require equality on all eight rows.

Only then may:

[
f(p,q,r)
]

become a parametric unit-cost instruction.

A sealed corrupted candidate must be rejected.

## Promotion policy

For an unpromoted schema of minimum D cost (c_f), maintain encounter count (n_f).

A schema becomes eligible when:

[
n_f ge 3
]

and

[
n_fmax(c_f-1,0) ge 6.
]

On first eligibility:

- VERIFY cost = 1
- PROMOTE cost = 1
- if verification succeeds, install the parametric macro.

No future frequency, held-out data, rule name, or semantic interpretation may influence promotion.

## Execution cost model

For each task internal node with schema f:

### EXPANDED_D
cost = canonical minimum D cost (c_f).

### BLIND_LEARNED
- before promotion: (c_f)
- after promotion: 1

Costs sum over internal operator occurrences.

Leaves cost 0.

VERIFY and PROMOTE are counted separately.

This is an exact frozen abstract instruction-count model for the task representation. It is not a wall-clock compiler benchmark.

## Controls

### COLD
No persistent learned macros. Cost equals EXPANDED_D.

### RANDOM_K
At the end of acquisition, let K be the number of blindly learned macros.

Choose K distinct latent operators by deterministic SHA256("DIR-V5-RANDOM"|j) selection, without using frequency or utility.

Evaluate Phase 2+3 with those K unit-cost macros.

### ORACLE_TRAIN_K
Using acquisition frequencies only, choose the K latent operators with highest realized training savings:

[
operatorname{count}_{train}(f)max(c_f-1,0).
]

No held-out frequencies may be used.

This is an upper comparison for a same-size instruction set with full hindsight over training.

### ABLATE_TOP8
From the learned archive, remove the eight learned macros with highest actual Phase-2+3 reuse count.

### LOW8
Remove eight learned macros with lowest Phase-2+3 reuse count.

### NO_WARRANT
Candidate schemas are observed but none may be installed.

### CORRUPTED
Flip one truth-table bit of the first eligible schema. Verification must reject it.

## Portability / regeneration test

Serialize the learned language as only:

- schema truth table;
- canonical D+GROUND expression;
- verifier digest;
- acquisition task index.

Then clear all learner runtime state.

Reload only this serialized capability language, independently reverify every macro from its D expression, and rerun Phase 2+3.

The reloaded archive must reproduce:

- identical held-out execution cost;
- identical outputs;
- identical learned-language hash.

This tests whether the acquired language is a portable verified developmental artifact rather than hidden runtime state.

## Frozen gates

L1. All 256 three-input functions remain exactly derivable from D+GROUND.

L2. All 12,000 task protected consequences exactly match independent direct hidden-operator evaluation.

L3. Blind schema recovery matches the hidden operator consequence for every internal node.

L4. Every installed macro was admitted only after exact eight-row verification.

L5. Sealed corrupted first-eligible macro is rejected.

L6. At least 8 macros are learned during acquisition.

L7. Fewer than all 64 latent operators are learned during acquisition.

L8. BLIND_LEARNED acquisition execution cost < 60% of EXPANDED_D acquisition cost.

L9. Including VERIFY+PROMOTE, acquisition total cost < 65% of EXPANDED_D acquisition cost.

L10. Frozen Phase-2 BLIND_LEARNED cost < 45% of COLD Phase-2 cost.

L11. Structural-shift Phase-3 BLIND_LEARNED cost < 50% of COLD Phase-3 cost.

L12. At least 95% of Phase-2 tasks invoke at least one learned macro.

L13. At least 90% of Phase-3 tasks invoke at least one learned macro.

L14. BLIND_LEARNED Phase-2+3 cost <= 115% of ORACLE_TRAIN_K cost.

L15. RANDOM_K Phase-2+3 cost is at least 20% higher than BLIND_LEARNED.

L16. ABLATE_TOP8 raises Phase-2+3 cost by at least 15%.

L17. LOW8 raises Phase-2+3 cost by less than half the TOP8 increase.

L18. NO_WARRANT installs zero macros.

L19. Portable reload reproduces identical Phase-2+3 execution cost and outputs.

L20. Portable reload reproduces identical learned-language hash after independent re-verification.

L21. Learned archive contains no duplicate schema consequences.

L22. Deterministic full replay produces identical workload hash, promotion trace hash, learned-language hash, and cost vector hash.

L23. At least one learned macro is reused with all three arguments instantiated by different nontrivial subexpressions than at its first promotion site.

L24. No gate depends on post-hoc human naming or semantic interpretation of any learned macro.

## Outputs

Record:

- latent 64-rule pool and sealed frequency ranks, revealed only in result;
- learned macro set and promotion task indices;
- canonical D expression and minimum D cost for every learned macro;
- acquisition / transfer / shift costs;
- promotion and verification overhead;
- learned K;
- oracle same-K comparison;
- random same-K comparison;
- hit rates;
- top-8 and low-8 ablation results;
- portability / regeneration hashes;
- post-hoc human-readable identification of learned macros where obvious, clearly marked as analysis only;
- L1-L24.

## Verdicts

- PASS_DEVELOPMENTAL_IR_V5_BLIND_LANGUAGE_GENESIS
- PARTIAL_DEVELOPMENTAL_IR_V5_BLIND_LANGUAGE_GENESIS
- VALID_NEGATIVE_DEVELOPMENTAL_IR_V5_BLIND_LANGUAGE_GENESIS

PASS requires L1-L24.

## Claim boundary

A PASS would establish only that, in this exact finite four-input Boolean workload:

- a D+GROUND system can infer recurring parametric operator schemas from expanded verified structure;
- it can select and promote a useful instruction language using only past occurrence and exact warrant;
- the learned language transfers to unseen syntax contexts and a shifted tree distribution;
- its value is causal under matched random and ablation controls;
- the language can be serialized, independently reverified, reloaded, and reproduce held-out execution.

It would **not** establish autonomous discovery of arbitrary mathematics, arbitrary programming abstractions, open-ended intelligence, self-hosting compilation, or general-purpose program synthesis.

The scientific purpose is narrower and decisive:

[
oxed{	extbf{Can useful language form itself from verified experience?}}
]
