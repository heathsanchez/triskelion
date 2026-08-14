# Natural Constructor Frontier

_Last updated 2026-08-14 NZST — audited through V91; V92/V93b/V94/V95/V96 primary runs live. V94C calibration attested separately._

This file tracks the natural-world constructor-language programme separately from bounded authored calibrations. The external corpus is QuixBugs at commit `4257f44b0ff1181dedaedee6a447e133219fcebf`, a pre-existing program-repair benchmark. Correct implementations are treated according to each experiment's explicit train/test sealing rule.

## Core question

`K_t -> Expressible(K_t) -> Cl(A_t)`

A claim about an irreducible operator is only meaningful relative to the constructor language `K_t`. The programme asks at what representation level external experience begins to induce reusable, causally specific, held-out closure-expanding structure.

## V83 — one-token natural IVAG census

Verdict: `MIXED_NATURAL_IVAG_V83`.

Two minimum repair schemas recur across independent curricula, but the frozen held-out closure remains `0 -> 0 -> 0`. V84 later shows one apparent syntactic convergence was an equal-MDL tie. Recurrence/minimality alone does not make a developmental primitive.

## V84 — observational quotient/lattice

Run `31782263023`, artifact `9212227436`, SHA-256 `96a1be28ae8cefd478f6935c2f8461dbbc8d8209557e58472706468e20481969`.

Across 37 initially failing programs, the complete frozen 26-schema one-token constructor reaches only two tasks:
- `{<= -> <}` -> `find_first_in_sorted`
- `{< -> <=, > -> >=}` -> `quicksort`

No nontrivial inclusion/Hasse structure and no schema reaches multiple distinct tasks. The observational algebra under K0 is too impoverished.

## V85 — verifier-selected generic AST families

Run `31782743901`, artifact `9212772996`, SHA-256 `8d2aa8bacc9903520c6b1083fde4557e2fba5f9e1ec91ad21e7e183c3c1f808d`.

Ten of eleven supplied AST mutation families receive zero training support; `CALL_ARG_SWAP` receives support on one task, below threshold. No K1 is admitted and held-out closure does not expand.

## V86 — exact edit grammar from training-side human fixes

Run `31784429088`, artifact `9213041932`, SHA-256 `436f6ab82d19719f3d6505ebe284124229fb370fa2dc5a4ea038e9c753d2adfa`.

Fourteen exact one-token templates are induced automatically from a frozen training half. They create zero new held-out closure beyond K0. Wrong-pair control solves none. Exact successful edits are real information but too specific to transfer.

## V87 — structural edit-schema induction

Run `31784802703`, artifact `9215089519`, SHA-256 `0181c97c3ce5f9efd9a39156491e64722715b2928165887702373e6a3ac1763c`.

Training-side fixes induce abstract schemas including `CONST_ROLE(str)` and `NAME_ROLE`.

Raw held-out reachability increases from:
- K0: `knapsack`
- K1: `minimum_spanning_tree`, `hanoi`, `knapsack`, `depth_first_search`

However the wrong-pair constructor solves the **exact same four tasks**. Verdict: `MIXED_STRUCTURAL_CONSTRUCTOR_INDUCTION_V87`.

Binding lesson: generic broadening of K can improve solving without constituting developmental learning. Learned K must beat a matched causally wrong constructor.

## V88 — contextual edit-role induction

Run `31785309780`, artifact `9213612717`, SHA-256 `41b274600d0f12c7389f8e320d68edc9ffcb31931c10a81b7075f6825e20b2c9`.

`(parent node, field, change kind)` roles produced an apparent test-suite gain on `bucketsort` and `depth_first_search`; the original verdict also had a sealing-boolean bug and non-monotonic K1 comparison. Manual inspection showed `bucketsort` matched the human repair role, while DFS likely exploited incomplete tests. Promising mixed signal only.

## V89 — fresh-split contextual confirmation

Run `31786710386`, artifact `9213865127`, SHA-256 `79874f34040f87d4af7141e778b5b3076614c2ee92ab2bc4c7a650a5de5cf373`.

K0, K0+learned-context and shuffled-context all solve exactly `knapsack`, `quicksort`. New closure is empty. Verdict: `MIXED_CONTEXTUAL_CONSTRUCTOR_CONFIRMATION_V89`.

Conclusion: V88's local contextual signal does not replicate.

## V90 — protected human-fix confirmation

Run `31786981266`, artifact `9214010229`, SHA-256 `81b998b4f4827382f46b1c9e5208a606358abbbaf4931b28822075cd75e90aaa`.

Ordinary tests again show a contextual gain on `bucketsort`:
- K0: `quicksort`
- K0+context: `quicksort`, `bucketsort`
- context shuffle: `quicksort`

But candidate patches are hash-committed before held-out fixes are revealed, and protected exact-AST agreement is false for both committed candidates. `protected_new_closure = []`.

Verdict: `MIXED_PROTECTED_CONSTRUCTOR_CONFIRMATION_V90`.

Binding lesson: benchmark test-passing is not sufficient evidence of natural constructor transfer.

## V91 — verifier-induced local site ontology

Run `31787205758`, artifact `9214285939`, SHA-256 `22d3966a0b6592fcd866ef115b677875c02ea6bccb6b4cd64c7ab9e53eaa1832`.

No correct implementations are read. Verifier gradients induce a repeated operational class:

`(OP, Compare, ops)` with support 2.

But held-out closure does not expand:
- K0: `find_first_in_sorted`, `knapsack`
- learned roles: same two
- shuffled roles: those two plus `next_permutation`

Verdict: `MIXED_VERIFIER_INDUCED_SITE_ONTOLOGY_V91`.

So verification can induce a nonempty local category, but this category is not yet transferable/closure-expanding.

## V92 — verifier-induced functional-role ontology

Primary run `31789737846` is live. Roles move above AST parent/field identity to coarse functional/dataflow categories such as `CONTROL_GUARD`, `ITERATION_SOURCE`, `STATE_UPDATE`, `RECURSIVE_ARGUMENT`, `INDEX_KEY`, `ACCUMULATE`, and `RETURN_FLOW`. Correct implementations are never read.

A separately labelled NONCLAIM V92P prefix found only one improving training role (`INDEX_KEY` on `kth`), below support threshold, and no new held-out closure. This is an early negative diagnostic, not primary evidence.

## V93 / V93b — anonymous whole-program change geometry

Original V93 was invalidated before outcome inspection because its null merely reordered a prototype list under a max-similarity score and was therefore mathematically identical to the learned arm; the sealing gate also had wrong Boolean polarity.

Corrected V93b run `31790354759` is live. Training-side human fixes are represented only as anonymous whole-program AST graph-delta vectors; the null permutes feature coordinates rather than prototype order. No semantic operator/site labels are supplied.

A shortened V93BP diagnostic is also running and is explicitly NONCLAIM.

## V94 — dynamic state-transition invariants

Primary natural run `31790728003` is live. This moves above static source shape to execution-state delta signatures: event/call structure, collection growth/shrinkage, numerical progress, local-state growth and revisitation. Training-side correct implementations are used only to induce anonymous dynamic prototypes; held-out correct implementations remain sealed.

### V94C calibration

Attested separately in `V94C_DYNAMIC_SIGNATURE_CALIBRATION_RESULT.md`.

Run `31790849808`, artifact `9215374279`, SHA-256 `591574959c797a6467eac15447066be935b89937bd2f0dc29360a3106e882552`.

Authored calibration result:
- 15/15 held-out mechanism classifications correct
- coordinate-permuted null 5/15

Three known mechanisms separate cleanly as collection growth (retention), collection contraction (frontier shrinkage), and numerical descent (fixed-point progress). This validates the measurement language only; it is not natural evidence.

## V95 — anonymous dynamic Collider

Run `31791105193` is live. Training-side verified correct behavior yields anonymous execution-delta vectors. A frozen MDL objective chooses the number and medoids of dynamic clusters without semantic labels. Held-out repair candidates are ranked by similarity against those clusters versus a coordinate-shuffled null.

This is the closest current implementation of the old Collider idea at the execution-state level, but remains supervised on the training split.

## V96 — verifier-only dynamic Collider

Run `31791344169` is live.

This removes human fixes entirely. On training tasks, generic mutations are retained only when they reduce externally measured failing-test counts. Their execution-state deltas are anonymously clustered under a frozen MDL rule. Held-out candidate syntax and verification budgets are identical for learned and coordinate-shuffled arms.

A positive result would be the strongest natural bridge in this sequence: `verifier improvement -> induced dynamic structure -> held-out causal search advantage`, without correct solutions anywhere in the developmental history.

## Current falsification ladder

Natural evidence has rejected increasingly shallow interpretations:

`recurring token patch != developmental primitive`

`flat one-token schema set != useful natural lattice`

`hand-named AST mutation family != supported constructor ontology`

`exact human edit template != transferable constructor grammar`

`structural schema gain == wrong-pair gain -> not causal learning`

`local AST contextual role != stable transferable ontology`

`test-passing contextual gain != protected human-fix agreement`

`verifier-induced local site class != held-out closure expansion`

The live hypothesis has therefore moved above local repair syntax toward **functional and dynamic state transformations**.

## Crown-jewel boundary

Even a positive V92–V96 bridge would not by itself establish autonomous constructor genesis. The maximal gate remains:

`frozen verifier residuals -> construct K1 -> strict natural held-out closure growth -> K1 makes K2 discoverable -> ancestor ablation moves the future developmental frontier backward`.

The correct object may ultimately be a coupled algebra over:
- semantic/epistemic transformations,
- typed composition/control grammar,
- executable state-transition motifs/organs,
- constructors that generate those structures.
