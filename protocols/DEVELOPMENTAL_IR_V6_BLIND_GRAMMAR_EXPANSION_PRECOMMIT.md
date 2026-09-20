# DEVELOPMENTAL IR V6 — BLIND GRAMMAR EXPANSION — prospective precommit

Status: **FROZEN BEFORE IMPLEMENTATION OR OUTCOME EXECUTION**

## Governing question

[
oxed{	extbf{Can the system grow the arity and contents of its own verified instruction language only when new workload structure requires it, under a strict finite language budget?}}
]

V5 showed that blind schema recovery and promotion can form a useful portable parametric language, but one frozen task-level hit-rate gate failed because the phase-2 generator permitted leaf-only tasks that could not invoke any macro. V5 remains unchanged.

V6 is stronger rather than a threshold repair:

- every task is guaranteed to contain computation;
- useful operators arrive in epochs of increasing latent arity;
- the learner is not told those operator identities;
- the learned language has a hard budget of 24 instructions;
- it must admit, retain, and evict instructions online using only past verified utility;
- higher-arity operators may enter the language only after the environment actually presents such structure.

## Kernel

Trusted primitives remain only:

- GROUND = 1
- INPUT
- (D(a,b)=
eg aland b)
- VERIFY
- PROMOTE

No 2-, 3-, or 4-argument macro is primitive.

## Hidden operator ecologies

Three deterministic hidden pools are precommitted.

### Arity 2
Select 12 distinct two-input Boolean functions from the 16-function space by SHA256("DIR-V6-A2"|i), deduplicating until 12 are obtained.

Canonical D+GROUND expressions are synthesized exactly.

### Arity 3
Select 32 distinct three-input Boolean functions from the 256-function space by SHA256("DIR-V6-A3"|i), deduplicating until 32 are obtained.

Canonical minimum-D expressions are synthesized exactly.

### Arity 4
Generate 24 distinct four-input operators without enumerating all 65,536 functions.

For candidate index i:

1. select two arity-3 canonical operators by SHA256("DIR-V6-A4-L"|i) and SHA256("DIR-V6-A4-R"|i);
2. instantiate the left operator on ((p,q,r));
3. instantiate the right operator on ((q,r,s));
4. combine the two results with D:
   [
   F_i(p,q,r,s)=D(L_i(p,q,r),R_i(q,r,s));
   ]
5. deduplicate by exact 16-row truth table;
6. continue until 24 distinct four-input operators exist.

No four-input rule is manually inserted or selected by semantic interpretation.

## Workload

10,000 exact four-variable tasks.

Every task root is an internal operator; leaf-only tasks are forbidden.

### Epoch A — tasks 1–2,000
Only hidden arity-2 operators occur.

### Epoch B — tasks 2,001–5,000
Arity-3 operators are introduced and mixed with arity-2 operators.

### Epoch C — tasks 5,001–8,000
Arity-4 operators are introduced and mixed with arity-2 and arity-3 operators.

### Frozen transfer — tasks 8,001–10,000
Freeze the learned language. Generate unseen trees using all three arities with shifted, strongly unbalanced shapes and repeated-variable arguments.

No new promotion or eviction occurs in the frozen phase.

## Blind schema recovery

The learner sees only expanded D+GROUND templates and actual argument subtrees.

For each internal template:

1. abstract its k actual argument roots to placeholders (x_1,ldots,x_k);
2. evaluate the D+GROUND template on all (2^k) rows;
3. identify the schema only by:
   [
   (k,	ext{exact truth table}).
   ]

Hidden generator operator IDs are unavailable to promotion and execution logic.

## Verification and promotion

Before installation, a candidate schema must be exhaustively reverified from its D+GROUND expression on all (2^k) rows.

A corrupted candidate is rejected.

Each schema maintains online:

[
U_f=n_fmax(c_f-1,0)
]

where (n_f) is encounter count and (c_f) expanded D cost.

Eligibility requires:

[
n_fge3,qquad U_fge6.
]

## Hard language budget

At most

[
oxed{24}
]

parametric macros may be installed.

When fewer than 24 are installed, an eligible verified candidate may be admitted.

When the archive is full, an eligible uninstalled candidate may replace the currently installed schema with smallest current (U_f) iff:

[
U_{	ext{candidate}} > U_{	ext{lowest installed}}.
]

Ties retain the existing language.

All replacement decisions use only information available up to that encounter.

Record every admission and eviction.

## Execution costs

For each internal occurrence:

- uninstalled schema: expanded D cost (c_f);
- installed verified schema: 1.

Leaves cost 0.

VERIFY and PROMOTE each cost 1.

EVICT bookkeeping cost is reported separately but not charged to execution.

## Controls

### COLD
No persistent macros.

### ORACLE24
After task 8,000, use only realized tasks 1–8,000 frequencies to choose the 24 schemas with greatest total training saving.

### RANDOM24
Choose 24 distinct encountered schemas from the deterministic SHA256("DIR-V6-RANDOM"|i) stream, independent of frequency and meaning.

### STATIC_A2
Freeze the instruction set after Epoch A; later epochs cannot expand grammar.

### STATIC_A3
Allow Epoch A+B learning, freeze before Epoch C.

These directly test the value of later grammar expansion.

### TOP6 ablation
Remove the six final learned macros with highest frozen-transfer reuse.

### LOW6 ablation
Remove six final learned macros with lowest frozen-transfer reuse.

### NO_WARRANT
Install zero macros.

## Portability

Serialize the final 24-or-fewer macro language using only:

- arity;
- exact truth table;
- D+GROUND expression;
- verifier digest;
- admission event index.

Clear runtime state, independently reverify the language, reload it, and rerun frozen transfer.

## Frozen gates

G1. All hidden arity-2 operator templates are exact D+GROUND expressions.

G2. All hidden arity-3 operator templates are exact D+GROUND expressions.

G3. All 24 hidden arity-4 templates are exact on all 16 rows.

G4. All 10,000 task expanded-D consequences equal independent direct hidden-operator semantics.

G5. Blind recovered ((arity,truth table)) matches the hidden operator consequence for every internal occurrence.

G6. Every installed macro is admitted only after exhaustive verification.

G7. Sealed corrupted candidate is rejected.

G8. Learned language never exceeds 24 installed macros.

G9. At least 4 arity-2 macros are installed by the end of Epoch A.

G10. At least 4 arity-3 macros are installed by the end of Epoch B.

G11. At least 4 arity-4 macros are installed by the end of Epoch C.

G12. No arity-3 macro is installed before the first arity-3 encounter.

G13. No arity-4 macro is installed before the first arity-4 encounter.

G14. Online learned execution cost over tasks 1–8,000 < 50% of COLD cost.

G15. Including VERIFY+PROMOTE, tasks 1–8,000 total < 55% of COLD cost.

G16. Frozen-transfer learned cost < 45% of COLD frozen-transfer cost.

G17. At least 95% of frozen-transfer tasks invoke at least one learned macro.

G18. Learned frozen-transfer cost <= 120% of ORACLE24.

G19. RANDOM24 frozen-transfer cost is at least 20% higher than learned.

G20. STATIC_A2 cost over Epoch B+C+frozen is at least 25% higher than developmental learning.

G21. STATIC_A3 cost over Epoch C+frozen is at least 15% higher than developmental learning.

G22. TOP6 ablation raises frozen-transfer cost by at least 15%.

G23. LOW6 ablation raises frozen-transfer cost by less than half the TOP6 increase.

G24. At least one installed macro is later evicted by a more useful verified macro.

G25. At least one final learned macro of each arity is used with nontrivial computed arguments in frozen transfer.

G26. NO_WARRANT installs zero macros.

G27. Portable reload independently reverifies every final macro.

G28. Portable reload reproduces identical frozen-transfer outputs and cost.

G29. Portable reload reproduces identical final-language hash.

G30. Full deterministic replay reproduces workload, event-trace, language, and cost hashes.

## Verdicts

- PASS_DEVELOPMENTAL_IR_V6_BLIND_GRAMMAR_EXPANSION
- PARTIAL_DEVELOPMENTAL_IR_V6_BLIND_GRAMMAR_EXPANSION
- VALID_NEGATIVE_DEVELOPMENTAL_IR_V6_BLIND_GRAMMAR_EXPANSION

PASS requires G1-G30.

## Claim boundary

A PASS would establish only that, in this exact finite staged Boolean ecology:

- a system starting with D+GROUND can infer useful parametric schemas of increasing arity from expanded structure;
- the grammar can expand only after relevant environmental structure appears;
- under a strict language budget, online verified utility can cause lawful admission and eviction;
- later grammar expansion has causal value against frozen earlier languages;
- the resulting language remains portable and independently re-verifiable.

It would not establish arbitrary grammar invention, natural-language understanding, open-ended evolution, or general self-hosting.

The bounded target is:

[
oxed{	extbf{the language grows because the world demands distinctions the current language compresses poorly.}}
]
