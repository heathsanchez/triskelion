# Triskelion / Metalogic Research State

_Last updated: 2026-08-14 NZST_

## Current strongest synthesis

The project is converging on a **self-extending verified capability algebra** rather than a flat memory or fine-tuning system.

At developmental state `A_t`, the system has a verified set of operators, composition laws, and provenance. For a new target `T` it should first test whether `T` is already in bounded lawful closure. If yes, recompose rather than invent. If closure fails, the residual may justify a minimal new generator. Verification controls admission. Repeatedly useful verified explicit capabilities may then be consolidated into neural weights, while the explicit source/provenance remains authoritative.

A useful distinction is now:

1. **Reuse** — invoke an existing capability.
2. **New composition** — construct a new capability from existing generators.
3. **New law** — learn a verified rule about when compositions are legal/equivalent.
4. **New generator** — add a genuinely closure-expanding primitive.
5. **Compounding** — a verified generator changes what new generator is discoverable next.

The remaining high-value gate is #5.

## Current cognitive IR hypothesis

Candidate semantic operators:

`DISTINGUISH, GENERATE, RELATE, PROBE, CONSTRAIN, SELECT, COMPOSE, RETAIN, TRANSDUCE, RECURSE`

The typed state space compresses strongly to three functional classes:

- **GROUNDED** — tied to an external boundary/reality.
- **OPEN** — unresolved possibility, candidates, relations, evidence.
- **MEMORY** — retained developmental structure.

The three-state algebra is intentionally only a quotient: multiple semantically distinct operators share the same coarse state transition.

## Best verified/causal experimental results

### River / neural-development sequence

- **V15**: retained primitive skills did not spontaneously compose. `A=B=C=100%` individually while unseen `AB/ABC=0%`. This localized a missing explicit composition function.
- **V16**: frozen V15 neural primitives + explicit verifier-governed composition recovered `AB=100%`, `ABC=100%`; fresh reload preserved performance; primitive ablations destroyed the corresponding composite. No new gradients were required.
- **V17**: promoted verified `D=A∘B`, then reused `D∘C` for the deeper composite. Hierarchical chunking reduced candidate evaluations from 56 to 24 (57.1%) with no accuracy loss.
- **V18**: verified explicit discovery generated correct neural supervision, but fixed replay/consolidation damaged protected ancestors. Useful negative result: discovery/verification worked; fixed consolidation policy did not.
- **V18b**: verifier-driven adaptive rehearsal closed the bounded discover→verify→compile loop. After regression-sensitive replay, `A=B=C=D=100%` survived close/reload; then verified higher-order `E=D∘C` became direct neural competence while `A=B=C=D=E=100%` survived reload.

### Cognitive alphabet / grammar sequence

- Frozen 10-operator alphabet encoded all 51 manually normalized cross-layer transitions with mean program length 2.78 and max 4. Initial free-text LODO prediction was mixed, so the alphabet is not declared universal/verified.
- Opaque-label semantic control: correct definitions materially outperformed shuffled/no-definition controls, suggesting the operator meanings carry usable information beyond names.
- **V19**: cross-domain operator words learned from other domains compressed held-out programs by 29.6%; matched shuffled words gave ~1% compression. 16 cross-domain words found, 15 spanning multiple layers.
- **V20**: held-out true operator order ranked above all permutations on 77.6% of multi-step programs. `CONSTRAIN→SELECT`, `SELECT→RETAIN`, and `RELATE→COMPOSE` showed strong directionality.
- Cross-domain executable word test: `RELATE→COMPOSE→CONSTRAIN→SELECT→RETAIN` solved 90/90 finite proof, safe interpreted program-repair, and system-configuration instances. `SELECT` before `CONSTRAIN` and `RETAIN` before `SELECT` gave 0/90; swapping `COMPOSE` before `RELATE` preserved correctness but roughly doubled search.
- **V21 typed IR**: all canonical programs type-check; target recovery 100%; critical reversal rejection 100%; mean search pruning 99.26%. Many 120–5,040 permutation searches collapse to one legal typed program.
- Type minimization: many named internal types collapse while retaining most pruning. A three-state `GROUNDED / OPEN / MEMORY` view remains highly informative; further collapse loses substantial pruning.
- Cross-domain continuation grammar: training on other domains predicts the hidden final operator at 61.2% vs 20.4% majority baseline; paired exact test approximately `p=3.6e-5`.

### MetaMath V23

V23 passed all frozen internal gates on the 51-transition / 11-domain corpus.

- 17 leave-one-domain-out robust precedence laws.
- Strong non-commutative rewrite candidates, including normalizing toward `RELATE→COMPOSE`, `COMPOSE→CONSTRAIN`, `TRANSDUCE→CONSTRAIN`, `CONSTRAIN→SELECT`, `SELECT→RETAIN`.
- Reusable cross-domain words compress 142 raw operator tokens to 88 coded tokens: **38.0% compression**.
- The semantic transition graph is recurrent rather than a single linear pipeline.
- The coarse three-state transition algebra generates only **23 distinct state transformations**, with short normal forms, but is too lossy to identify semantic equivalence: e.g. `GENERATE`, `RELATE`, and `COMPOSE` can share a coarse `OPEN→OPEN` signature while executable experiments show they are causally distinct.

## Current mathematical framing

Let a developmental algebra be approximately

`A_t = (O_t, L_t, V, D_t)`

where:

- `O_t`: currently verified generators/capabilities;
- `L_t`: verified conditional equations/rewrite/composition laws;
- `V`: external verifier family / authority boundary;
- `D_t`: frozen discovery procedure induced by the current algebra.

Define:

- `Closure(A)`: what can be constructed now by lawful composition.
- `Discoverable(A)`: what new verified generators the frozen discovery process can reach from the current algebra.

Capability accumulation is `Closure(A_0) ⊊ Closure(A_1)`.

The next decisive result is stronger:

`Discoverable(A_0) ⊊ Discoverable(A_1)`.

That would show that a prior verified invention changes the space of later inventions, not merely later task success.

## Scientific discipline / claims boundary

Current results strongly support bounded mechanisms: verified reuse, closure-before-invention, causal primitive dependence, explicit composition, hierarchical chunking, protected neural consolidation, typed cognitive programs, and cross-domain grammar structure.

Do **not** yet claim a universal cognitive algebra, open-ended self-improvement, or recursive capability compounding. The next experiment is explicitly designed to test the latter under a frozen bounded protocol.

## Immediate next experiment

**V24 — Discoverability Ratchet**

Precommit a frozen typed discovery algorithm and a three-generation task stream. Require:

1. `q1` is not in old lawful closure and is independently synthesized/verified.
2. `q2` is *not discoverable* under the same frozen discovery algorithm from `A0`.
3. After adding `q1`, `q2` becomes discoverable from `A1`.
4. A later independent target requires the composed lineage.
5. Ablating `q1` removes not only final-task success but the ability to discover `q2`.
6. An oracle-intermediate-representation control restores `q2` discoverability without `q1`, showing the causal mechanism is representation/capability access rather than an arbitrary hard-coded lock.

This is a bounded causal test of whether verified algebra growth expands future discoverability.