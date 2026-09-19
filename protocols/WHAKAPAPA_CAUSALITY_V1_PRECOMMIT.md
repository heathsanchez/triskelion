# WHAKAPAPA CAUSALITY V1 — prospective precommit

Status: **FROZEN BEFORE OUTCOME IMPLEMENTATION OR EXECUTION**

## Question

Does verified developmental ancestry carry causal value beyond possession of the same capabilities, and does that ancestry fall out of the same candidate nucleus rather than requiring a separate hand-designed stack?

This experiment tests two linked hypotheses:

1. **Nucleus hypothesis** — the same three developmental roles
   [
   N={	extbf{Differentiate},	extbf{Mediate},	extbf{Integrate}}
   ]
   generate a branching, recombining capability lineage across source-distinct finite worlds.
2. **Whakapapa hypothesis** — once the executable capability contents are held fixed, retaining their true verified parent/dependency relationships improves future development, selective revocation, regeneration, and recombination relative to flat, severed, or sham ancestry.

The word *whakapapa* is used here in the limited engineering sense of verified relational ancestry/dependency. This experiment does not claim to exhaust or redefine the cultural meaning of whakapapa.

## Scientific order

The protocol is frozen before outcome code.

The experiment must not rescue a favored triad. If a proper subset of D/M/I repeatedly matches the full nucleus, the correct outcome is a reduced-nucleus verdict. If true ancestry adds no value once capability contents are fixed, the correct outcome is a negative whakapapa result.

## Inherited frozen nucleus

The implementation must import the generic D/M/I functions from:

`experiments/cross_world_nucleus_invariance_v1.py`

The nucleus source itself may not be modified on this branch.

### D — Differentiate
Find a minimum sufficient parent set under the generic exact finite-function criterion.

### M — Mediate
Compile the exact finite relation induced between selected parents and the externally verified target.

### I — Integrate
Install the verified child with exact semantics, parent dependencies, provenance, and revocation lineage.

External exact authority remains outside the nucleus. OPEN evidence cannot promote structure.

## Cross-world basis

Run the same experiment over the five frozen adapters inherited from CROSS-WORLD NUCLEUS INVARIANCE V1:

- binary Cartesian;
- ternary Cartesian;
- symbolic string;
- temporal history;
- graph-observation.

No world-specific operator, graph rule, temporal rule, Boolean connective, arithmetic formula, or string rule may appear in nucleus code.

## Branching lineage world

Each episode builds a directed acyclic developmental lineage rather than a single chain.

Frozen topology:

[
G1 ightarrow G2
]

then two source-distinct branches:

[
G2ightarrow L3ightarrow L4
]
[
G2ightarrow R3ightarrow R4
]

then recombination:

[
(L4,R4)ightarrow X5ightarrow X6.
]

Thus the final developmental object has shared ancestry, branching, and a two-parent recombination event.

Every hidden relation is generated mechanically by the same hash-driven finite relation generator used by the cross-world experiment, subject only to frozen admissibility:

1. target is novel at episode start;
2. declared parents are both essential;
3. no smaller active parent set is sufficient;
4. for non-root generations, at least one minimum sufficient set contains the declared inherited parent(s);
5. output stays inside the world alphabet.

The generator may advance to the next hash counter only when one of those preregistered structural conditions fails.

## Candidate nuclei

The lineage must be attempted under every candidate subset:

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

All arms receive identical world, target order, authority, and per-episode resource boundaries.

A full nucleus is **not** declared necessary merely because DMI has the highest reach. Any proper subset that achieves equal lineage reach with equal causal criteria and no higher verifier-candidate work counts against irreducibility.

## Generated ancestry requirement

For DMI, the retained parent edges must be exactly the parent identities selected by the generic differentiation/mediation process at integration time.

No lineage edge may be injected after the fact from the hidden world generator.

The experiment records two graphs:

- **hidden construction DAG** — evaluator-only ground truth;
- **generated verified DAG** — edges emitted by DMI integration.

Graph equality is evaluated only after the lineage is sealed.

## Capability freeze

After a successful DMI lineage is generated, freeze the exact executable capability node contents:

[
C={G1,G2,L3,L4,R3,R4,X5,X6}.
]

Every ancestry arm below receives exactly the same frozen node contents and external verifier. Only relational ancestry differs.

## Ancestry arms

### TRUE_MIN
The direct verified parent/dependency DAG emitted by DMI.

### FULL_CLOSURE
The same correct ancestry expanded to its full transitive ancestor closure.

This tests whether direct parentage is a minimum sufficient ancestry representation.

### FLAT
Identical capability nodes, no ancestry edges.

### SEVERED
Identical nodes, but one deterministic true incoming edge is removed from every multi-parent/non-root node where possible.

### SHAM
Identical nodes and the same total incoming-edge count per non-root node, but parent identities are deterministically replaced by earlier topologically legal nodes that are not the true parent set.

SHAM must remain acyclic.

### RECONSTRUCT
Starts FLAT. It may infer parent sets from frozen node semantics using the same generic minimum-sufficient finite-function search. Every tested parent subset is charged.

### COLD
No inherited capability nodes.

## Generic lineage operations

The lineage consumer may use only the following graph-generic operations:

- direct parents;
- direct children;
- ancestor closure;
- descendant closure;
- leaves/tips;
- roots.

It may not inspect world-specific labels to route search.

## Four causal tests

### T1 — Future discovery from frontier

After lineage freeze, generate a sealed future child (F1) from one current lineage tip and one primitive feature.

A lineage-aware policy searches candidate (tip, primitive) parent pairs first.

FLAT has no tip relation and therefore searches all active capability/primitive pairs in stable ID order.

All arms receive the same target semantics and exact verifier.

Record parent-subset checks required to find a sufficient pair.

A true-lineage benefit exists only if TRUE_MIN reaches the verified child with fewer checks than FLAT and SHAM on the frozen episode.

### T2 — Recombination

Generate a sealed future child (F2) from two current lineage tips belonging to distinct branches.

TRUE_MIN searches unordered tip pairs.

FLAT searches all unordered capability pairs in stable order.

SHAM/SEVERED derive tips from their own supplied graph and may therefore search the wrong frontier.

Record:
- whether the correct verified child is reached within a fixed 8-pair budget;
- pair checks used.

### T3 — Selective revocation

External authority invalidates G2.

Ground truth requires requalification of exactly the true descendant cone of G2 and preservation of unaffected nodes.

Policy:
- TRUE_MIN and FULL_CLOSURE may use their supplied descendant relation;
- FLAT and RECONSTRUCT must conservatively inspect every inherited nonprimitive capability to remain safe;
- SHAM/SEVERED first use their supplied descendant cone, then undergo an external safety audit.

Required metrics:
- unsafe retained descendants;
- unaffected capabilities unnecessarily requalified;
- total requalification checks.

A lineage arm is safe only if no invalid true descendant remains trusted.

### T4 — Regeneration

Delete the executable implementation of L3 while retaining its verified extensional target certificate.

TRUE_MIN may use L3's supplied direct parents to rebuild it.

FULL_CLOSURE must still choose a minimum direct parent set from its ancestor set.

FLAT/RECONSTRUCT must search active parent subsets from semantics.

SHAM/SEVERED may use their supplied candidate parents but external verification rejects incorrect reconstructions.

Record:
- success within a fixed 12-parent-subset budget;
- verifier checks;
- parent-subset checks.

## Minimum-sufficient ancestry test

TRUE_MIN and FULL_CLOSURE must be equivalent on correctness/reach for T1–T4.

TRUE_MIN must use no more relational edges than FULL_CLOSURE and should use strictly fewer whenever the DAG has a path of length >1.

If FULL_CLOSURE materially outperforms TRUE_MIN under the frozen generic policies, direct parentage is not established as sufficient.

## Reconstruction cost

RECONSTRUCT is scientifically important.

If FLAT can cheaply regenerate the entire true direct-parent DAG from capability contents, then stored ancestry may be useful but not nuclear.

Record:
- exact generated-edge recovery;
- tested parent subsets;
- verifier checks.

The protocol does not require reconstruction to fail. It asks whether retained true ancestry saves future developmental work.

## Representation metamorphism

For binary, ternary, symbolic, and temporal headline worlds, apply the same bijective value relabelling used by CROSS-WORLD NUCLEUS INVARIANCE V1.

Required invariants:

- nucleus lineage reach unchanged;
- generated DAG isomorphic under stable node IDs;
- TRUE_MIN vs FLAT ordering on T1/T4 unchanged;
- T2 success class unchanged;
- T3 safety class unchanged.

The graph world is excluded from this relabelling gate exactly as in the prior protocol.

## Seeds

Headline seeds:

- `TRISKELION_WHAKAPAPA_V1_BINARY`
- `TRISKELION_WHAKAPAPA_V1_TERNARY`
- `TRISKELION_WHAKAPAPA_V1_SYMBOLIC`
- `TRISKELION_WHAKAPAPA_V1_TEMPORAL`
- `TRISKELION_WHAKAPAPA_V1_GRAPH`

Then 25 additional deterministic seeds per world:

`<WORLD_SEED>:SWEEP:000` through `:024`.

Total sweep worlds: 125.

## Headline nucleus gates

N1. Same imported D/M/I source is used in all five worlds.
N2. DMI generates all eight lineage nodes in all five headline worlds.
N3. Generated verified DAG exactly matches hidden construction DAG in all five headline worlds.
N4. DMI_COLD does not generate the full eight-node lineage in any headline world.
N5. Removing I reduces lineage reach in every headline world.
N6. Removing M reduces lineage reach in every headline world.
N7. Removing D either reduces reach or strictly increases verifier-candidate work in every headline world.
N8. No proper subset matches DMI on full lineage reach + generated-DAG correctness + typed cost in all headline worlds.

## Headline whakapapa gates

W1. TRUE_MIN is safe and successful on T1–T4 in all five headline worlds.
W2. TRUE_MIN uses fewer T1 parent checks than FLAT in all five headline worlds.
W3. TRUE_MIN succeeds on T2 within budget in all five headline worlds and beats either FLAT reach or checks.
W4. TRUE_MIN performs exact selective G2 revocation with zero unsafe retained descendants in all five worlds.
W5. SHAM produces either unsafe revocation or strictly greater safety-repair work than TRUE_MIN in all five worlds.
W6. TRUE_MIN regenerates L3 within budget in all five worlds with fewer parent checks than FLAT.
W7. TRUE_MIN and FULL_CLOSURE are correctness-equivalent on T1–T4, while TRUE_MIN uses fewer edges.
W8. RECONSTRUCT, if successful, requires strictly positive reconstruction work in every headline world.
W9. Representation metamorphism preserves the preregistered invariants for W1–W4 worlds.
W10. Capability contents are byte-for-byte/extensional identical across TRUE_MIN, FULL_CLOSURE, FLAT, SEVERED, SHAM, and RECONSTRUCT before T1–T4.

## Sweep criteria

### Nucleus signal
- DMI full eight-node lineage in at least 120/125.
- Generated DAG exact in at least 120/125.
- DMI_COLD full lineage in at most 10/125.
- DM and DI each lose lineage reach in at least 115/125.
- MI either loses reach or uses strictly more verifier-candidate work than DMI in at least 115/125.

### Whakapapa signal
- TRUE_MIN T1 success in at least 120/125 and lower parent-check cost than FLAT in at least 115/125.
- TRUE_MIN T2 success within budget in at least 115/125.
- TRUE_MIN exact safe selective revocation in at least 120/125.
- TRUE_MIN regeneration success in at least 120/125 and lower parent-check cost than FLAT in at least 115/125.
- SHAM is either unsafe or more expensive to repair than TRUE_MIN in at least 115/125.
- TRUE_MIN/FULL_CLOSURE correctness equivalence in at least 120/125.

## Verdicts

- `PASS_WHAKAPAPA_CAUSALITY_AND_IRREDUCIBLE_NUCLEUS_V1`
- `PASS_WHAKAPAPA_CAUSALITY_REDUCED_NUCLEUS_V1`
- `NUCLEUS_PASS_WHAKAPAPA_NEGATIVE_V1`
- `WHAKAPAPA_PASS_NUCLEUS_PARTIAL_V1`
- `PARTIAL_WHAKAPAPA_CAUSALITY_V1`
- `VALID_NEGATIVE_WHAKAPAPA_CAUSALITY_V1`

The phrase **irreducible nucleus** is permitted only within this frozen finite experimental family. The experiment must not use the word "inevitable" as an unrestricted scientific conclusion.

## Claim boundary

A full pass would support the bounded claim that:

1. the same imported D/M/I developmental mechanism generates correct branching/recombining verified ancestry across five materially different finite worlds;
2. correct ancestry itself carries causal developmental value when capability contents are held fixed;
3. direct verified parentage is sufficient relative to full transitive closure under the frozen policies; and
4. no tested proper D/M/I subset matches the full nucleus under the preregistered reach/causal/cost criteria.

It would **not** establish metaphysical inevitability, unique minimality over all possible algorithms, unrestricted open-world intelligence, or that the engineering use of whakapapa captures the full Māori concept.
