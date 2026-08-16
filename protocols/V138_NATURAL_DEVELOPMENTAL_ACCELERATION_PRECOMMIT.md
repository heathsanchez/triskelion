# V138 — Natural developmental acceleration and repeated-development precommit

Date frozen: 2026-08-16 NZST

## Purpose

V135 left Q7 natural developmental reachability, Q8 natural multigeneration compounding, Q9 constructor growth, and Q10 open-ended repeated development open. V137 subsequently introduced an exact semantic quotient over the 60 comparison-relation presentations. V138 tests only consequences that were still not directly measured.

This protocol does not backfill higher-order gates from V54, V80, V132, V135, or V137. Historical results are controls/background only.

## External corpus

Pinned QuixBugs commit:

`4257f44b0ff1181dedaedee6a447e133219fcebf`

The runner uses the existing V135 verifier convention: correct Python programs are mutated at natural one-comparison sites and checked with the pinned QuixBugs pytest tests. Timeouts count as failures; they are not dropped.

## O1

O1 is the exact semantic presentation quotient introduced by V137:

- 60 syntactic `(swap, strict token, relaxed token)` candidates;
- 30 extensional semantic classes under operand-swap duality;
- one deterministic representative per class selected without verifier outcomes.

O1 itself does not identify which relation is correct on a new program. Acquisition verifier evidence is still required.

## Subsequent capability O2

For every leave-one-program-out natural fold, O2 is the semantic comparison-relation class that uniquely explains the acquisition verifier transitions and then survives the held-out program verifier.

Direct-solution exclusion is mandatory: O1 must leave at least two possible semantic classes before acquisition evidence. If O1 alone identifies O2, CP5 is invalid.

## CP5 matched arms

Primary discovery-cost measure: **candidate hypotheses that must be evaluated to establish the selected semantic capability under the arm's representation**. This is frozen before the V138 run.

Arms:

1. `COLD_SYNTAX_60`: all 60 syntactic candidates; no quotient.
2. `RAW_HISTORY_60`: same 60 candidates plus acquisition identifiers/outcome counts serialized as raw history; no semantic quotient.
3. `O1_QUOTIENT_30`: exactly one deterministic representative from each of the 30 semantic classes.
4. `SHUFFLED_EQUAL_SIZE_30`: deterministic seed `20260816`; 30 syntactic candidates sampled without semantic balancing.

All arms see the same acquisition verifier outcomes for candidates they contain. No held-out outcome participates in selection.

### CP5 gates

- D1 apparatus valid and pinned external commit reproduced.
- D2 O1 direct-solution exclusion holds in every evaluable fold.
- D3 O2 is uniquely selected at semantic-class level in the O1 arm.
- D4 selected O2 passes held-out verifier at >=90% and ablation restores held-out failure at >=90%.
- D5 O1 primary discovery cost is strictly below cold and raw-history cost.
- D6 removing O1 restores cold cost.
- D7 shuffled equal-size state does not dominate O1 on both semantic coverage and verified O2 discovery.

`PASS_V138_CP5_NATURAL_ACCELERATION` iff D1-D7 all hold.

## Q7 reachability under a fixed budget

A separate frozen budget of 30 candidate hypotheses is applied to each representation. `COLD_BUDGET30` uses the first 30 candidates in the frozen expanded-generation order; `O1_BUDGET30` uses one representative per exact semantic class.

Q7 passes only if O1 discovers/verifies O2 on strictly more evaluable folds than cold under the same budget. Equality is a null, even if CP5 cost compression passes.

## Generation 3 / scope capability O3

To test rather than assume natural multigeneration, application of O2 generates a second label on every natural strict-comparison site: whether the O2 relaxed transformation is verifier-harmful (`RELAX_SENSITIVE`) or verifier-safe (`RELAX_SAFE`).

The runner extracts only generic AST structural features fixed here:

- immediate parent AST node type;
- nearest statement node type;
- comparison nesting depth;
- left operand AST type;
- right operand AST type;
- inside loop boolean;
- inside conditional boolean;
- comparison site ordinal bucket `{0,1,2+}`.

O3 search language is frozen to single-feature equality/boolean rules and conjunctions of two such literals. No program name, function name, source token string, failure node id, or held-out label may be a feature.

Leave-one-program-out selection chooses the rule with highest acquisition balanced accuracy, then fewer literals, then lexical rule id. O3 is admitted only if median held-out balanced accuracy >=0.75, at least 8 programs are evaluable, and an O2-ablation arm cannot form the RELAX_SENSITIVE/RELAX_SAFE labels by construction.

Q8 natural multigeneration passes only if CP5 O1→O2 passes **and** O2-generated evidence prospectively yields admitted O3 under the above gate. Otherwise Q8 is a measured negative/obstruction, not left untested.

## Q10 repeated-development stream

The natural strict-comparison sites are ordered by `(program, site)` before outcomes are interpreted. The first 20 sites form a frozen episode stream if at least 20 exist.

At each episode the controller may retain only:

- the exact O1 quotient;
- an O2 semantic class after it has enough prior verifier evidence for unique class selection;
- an O3 structural rule after the O3 admission gate is reached on prefix-only data.

No other semantic state may be added.

Q10 does **not** pass merely for processing 20 episodes. It requires:

- at least 20 valid episodes;
- at least three strict developmental state transitions (empty→O1, O1→O1+O2, O1+O2→O1+O2+O3);
- each retained state survives replay on all earlier obligations;
- the final state improves a frozen future-cost or held-out endpoint over the initial state.

If the corpus has <20 sites, verdict is `CORPUS_CEILING_Q10`. If 20 episodes run but fewer than three state transitions occur, verdict is `NEGATIVE_NO_OPEN_ENDED_DEVELOPMENT`.

## CP6 recompression audit

The 60→30 O1 quotient is evaluated under the developmental constitution:

- exact extensional equivalence of every paired class on integer domain `[-3,3]^2`;
- every natural candidate outcome agrees inside each semantic class wherever both presentations are evaluated;
- class-level acquisition and held-out O2 verdicts are preserved;
- serialized candidate description size and candidate count both strictly decrease.

CP6 is `PASS_V138_CP6_RECOMPRESSION` only if all replay and strict-complexity gates hold. This is bounded to the comparison-relation capability family.

## Q9 / V134 boundary

V134 was separately precommitted as a Specimen specialization-before-instance-synthesis discriminator. V138's QuixBugs runner does not manufacture a constructor-growth result from it. Q9 remains open until V134 is executed and, if it isolates a barrier, a separately frozen successor K6 is admitted with causal ablation and protected replay.

## Information boundary

- source/candidate order is fixed before interpreting V138 verifier outcomes;
- held-out program outcomes are never arguments to capability/rule selection;
- failed/time-out cases remain in denominators;
- all reported higher-order PASSes must be produced by this fresh run, not copied from historical summaries.

## Claim boundary

A CP5 pass establishes bounded natural developmental acceleration for one external program-repair relation family. A Q8 pass would establish a fresh three-state natural developmental chain under this fixed representation/search substrate. A Q10 pass would establish only a 20-episode bounded repeated-development result, not open-ended recursive self-improvement in the unrestricted sense.