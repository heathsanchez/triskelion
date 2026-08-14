# Natural Constructor Frontier

_Last updated 2026-08-14 NZST — through V89; V87/V88P/V90/V91 running or awaiting final audit._

This file tracks the natural-world constructor-language programme separately from bounded authored calibrations. The external corpus is QuixBugs at commit `4257f44b0ff1181dedaedee6a447e133219fcebf`, a pre-existing program-repair benchmark. Correct implementations are treated according to each experiment's explicit train/test sealing rule.

## Core question

`K_t -> Expressible(K_t) -> Cl(A_t)`

A claim about an irreducible operator is only meaningful relative to the constructor language `K_t`. The programme therefore asks which representation of candidate transformations is actually supported by external experience.

## V83 — one-token natural IVAG census

Verdict: `MIXED_NATURAL_IVAG_V83`.

Two minimum repair schemas recur across independent curricula, but the frozen held-out closure remains `0 -> 0 -> 0`. V84 later shows that one apparent syntactic convergence was an equal-MDL tie. Recurrence/minimality alone does not make a developmental primitive.

## V84 — observational quotient/lattice

Run `31782263023`, artifact `9212227436`, SHA-256 `96a1be28ae8cefd478f6935c2f8461dbbc8d8209557e58472706468e20481969`.

Across 37 initially failing programs, the complete frozen 26-schema one-token constructor reaches only two tasks. Nonempty extensional classes:

- `{<= -> <}` -> `find_first_in_sorted`
- `{< -> <=, > -> >=}` -> `quicksort`

No nontrivial inclusion/Hasse structure and no schema reaches multiple distinct tasks. The observational algebra under K0 is too impoverished; quotient by verified behavior, not syntax.

## V85 — verifier-selected generic AST families

Run `31782743901`, artifact `9212772996`, SHA-256 `8d2aa8bacc9903520c6b1083fde4557e2fba5f9e1ec91ad21e7e183c3c1f808d`.

Eleven supplied AST mutation families are tested using training verifier support only; correct implementations are never read. Ten receive zero support and `CALL_ARG_SWAP` receives support on one training task, below the frozen threshold of two. No K1 is admitted and held-out closure does not expand.

Conclusion: the hand-specified AST family vocabulary is not empirically justified as the constructor ontology.

## V86 — exact edit grammar induced from external successful repairs

Run `31784429088`, artifact `9213041932`, SHA-256 `436f6ab82d19719f3d6505ebe284124229fb370fa2dc5a4ea038e9c753d2adfa`.

Human fixes are read only on a frozen training half; held-out correct implementations remain sealed. Fourteen exact one-token edit templates are induced automatically. They solve `quicksort` on held-out data but create zero new closure beyond K0. A rotated wrong-pair control solves none.

Verdict: `MIXED_PATCH_INDUCED_CONSTRUCTOR_V86`.

Conclusion: successful external experience contains real edit information, but exact token templates are too specific to form a transferable constructor language.

## V87 — structural edit-schema induction

Status: primary CI still running at last audit. Training-side external fixes induce abstract AST change kinds; held-out correct implementations remain sealed. This asks whether edit *kind* transfers beyond exact syntax.

## V88 — contextual edit-role induction

Run `31785309780`, artifact `9213612717`, SHA-256 `41b274600d0f12c7389f8e320d68edc9ffcb31931c10a81b7075f6825e20b2c9`.

Training-side fixes induce `(parent node, field, change kind)` roles. Raw held-out test-suite results add `bucketsort` and `depth_first_search` beyond K0; a context-shuffle control also reaches `depth_first_search` but not `bucketsort`. The original verdict calculation contains a sealing-boolean bug and K1 was evaluated as replacement rather than monotonic `K0 + K1`, so V88 is **promising mixed evidence only**, not a pass.

Manual audit strengthens the distinction: `bucketsort`'s independent human repair really is a `Call.args` name change (`enumerate(arr)` -> `enumerate(counts)`), while `depth_first_search`'s human repair adds `nodesvisited.add(node)` and therefore the V88 test-passing mutation is likely test-suite overfit.

## V89 — fresh-split contextual confirmation

Run `31786710386`, artifact `9213865127`, SHA-256 `79874f34040f87d4af7141e778b5b3076614c2ee92ab2bc4c7a650a5de5cf373`.

V89 fixes the V88 methodology by using a fresh hash split, monotonic `K0 + learned context`, a correctly encoded sealed-test condition, and a matched context-shuffle null.

Result:

- K0 solves `knapsack`, `quicksort`;
- K0 + learned context solves exactly the same two;
- shuffled context solves exactly the same two;
- new closure = empty.

Verdict: `MIXED_CONTEXTUAL_CONSTRUCTOR_CONFIRMATION_V89`.

Conclusion: the V88 local contextual signal does **not** replicate. `(parent AST node, field, edit kind)` is not currently supported as a stable natural constructor ontology.

## V90 — protected human-fix confirmation

Status: primary CI running. Another fresh split commits candidate patches and hashes before opening held-out human fixes. Protected evaluation then asks whether any new test-suite closure agrees exactly at the AST level with the independently authored repair. This is designed to reject DFS-style test overfit.

## V91 — verifier-induced site ontology

Status: primary CI running. This is the first step after the human-fix representation ladder. Correct implementations are never read. Generic typed perturbations on training tasks are scored only by changes in externally verified failing-test counts. Operational site roles `(kind, parent, field)` with repeated positive verifier gradients are frozen, then tested on held-out repair search against matched shuffled roles.

This is the natural-world analogue of the earlier verifier-induced ontology work: the verifier, not the human fix syntax, supplies the distinctions used to construct the candidate site/type system.

## Current inference

Natural evidence has progressively rejected increasingly shallow representations:

`recurring token patch`
`!= developmental primitive`

`flat one-token schema set`
`!= useful natural lattice`

`hand-named AST mutation family`
`!= supported constructor ontology`

`exact edit template from human fixes`
`!= transferable constructor grammar`

`local AST contextual role`
`!= stable transferable constructor ontology`

The live hypothesis has therefore moved one level deeper: useful constructor structure may be **operational/verifier-induced** or based on nonlocal dataflow/control-purpose relations rather than local syntax, AST type, or parent/field context.

A positive verifier-induced bridge would still not be autonomous constructor growth. The crown-jewel step remains: from frozen verifier residuals alone, construct a new representation/constructor K1 that strictly expands natural held-out closure and makes later K2 discoverable, with ancestor ablations moving the developmental frontier backward.
