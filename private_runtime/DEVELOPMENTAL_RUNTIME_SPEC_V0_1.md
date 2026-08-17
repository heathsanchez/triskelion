# Metalogic Developmental Runtime Specification v0.1

_Status: private engineering specification._

## 0. Purpose

The runtime implements one narrow falsifiable claim:

> Under matched base model, experience, experience access, tools, verifier and budget, verified experience can cause a persistent causal reorganization that changes protected future cognition or future learning without changing the base-model weights.

The public demo is only the viewport. This document specifies the private machinery underneath it.

## 1. State hierarchy

```text
Base Model
+
Developmental State                  # everything persistent that development changed
  └── Thought Matrix                 # addressable organization mediating cognition
       └── Verified World Map        # warranted subgraph
            └── Active Lens          # current projection into this situation
```

`Developmental State` may include opaque/distributed artifacts. The `Thought Matrix` contains what the runtime can address. The `Verified World Map` contains only externally warranted state. The `Active Lens` is the minimal projection used now.

## 2. Core state types

Every persistent object MUST expose at least:

```text
id
kind
scope
evidence[]
dependencies[]
invalidators[]
status
version
created_by
data
```

Required kinds:

```text
Experience
Law
Capability
Applicability
Boundary
Obstruction
Residual
Representation
Lens
Constructor
Disposition
Counterexample
Quotient
Dependency
```

Capability is decomposed as:

```text
content
entry
applicability
composition
termination
recovery
```

A system does not “have a capability” merely because `content` exists. Entry, applicability, termination and recovery remain independently testable.

## 3. Graph semantics

Let `G=(N,E)` be the addressable Thought Matrix.

Initial edge vocabulary:

```text
APPLIES_TO
DEPENDS_ON
CONTRADICTS
QUOTIENTS
REFINES
ENABLES
OBSTRUCTS
COMPOSES_WITH
INVALIDATED_BY
DERIVED_FROM
TRANSFERRED_TO
SUPERSEDES
```

Do not infer semantic equivalence from graph form alone. Verifier behavior decides within the declared scope.

## 4. Continuation-space semantics

For world state `s`, define:

```text
C(s) = set of currently admissible continuations
```

A continuation is an executable or testable next move.

Development changes cognition when it changes the reachable continuation space under fixed budget:

```text
C_Dt(s) != C_Dt+1(s)
```

The strongest event is:

```text
x not reachable under D_t
x reachable under D_t+1
```

Laws may quotient equivalent continuations. Obstructions eliminate regions. Counterexamples split a quotient. New representations or constructors may create continuations not expressible before.

## 5. Developmental update operator

One update is:

```text
Delta(D_t, E_t, V) -> {retain, split, merge, promote, revoke, reopen, construct, quotient}
```

where `V` is external verifier authority.

Acceptance gate:

1. proposal has a declared scope;
2. proposal names the evidence/residual that motivated it;
3. proposal has a smallest deciding test;
4. test is externally decided;
5. causal gain is measured against matched control/ablation where the claim requires it;
6. accepted object is versioned and reversible;
7. counterevidence names an invalidator and triggers narrowing, split, reopen or revoke.

## 6. Governing loop

```text
retrieve minimal relevant neighborhood
-> project active lens
-> propose strongest distinction-changing move
-> choose smallest deciding test
-> execute
-> external verification
-> record experience
-> compute residual
-> closure test
-> obstruction analysis
-> update developmental graph
-> re-project
-> continue
```

Stop when:

```text
verified success
OR fixed obstruction
OR no remaining decision-changing test under budget
```

## 7. Residual -> ontology change

Persistent residuals are not merely failures. They are evidence that the current continuation language may be inadequate.

```text
repeated residual
-> cluster by behavioral signature
-> mine minimal contrasts
-> identify missing distinction / conditioning variable / operator / representation
-> propose ontology change
-> verify causally
-> install or reject
```

Failure migration is not progress. A proposal counts only if it removes a root obstruction or exposes a genuinely downstream residual.

## 8. Compression / decompression law

Core developmental primitive:

```text
verified invariance -> quotient / compress
counterexample      -> split / recover distinction
```

Operationally:

- if two regions are indistinguishable by the verifier over the stated scope, a quotient may replace them;
- the quotient records members and evidence;
- a separating counterexample invalidates the permission to forget;
- the runtime restores the distinction and records the separator.

Mnemonic:

> A law gives permission to forget; a counterexample withdraws that permission.

## 9. Machine Experience and cumulative experiential learning

Raw encounter:

```text
state + action + consequence
```

Machine Experience:

```text
consequential encounter + retained structural consequence
```

Cumulative Experiential Learning:

```text
experience changes how subsequent experience is processed
```

The decisive DI criterion is therefore not “the system remembers E1,” but:

```text
E1 -> Delta D1
Delta D1 changes the processing / discoverability / sample efficiency of E2
```

## 10. Wake / sleep architecture

Fast state:

```text
D_t -> D_t+1
```

Properties: explicit, cheap, reversible, scope-bearing, continuously testable.

Slow state:

```text
theta_t -> theta_t+1
```

Properties: optional neural consolidation, expensive to reverse, must be reverified.

Consolidation gate requires:

```text
repeated verified transfer
+ stable applicability scope
+ no unresolved invalidators
+ regression suite pass
+ recoverable explicit source object
```

After compilation, explicit source remains authority until neural competence + scope + termination are reverified.

## 11. Controller pseudocode

```python
while budget:
    lens = project(current_world, developmental_state)
    continuations = enumerate_admissible(current_world, lens)
    move = rank_by_decision_change(continuations)
    outcome = execute(move)
    verdict = verifier(outcome)
    experience = ledger.append(current_world, move, outcome, verdict)

    if verdict proves target:
        return VERIFIED

    residual = compute_residual(experience, target)
    obstruction = closure_and_obstruction_test(residual, lens)

    if obstruction.closed:
        candidate = construct_from_minimal_contrast(obstruction, ledger)
        verdict2 = verifier(smallest_deciding_test(candidate))
        update_state(candidate, verdict2)
    else:
        update_state(retain_or_refine(experience))

return OBSTRUCTED
```

## 12. Runtime topology

```text
Model Adapter
    |
Agent Runtime <-> Active Lens
    |              |
    |          Thought Matrix
    |              |
World / Tools   Verified World Map
    |
Verifier
    |
Experience Ledger
    |
Development Controller
    |
Graph Update / Constructor
    |
Checkpoint / Revert
    |
Optional Consolidator -> neural adapter/weights
```

## 13. MVP storage choices

Freeze for v0.1:

- immutable JSONL event ledger;
- SQLite for indexed state and checkpoint metadata;
- typed graph serialized as nodes/edges in SQLite tables;
- content-addressed evidence/artifact hashes;
- vector retrieval only as a secondary index, never authority;
- Python controller/runtime;
- verifier adapters as pure interfaces;
- model adapters behind one interface;
- checkpoint/revert at every promoted update;
- no mandatory external graph database.

The first implementation should remain dependency-light enough to audit end-to-end.

## 14. Economic metric

Track developmental efficiency, not only accuracy:

```text
verified_progress /
(model_calls + verifier_calls + tokens + wall_time + dollars)
```

A successful developmental system should stop paying repeatedly for already-resolved structure. Over sequential worlds, cumulative verified progress per unit cost should improve relative to strong memory and cold controls.

## 15. Experimental order

1. Memory boundary: cold/context/strong-memory/DL.
2. Local capability acquisition with revert/restore.
3. Applicability and termination separation.
4. Residual -> missing distinction/operator.
5. Quotient/compress then counterexample/split.
6. O1 makes O2 discoverable.
7. Phase-one development changes phase-two learning curve.
8. Natural heterogeneous worlds.
9. Optional neural consolidation.
10. Open mathematical discovery.

## 16. Public/private boundary

Public demo may expose:

```text
same base
same evidence
protected result
revert / restore
base weight delta
certificate hashes
claim boundary
```

Private kernel retains:

```text
constructor search
continuation ranking
residual clustering
minimal-contrast mining
quotient heuristics
world-map schemas
capability algebra
scope induction
consolidation policy
cross-domain evidence graph
```

The public proof should be independently checkable without publishing the entire developmental algorithm.

## 17. Hard rule

No object becomes “knowledge,” “capability,” “law,” “wisdom,” “lens,” or “development” because the model names it that way.

Only its externally testable causal footprint earns promotion.
