# Unified Developmental Architecture

## Thesis

The repository family is best understood as one verifier-controlled developmental system rather than a collection of unrelated experiments.

> Intelligence here is not merely search through a fixed state space. It is externally verified modification of the representation, operator set, routing policy, or executable capability set in which future search occurs.

Canonical loop:

```text
failure/residual
  -> diagnose missing distinction or bad representation
  -> propose representation/operator/capability change
  -> run smallest deciding external test
  -> accept/reject under a verifier and resource budget
  -> compress accepted change
  -> scope applicability
  -> persist as law/capability/provenance
  -> reapply to the sharpened residual or a new task
```

## Repository map

### `heathsanchez/mathgraph` — inquiry/control plane

Role: identify what remains unresolved, route deciding tests, preserve verified outcomes, and compound them.

Core objects and mechanisms visible in the history:

- residual and obstruction driven continuation;
- Lawbook admission/replay;
- Reason Atlas routing memory;
- semantic validation and executable trust boundaries;
- recursive residual compounding;
- polarized quotient continuation IR;
- proof/counterexample inventory;
- SAIR-backed external evaluation.

Interpretation: MathGraph answers **what should be tried next, what evidence is admissible, and what verified knowledge may safely be retained or forgotten**.

### `heathsanchez/latent-coordinate-law-engine` — representation-change discovery

Role: search for latent coordinates, portals, quotient relations, continuation kernels, and higher-value representations when the current language stalls.

Historical progression includes latent-coordinate laws, portal grammar, semantic portals, hidden-world semantic discovery, survivorship, discovery acceleration, future-volume estimation, and maximum viable complexity.

Interpretation: this is the machinery for **changing the state space rather than merely searching it harder**.

### `heathsanchez/mathgraph-igp24-continuation-engine` — replayable developmental continuation

Role: provenance-bearing continuation, feedback-loop scoring, replayable packages, survivor geometry, and cycle orchestration.

Interpretation: operationalizes the move from one verified representation change to the next while retaining provenance.

### `heathsanchez/triskelion` — executable developmental runtime

Role: turn verified discoveries into portable executable capabilities and control their later invocation.

Key runtime components recovered from the sealed CP1 artifact:

- registry;
- executable artifacts;
- scope predicates;
- verifier boundary;
- provider abstraction;
- install/import/export;
- enable/disable/uninstall;
- isolated replay and provenance.

The CP1 causal arms separate:

```text
COLD -> RAW MEMORY       passive textual experience
RAW MEMORY -> ALWAYS-ON executable capability extraction
ALWAYS-ON -> VERIFIED    applicability/scoping control
```

The IKKF branch lineage (`portable-capability` -> `capability-routing` -> `verified-capability-os` -> `verified-capability-invocation`) is therefore a product/architecture lineage, not a separate research direction.

### Triskelion V102-V115 — developmental theory layer

Recent experiments increasingly formalize the runtime's underlying mathematical object:

- boundary robustness and compression;
- quotient-level operator discovery;
- adversarial quotient identity;
- capability lattices/posets and their falsification where appropriate;
- natural-code quotient bridges;
- leave-one-program-out and cross-family reuse;
- verifier-discovered quotients;
- blind historical repair;
- prospective BugsInPy prediction;
- closure-extension identity;
- horizon-indexed capability identity;
- verifier/resource-indexed developmental state;
- developmental reachability preorder.

Working abstraction:

```text
state S = (representation/operator/capability resources, verifier, horizon/resource budget, provenance)
```

and a verifier/resource-relative preorder `S1 <= S2` when the admissible reachable outcomes from `S1` remain reachable from `S2` under the same observational regime.

Important consequence: **capability identity is observational, verifier-relative, and horizon-relative, not merely file or weight identity**.

### BugsInPy / CP3 — real-world causal test

Role: test whether acquisition on independently authored software becomes a frozen reusable capability that affects genuinely protected cases.

Two complementary lines:

1. V110/V111/V115-style prospective structural/operator predictions on real code.
2. CP3 four-arm runtime experiment testing causal competence gain and applicability control.

CP3 is therefore the principal missing end-to-end credibility layer, not the source of the core idea.

### `heathsanchez/equational_theories` and `equational-theories-lean-stage2` — formal mathematics proving ground

Role: external finite implication world with Lean proofs, finite countermodels, quotient structure, closure/Hasse relations, residuals, witness grammars, and held-out consequences.

Interpretation: supplies a rigorous example of the law:

> a verified equivalence permits the system to forget distinctions; a counterexample withdraws that permission.

It is also an external route from residual detection into a live formal mathematics repository.

### `heathsanchez/lean-kernel-arena` and `lean4lean` — the verifier becomes an optimization object

Role: preserve soundness/completeness while changing checker representation and algorithms under measurable resource constraints.

Interpretation: the same developmental controller applies one level down:

```text
performance/completeness residual
  -> mechanism diagnosis
  -> representation/algorithm intervention
  -> semantic verifier + resource measurement
  -> retain or reject
```

A semantically correct intervention that regresses the frozen resource objective is a valid negative result, not a capability.

### `heathsanchez/specimen` — external structural analogue / transfer surface

Role: constrained generation, dependency discovery, schedule search, delegated producers, pattern coverage, scoring, recursion and applicability-sensitive producer choice.

Interpretation: independently demonstrates the systems value of **discovering a stronger lawful operator and changing the schedule only when its applicability conditions hold**. Do not count it as Triskelion evidence without a prospective frozen intervention.

### `heathsanchez/vericoding-benchmark`, `OpenGauss`, `QuantumOptics.jl`, `FormalBook` — external transfer reservoir

Role: independently authored software/formal/scientific surfaces suitable for future prospective tests.

Evidence rule: their existence in the account is not evidence. They become evidence only after a frozen, precommitted Triskelion intervention is evaluated there without target-specific tuning.

## Unified object model

The architecture can be expressed as four layers.

### Layer 1 — Observation

Inputs:
- failures;
- residuals;
- verifier traces;
- counterexamples;
- resource regressions;
- named obstructions.

Output: the smallest unresolved distinction that currently matters.

### Layer 2 — Development

Candidate changes:
- quotient/canonicalization;
- dependency or relation lift;
- state introduction;
- arity/constructor expansion;
- recursive/nested fixpoint;
- scope/applicability rule;
- composition of existing operators;
- deletion after negative evidence.

Output: a proposed enlargement, quotient, or reorganization of reachable behavior.

### Layer 3 — External decision

A candidate is admitted only through an independent verifier and the precommitted resource criterion.

Possible outcomes:
- verified/admit;
- refuted/delete;
- obstructed/infrastructure unknown;
- semantically valid but resource-rejected.

### Layer 4 — Persistence and invocation

Accepted changes become:
- Lawbook entries;
- compact capability artifacts;
- registry entries;
- applicability predicates;
- provenance edges;
- replayable packages.

They can then be installed, disabled, removed, imported, composed, or withheld by scope.

## The unifying distinction

Conventional learning asks whether the model's output distribution changed.

This program asks a stronger systems question:

> Did verified experience change what transformations, distinctions, abstractions, or executable operators are available to future reasoning, while preserving a trustworthy boundary on when they apply?

That is **verified developmental plasticity**.

## Evidence ladder

1. **Mechanics:** install / enable / disable / uninstall / import work.
2. **Causality:** removal or ablation removes the gained behavior.
3. **Verification:** external checker decides success, not model self-report.
4. **Compression:** retained artifact is smaller/cheaper than replaying the full history.
5. **Transfer:** capability works on source-distinct or held-out tasks.
6. **Applicability:** scoped use beats indiscriminate always-on invocation.
7. **Operator discovery:** old closure is insufficient and a new lawful operator/quotient is discovered.
8. **Developmental composition:** one acquired capability makes later capability discovery reachable or cheaper.
9. **Real-world protected evaluation:** the complete chain survives independently authored protected tasks.

The existing work establishes substantial evidence through levels 1-8 in bounded settings. CP3 is intended to close level 9 cleanly on real software.

## Canonical demo

```text
Frozen model + task A
    FAIL
      |
bounded verified experience
      |
discover / verify / compress capability C
      |
INSTALL(C)
      |
source-distinct task B
    PASS
      |
UNINSTALL(C)
    FAIL
      |
IMPORT(C) without original learning conversation
    PASS
```

Then test applicability:

```text
ALWAYS-ON: C is available everywhere -> competence gain + possible misuse
VERIFIED:  same C, scope-gated      -> preserve gain, reduce bad activation
```

No model-weight change is required for the claim. The developmental state changes outside the frozen base model through verified executable structure.

## Current highest-priority unresolved item

The architecture is not presently missing another abstract mechanism. The decisive gap is a **protocol-clean real-world CP3 execution** with:

- acquisition-only frozen capability payload;
- protected information boundary preserved;
- identical four-arm budgets;
- fresh state per cell;
- native verifier outcomes;
- no protected tuning or post-hoc exclusions;
- applicability result interpreted separately from raw competence.

Until that run exists, bounded and prospective evidence should remain clearly labeled as such.
