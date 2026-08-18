# V165 — Semantic Scope Requalification

## Why this exists

V163 showed a causal effect of the frozen semantic capability manifest on `thefuck/32`, but the frozen capability's own applicability statement is specifically about structured parsing failures caused by escaped separators. Its executable scope was only `{field: source, contains: "re."}`. That operational scope is far broader than the semantic preconditions. V164 then admitted the capability on `keras/32`, where every arm followed a collections-compatibility path while the native failures concerned `ReduceLROnPlateau`; the separator-parsing law did not engage.

Therefore V163 is retained as evidence that semantic manifest content can causally alter search, but is not sufficient by itself to establish lawful in-scope capability qualification. V164 is retained as a valid negative under the old scope rule, but not as the definitive developmental-compounding test.

V165 repairs the admission criterion before any further developmental claim.

## Frozen capability semantics

The capability artifact is unchanged: `cp3_frozen/acquisition/CAPABILITY.json`.

Required semantic ingredients are taken directly from its already-frozen preconditions/postconditions/applicability text:

1. structured-data parsing or extraction;
2. a separator/delimiter/splitting/matching operation;
3. escaped/quoted/protected separator behavior, or an equivalent boundary error in which a separator is incorrectly treated as active inside protected syntax.

The repair law itself is not changed.

## Phase A — zero-model semantic eligibility census

Before any model call, scan the frozen BugsInPy candidate stream using only visible baseline failure output and visible source context. A case is `SEMANTICALLY_ELIGIBLE` only if the evidence supports all three ingredients above. Merely containing regex syntax, `re.`, or string-splitting code is insufficient.

The census must record the evidence snippets and hashes for every eligible case. Case selection is the first eligible case in the already-frozen deterministic corpus order. No result-dependent reselection is permitted.

If no semantically eligible natural case exists, verdict is `OBSTRUCTED_V165_NO_LAWFUL_NATURAL_SCOPE_FRONTIER`; do not spend model calls and do not widen the scope.

## Phase B — qualification, only if Phase A finds a case

Use the same model/seeds/exact native verifier/persistent workspace/source synchronization as V163, with no hand-specified locus and no binding hint.

Arms:
1. `SEMANTIC_CAPABILITY`
2. `OPAQUE_MATCHED`
3. `COLD`
4. `RAW`
5. `RAG`

Primary endpoint: native verified solve within three calls.

`PASS_V165_LAWFUL_CAPABILITY_REQUALIFIED` iff the semantic arm solves at least 2/3 and strictly beats all controls.

Any causal effect outside Phase-A semantic eligibility cannot count as capability qualification.

## Admission rule going forward

A capability may enter developmental state for a downstream test only when both are true:

- its operational scope matches a prospectively auditable semantic eligibility rule derived from the frozen capability semantics; and
- it passes causal qualification against matched alternatives on an eligible case.

This rule supersedes the coarse `source contains re.` admission rule for developmental claims. Historical V159–V164 artifacts are not deleted or rewritten; their claim boundaries are narrowed accordingly.
