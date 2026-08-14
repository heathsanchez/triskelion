# Natural Constructor Frontier

_Last updated 2026-08-14 NZST — through V86; V87/V88 running._

This file tracks the natural-world constructor-language programme separately from bounded authored calibrations. The external corpus is QuixBugs at commit `4257f44b0ff1181dedaedee6a447e133219fcebf`, a pre-existing program-repair benchmark. Correct implementations are treated according to each experiment's explicit train/test sealing rule.

## Core question

`K_t -> Expressible(K_t) -> Cl(A_t)`

A claim about an irreducible operator is only meaningful relative to the constructor language `K_t`. The current programme therefore asks which representation of candidate transformations is actually supported by external experience.

## V83 — one-token natural IVAG census

Verdict: `MIXED_NATURAL_IVAG_V83`.

Two minimum repair schemas recur across independent curricula, but the frozen held-out closure remains `0 -> 0 -> 0`. V84 later shows that one apparent syntactic convergence was an equal-MDL tie. Conclusion: recurrence/minimality alone does not make a developmental primitive.

## V84 — observational quotient/lattice

Run `31782263023`, artifact `9212227436`, SHA-256 `96a1be28ae8cefd478f6935c2f8461dbbc8d8209557e58472706468e20481969`.

Across 37 initially failing programs, the complete frozen 26-schema one-token constructor reaches only two tasks. Nonempty extensional classes:

- `{<= -> <}` -> `find_first_in_sorted`
- `{< -> <=, > -> >=}` -> `quicksort`

No nontrivial inclusion/Hasse structure and no schema reaches multiple distinct tasks. Conclusion: the observational algebra under K0 is too impoverished; quotient by verified behavior, not syntax.

## V85 — verifier-selected generic AST families

Run `31782743901`, artifact `9212772996`, SHA-256 `8d2aa8bacc9903520c6b1083fde4557e2fba5f9e1ec91ad21e7e183c3c1f808d`.

Eleven supplied AST mutation families are tested using training verifier support only; correct implementations are never read. Ten receive zero support and `CALL_ARG_SWAP` receives support on one training task, below the frozen threshold of two. No K1 is admitted and held-out closure does not expand.

Conclusion: the hand-specified AST family vocabulary is not empirically justified as the constructor ontology.

## V86 — exact edit grammar induced from external successful repairs

Run `31784429088`, artifact `9213041932`, SHA-256 `436f6ab82d19719f3d6505ebe284124229fb370fa2dc5a4ea038e9c753d2adfa`.

Human fixes are read only on a frozen training half; held-out correct implementations remain sealed. Fourteen exact one-token edit templates are induced automatically. They solve `quicksort` on held-out data but create zero new closure beyond K0. A rotated wrong-pair control solves none.

Verdict: `MIXED_PATCH_INDUCED_CONSTRUCTOR_V86`.

Conclusion: successful external experience does contain real edit information, but exact token templates are too specific to form a transferable constructor language.

## V87 — structural edit-schema induction

Status: primary CI running. Training-side external fixes induce abstract AST change kinds; held-out correct implementations remain sealed. This tests whether edit *kind* transfers beyond exact syntax.

## V88 — contextual edit-role induction

Status: primary CI running. Training-side external fixes induce `(parent node, field, change kind)` roles; held-out correct implementations remain sealed. Context-shuffled roles are the null. This tests whether transferable constructor structure is relational/context-indexed.

## Current inference

The natural evidence has progressively rejected increasingly shallow representations:

`recurring token patch`
`!= developmental primitive`

`flat one-token schema set`
`!= useful natural lattice`

`hand-named AST mutation family`
`!= supported constructor ontology`

`exact edit template from human fixes`
`!= transferable constructor grammar`

The current live hypothesis is that useful constructor structure may reside in **relational/program-role representations** rather than surface syntax or node type alone. V87 and V88 are designed to separate those possibilities.

A positive supervised bridge is still not autonomous constructor growth. If a transferable representation is found, the next crown-jewel step is to reconstruct that representation from verifier residuals alone on a fresh sealed stream.
