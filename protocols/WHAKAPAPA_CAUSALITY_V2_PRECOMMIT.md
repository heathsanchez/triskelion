# WHAKAPAPA CAUSALITY V2 — admissible-world / causally-distinct-sham precommit

Status: **FROZEN BEFORE V2 IMPLEMENTATION OR OUTCOME EXECUTION**

## Why V2 exists

V1 remains intact.

Its non-authoritative deterministic preflight exposed two apparatus limitations:

1. some frozen seeds exhaust the complete finite relation family before the preregistered exact-parent lineage topology can be instantiated;
2. a false acyclic ancestry can sometimes preserve the exact tested descendant cone, making the revocation probe unable to distinguish true from false ancestry.

V2 changes only those apparatus points. It does not alter the nucleus, lineage topology, ancestry arms, causal tasks, budgets, five world adapters, or scientific interpretation.

## Scientific question

On worlds where the preregistered branching/recombining lineage **exists**, does the same imported D/M/I nucleus generate it, and does retaining the true verified ancestry causally improve later development relative to identical capability contents with flat, severed, or causally-distinct false ancestry?

## Frozen nucleus and worlds

Import the same D/M/I implementation from:

`experiments/cross_world_nucleus_invariance_v1.py`

Use the same five world adapters:

- binary;
- ternary;
- symbolic;
- temporal;
- graph-observation.

Candidate nuclei remain:

- NONE
- D
- M
- I
- DM
- DI
- MI
- DMI
- DMI_COLD
- ORACLE_STACK

No V2 world-specific operator may appear inside nucleus code.

## Frozen lineage topology

Exactly the V1 eight-node topology:

[
G1ightarrow G2
]

[
G2ightarrow L3ightarrow L4
]

[
G2ightarrow R3ightarrow R4
]

[
(L4,R4)ightarrow X5ightarrow X6.
]

At most one new child is integrated per episode.

## V2 admissible-world sampler

For each frozen **base seed**, the evaluator examines deterministic candidate world seeds in this exact order:

[
	exttt{<BASE>:WORLD:000},ldots,	exttt{<BASE>:WORLD:255}.
]

For each candidate seed, run the unchanged V1 world constructor.

The selected world is the **first** candidate for which the complete lineage plus frozen F1/F2 future targets are constructible under all V1 exact-parent admissibility rules.

Important:

- selection is based only on world-construction existence;
- no nucleus arm, ancestry arm, cost, causal result, or future experimental verdict is evaluated before the candidate world is selected;
- the number of rejected candidate worlds is recorded;
- no selected world may be replaced after any scientific arm is executed;
- failure to find an admissible world within 256 candidates is a valid V2 world-construction failure and counts against the fixed denominator.

This conditions the experiment on the existence of the object being tested rather than treating nonexistence of the synthetic target topology as nucleus failure.

## Generated ancestry

As in V1, DMI's retained dependencies must be the parent identities actually selected by the generic differentiation/mediation process at integration time.

No evaluator-only hidden edge may be copied into the generated graph after the fact.

## Capability freeze

After DMI succeeds, freeze exactly the same executable capability contents for all ancestry arms.

Relational ancestry is the only experimental variable.

## Ancestry arms

Unchanged:

- TRUE_MIN
- FULL_CLOSURE
- FLAT
- SEVERED
- SHAM_V2
- RECONSTRUCT
- COLD

## Causally-distinct SHAM_V2

SHAM_V2 must satisfy all of the following before any causal task is run:

1. same node set as TRUE_MIN;
2. same incoming-edge count for every non-root capability node;
3. topologically legal / acyclic;
4. not equal to TRUE_MIN;
5. generated deterministically from the frozen world seed;
6. for the frozen revocation anchor, its descendant cone differs from TRUE_MIN.

The revocation anchor is selected **before task evaluation** as the first node in this frozen order:

[
G2, L3, R3, L4, R4
]

whose TRUE_MIN descendant cone is nonempty and for which a topologically legal same-in-degree SHAM candidate can be found with a different descendant cone.

Search candidate sham graphs in SHA-256 order over the finite topologically legal parent-set choices.

If no such sham exists, the world is marked SHAM-unidentifiable and counts against the SHAM-specific threshold; no graph may be hand-edited.

The anchor and both true/sham descendant cones are persisted before T1–T4 outcomes.

## Frozen causal tasks

Exactly the V1 tasks.

### T1 Future discovery
Generate F1 from a current true lineage tip plus one primitive feature.

TRUE_MIN searches tip×primitive pairs first.

FLAT searches all capability×primitive pairs in stable order.

### T2 Recombination
Use the V1 pre-recombination cut; L4/R4 are the intended branch-frontier parents.

Budget: 8 pair checks.

### T3 Selective revocation
Invalidate the V2-selected revocation anchor.

TRUE_MIN uses the true descendant cone.

FLAT must conservatively requalify all inherited capabilities to remain safe.

SHAM_V2 uses its false descendant cone first, then undergoes exact external safety audit.

Record unsafe omissions and repair work.

### T4 Regeneration
Delete L3 executable form while retaining its verified extensional certificate.

Budget: 12 parent-subset checks.

TRUE_MIN may use its direct parents.

FLAT must search from contents.

## Minimum ancestry

TRUE_MIN vs FULL_CLOSURE remains unchanged.

Required comparison:

- same T1–T4 correctness class;
- TRUE_MIN uses strictly fewer stored relational edges.

## Reconstruction

RECONSTRUCT starts from FLAT and may recover parentage only by generic finite-function search over already frozen node contents.

Record exact recovery and search cost.

## Representation metamorphism

Binary, ternary, symbolic, and temporal headline worlds are value-relabeled bijectively exactly as in V1.

The same selected admissible scenario is relabeled; the world sampler is **not rerun** after relabeling.

Required invariant signature is unchanged.

## Seeds

Headline base seeds:

- `TRISKELION_WHAKAPAPA_V2_BINARY`
- `TRISKELION_WHAKAPAPA_V2_TERNARY`
- `TRISKELION_WHAKAPAPA_V2_SYMBOLIC`
- `TRISKELION_WHAKAPAPA_V2_TEMPORAL`
- `TRISKELION_WHAKAPAPA_V2_GRAPH`

Sweep base seeds:

`<HEADLINE_BASE>:SWEEP:000` through `:024`.

For each base seed apply the fixed `:WORLD:000..255` admissible-world sampler.

Total frozen scientific denominator: **125 selected-world attempts**.

## Headline nucleus gates

N1 same imported nucleus source in all worlds.
N2 an admissible world is selected in every headline world.
N3 DMI reaches all 8 nodes in every headline world.
N4 generated DMI DAG exactly equals hidden DAG in every headline world.
N5 DMI_COLD does not reach 8 in any headline world.
N6 removing I reduces reach in every headline world.
N7 removing M reduces reach in every headline world.
N8 removing D either reduces reach or strictly increases verifier-candidate work in every headline world.
N9 no proper tested subset matches DMI on full reach + exact generated ancestry + typed work in all headline worlds.

## Headline whakapapa gates

W1 TRUE_MIN succeeds safely on T1–T4 in all headline worlds.
W2 TRUE_MIN T1 uses fewer parent checks than FLAT in every headline world.
W3 TRUE_MIN T2 succeeds within budget and beats FLAT reach or checks in every headline world.
W4 TRUE_MIN performs exact safe selective revocation at the frozen V2 anchor.
W5 SHAM_V2 is identified in every headline world and either leaves unsafe descendants before repair or requires strictly more total requalification work than TRUE_MIN.
W6 TRUE_MIN regenerates L3 within budget with fewer checks than FLAT.
W7 TRUE_MIN and FULL_CLOSURE are correctness-equivalent while TRUE_MIN stores fewer edges.
W8 RECONSTRUCT performs strictly positive ancestry-recovery work.
W9 representation metamorphism preserves the frozen signature in W1–W4 worlds.
W10 non-cold ancestry arms receive identical capability contents.

## Sweep thresholds

### Nucleus
- admissible world selected: at least 124/125;
- DMI full 8-node lineage: at least 120/125;
- exact generated DAG: at least 120/125;
- DMI_COLD full lineage: at most 5/125;
- DM reach loss: at least 115/125;
- DI reach loss: at least 115/125;
- MI reach loss or higher verifier-candidate work: at least 115/125.

### Whakapapa
- TRUE_MIN T1 success: at least 120/125;
- TRUE_MIN T1 cheaper than FLAT: at least 115/125;
- TRUE_MIN T2 success: at least 115/125;
- TRUE_MIN exact safe revocation: at least 120/125;
- SHAM_V2 identifiable and unsafe-or-more-expensive: at least 115/125;
- TRUE_MIN T4 regeneration success: at least 120/125;
- TRUE_MIN T4 cheaper than FLAT: at least 115/125;
- TRUE_MIN/FULL_CLOSURE correctness equivalence: at least 120/125.

## Verdicts

- `PASS_WHAKAPAPA_CAUSALITY_AND_BOUNDED_IRREDUCIBLE_NUCLEUS_V2`
- `PASS_WHAKAPAPA_CAUSALITY_REDUCED_NUCLEUS_V2`
- `NUCLEUS_PASS_WHAKAPAPA_NEGATIVE_V2`
- `WHAKAPAPA_PASS_NUCLEUS_PARTIAL_V2`
- `PARTIAL_WHAKAPAPA_CAUSALITY_V2`
- `VALID_NEGATIVE_WHAKAPAPA_CAUSALITY_V2`

"Bounded irreducible nucleus" means only: no tested proper D/M/I subset matches the full nucleus under these five finite adapters, frozen worlds, causal gates, and resource accounting.

## Claim boundary

A full V2 pass would support a bounded cross-world causal claim that true generated ancestry is developmental capital and that the tested D/M/I nucleus is irreducible under the preregistered finite experimental family.

It would **not** establish metaphysical inevitability, unique minimality among all possible developmental algorithms, unrestricted intelligence, biological identity with genetic inheritance, or the full cultural meaning of whakapapa.
