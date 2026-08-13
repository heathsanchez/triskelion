# Triskelion / Metalogic Research State

_Last updated: 2026-08-14 NZST_

## Current strongest synthesis

The project is converging on a **self-extending verified capability algebra** rather than a flat memory or fine-tuning system.

At developmental state `A_t`, the system has a verified set of operators, composition laws, scopes, provenance, and revision conditions. For a new target `T` it should first test whether `T` is already in bounded lawful closure. If yes, recompose rather than invent. If closure fails, the residual may justify a minimal new generator. Verification controls admission. Repeatedly useful verified explicit capabilities may then be consolidated into neural weights, while the explicit source/provenance remains authoritative.

A useful distinction is now:

1. **Reuse** — invoke an existing capability.
2. **New composition** — construct a new capability from existing generators.
3. **New law** — learn a verified scoped rule about when compositions are legal/equivalent.
4. **New generator** — add a genuinely closure-expanding primitive.
5. **Compounding** — a verified generator changes what new generator is discoverable next.
6. **Meta-growth** — verified operator experience produces/revises reusable constructor families which change what operators can subsequently be built.

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

### External algebra / recursive discoverability

- **even_pairs negative**: apparent `MAP_PAIRS` novelty was already in closure through lawful recomposition, so primitive invention was correctly rejected. This remains the canonical closure-before-invention negative.
- **EXCEPTION_FLOW external formation/reuse**: independently selected ffmpeg source exposed a missing exception-flow boundary; the operator was retained and later independently required by SHAP. Retained-library ACCEPT vs ablated-library REJECT established bounded causal reuse.
- **V30b**: on fixed independently authored QuixBugs code, syntactic ambiguity became a scoped extensional-equivalence law; quotienting by the verified law changed composition-search topology and enabled a later chunked repair within the frozen horizon.
- **V32**: global algebraic laws were mostly false. No CMP/BIN/CONST pair commuted over the full support, despite many local contexts collapsing all six triple orderings to one extensional class. Conclusion: equations must carry explicit scope/context.
- **V33**: fixed external Rich source produced a causal frontier chain `Raise -> With -> GeneratorExp`. Each retained frontier handler exposed the next frontier; ancestor ablation hid the successor again. This established bounded within-source `Discoverable(A_t)` growth.
- **V34**: source-distinct recursive discoverability ratchet across three independently authored fixed repositories. Deterministic lineage: Requests `Try` -> Rich `Raise` -> Flask `With`. Corpus contained 1,025 functions and 9,240 eligible three-generation lineages before hash selection. Cold later targets exposed only earlier frontiers; ancestor ablations on the deepest target moved discovery back to the missing ancestor. Verdict: `PASS_SOURCE_DISTINCT_DISCOVERABILITY_RATCHET_V34`.

### V35 constructor-family formation — bounded meta-level result

Question: can exact operator instances be compressed into a reusable constructor family that then causally constructs a new source-distinct operator?

Frozen V34 instances:

- exact `Try` handler from Requests;
- exact `Raise` handler from Rich;
- held-out `With` handler from Flask.

A naive generic `PARAMETRIC_AST_HANDLER` was **rejected** because it also admitted protected non-statement AST objects (`Constant`, `Name`, `Load`, `Store`, `Add`, `Eq`). This is a useful negative: compression alone is insufficient for constructor promotion.

The smallest scoped repair tested was a typed `PARAMETRIC_STMT_HANDLER(node_type, declared_fields)`. Under the transparent description-length proxy it:

- covered the exact Try and Raise handlers;
- rejected the protected non-statement negatives;
- constructed the unseen source-distinct With handler;
- compressed the two exact handlers from cost 247 to 148 (gain 99);
- when the constructor family was ablated, With construction disappeared while already-retained Try/Raise remained available.

Interpretation: bounded evidence for

`exact verified operator instances -> scoped constructor abstraction -> unseen operator construction`.

Claim boundary: the constructor candidate language and type predicates are still supplied. This is **not** unrestricted constructor invention.

## Current mathematical framing

Let a developmental algebra be approximately

`A_t = (O_t, L_t, V, D_t, K_t)`

where:

- `O_t`: currently verified generators/capabilities;
- `L_t`: verified scoped equations/rewrite/composition laws;
- `V`: external verifier family / authority boundary;
- `D_t`: frozen discovery procedure induced by the current algebra;
- `K_t`: currently available constructor algebra for forming candidate operators/representations.

Define:

- `Closure(A)`: what can be constructed now by lawful composition.
- `Discoverable(A)`: what new verified generators the frozen discovery process can reach from the current algebra.
- `Constructible(K)`: what operator schemas the current constructor algebra can express.

V34 gives bounded external evidence that `Discoverable(A_0)`, `Discoverable(A_1)`, and `Discoverable(A_2)` differ causally.

The next stronger meta-level target is:

`Constructible(K_0) ⊊ Constructible(K_1)`

with a later operator/constructor family discoverable only because the earlier verified constructor extension exists.

## Scientific discipline / claims boundary

Current results support bounded mechanisms: closure-before-invention, verified operator formation, independent causal reuse, scoped law discovery, quotient search, recursive source-distinct discoverability, explicit composition, hierarchical chunking, protected neural consolidation, typed cognitive programs, and bounded constructor-family abstraction.

Do **not** yet claim a universal cognitive algebra, unrestricted operator invention, unrestricted constructor invention, or open-ended self-improvement.

## Immediate next experiment

**V36 — Constructor Discoverability Ratchet**

Freeze an old constructor algebra `K0`, a generic meta-construction/search budget, protected negatives, and source-selection protocol. Require:

1. a first residual/operator family is not expressible in `Closure(K0)`;
2. a minimal constructor generator `k1` is synthesized and externally scoped/verified;
3. `k1` enables construction of an operator family that was not constructible under `K0`;
4. that new operator changes the frontier on a source-distinct target and exposes a residual requiring a second constructor family `k2`;
5. `k2` is not constructible/discoverable under `K0` but is under `K1=<K0,k1>`;
6. ablating `k1` removes discovery of `k2`, not merely final task success;
7. all constructor laws carry provenance, scope, counterexamples, and explicit revision/removal conditions.

This is the constructor-level analogue of V34 and is now the highest-value falsification target.