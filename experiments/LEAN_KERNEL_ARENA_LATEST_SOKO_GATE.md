# Lean Kernel Arena — latest sokonanoda closure gate

## Status

Precommitted, not executed. Hosted Actions is currently rejecting new jobs before runner assignment.

## Question

Before inventing or composing further performance operators, test whether the published Arena-pinned sokonanoda revision is already obsolete relative to current upstream.

## Revisions

Published substrate used by our prior experiments:

- `0fab8874080e379a774a9a27f7538d8a1ddd786b` — `Smallvec`

Current upstream tip observed after it:

- `9b4ea12f4cd437d00b6bcd0e34743065c58dea08` — `eagerness in some places`

## Why this is a real closure gate

`9b4ea12` is not a cosmetic commit. It changes the effective optimization language in at least three ways:

1. Removes the hashed thunk-construction path in ordinary evaluation/inference and evaluates arguments/binder domains eagerly.
2. Adds an `ignores_binder` predicate using loose-bvar count + free-variable mask.
3. Extends relevance signatures with `absent_arg`, allowing conversion to skip arguments that are absent from a definition's value and safely ignored by the remaining type, not only arguments known to be proofs.

This means optimizing only `0fab887` risks rediscovering or working around a capability that already exists upstream.

## Exact static applicability audit

The immutable 161-case Arena artifact was materialized locally and analyzed by reproducing sokonanoda's exact structural metadata equations:

- `Var(i)`: loose-bvar count `i+1`, mask `1<<i` when `i<64`;
- `App`: max child loose-bvar count and OR of child masks;
- `Lambda/Pi`: max(domain count, body count - 1), domain mask OR body mask shifted right by one;
- `Let`: same binder shift plus type/value masks;
- `Proj`: inherits structure metadata.

The `absent_args` algorithm was then replayed exactly over exported definitions.

### Structural irrelevance / `absent_arg`

Across all 161 files:

- expressions: **277,391**
- definitions: **2,684**
- definitions with leading lambdas: **2,393**
- leading lambda parameters: **9,725**
- definitions with at least one `absent_arg`: **120**
- absent parameter positions: **120**
- absent fraction of leading lambda parameters: **1.23%**
- unique exported constant-application sites exposing such an argument position: **48**

On the frozen 24 largest files:

- leading lambda parameters: **9,558**
- absent parameter positions: **108** (**1.13%**)
- exposed constant-application argument positions: **34**

On `good/perf/grind-ring-5.ndjson` specifically:

- definitions: **891**
- leading lambda parameters: **2,989**
- absent parameter positions: **8** (**0.27%**)
- exposed constant-application positions: **15**

On `good/init-prelude.ndjson`:

- definitions: **1,479**
- leading lambda parameters: **6,210**
- absent parameter positions: **100** (**1.61%**)
- exposed constant-application positions: **19**

Interpretation: `absent_arg` is a real generalization of proof irrelevance, but it is too sparse in the frozen performance corpus to assume it explains a large runtime shift by itself.

### Eagerness / thunk-elimination opportunity

The other half of `9b4ea12` has far broader static reach. Under the pinned evaluator, nontrivial application arguments are candidates for hash-consed thunk construction; the new commit evaluates them eagerly.

Across all 161 files:

- application nodes: **197,699**
- application nodes with nontrivial arguments: **133,359** (**67.46%**)
- Pi nodes with nontrivial domains: **13,138**
- Lambda nodes with nontrivial domains: **15,967**

Frozen largest 24:

- application nodes: **195,936**
- nontrivial application arguments: **133,115** (**67.94%**)

`grind-ring-5`:

- application nodes: **145,158**
- nontrivial application arguments: **108,282** (**74.60%**)
- Pi nodes with nontrivial domains: **5,872**
- Lambda nodes with nontrivial domains: **7,945**

`init-prelude`:

- application nodes: **30,113**
- nontrivial application arguments: **10,977** (**36.45%**)

`app-lam`:

- application nodes: **16,165**
- nontrivial application arguments: **12,044** (**74.51%**)

This does **not** estimate dynamic execution counts, but it establishes a large static opportunity set. It also aligns with the prior profile where `key_env` was a material hotspot: the old thunk-hash-cons path canonicalizes environments before constructing reusable thunks, whereas `9b4ea12` removes that path from ordinary evaluation/inference.

### Cleanup consequence

Current `TcCache` still contains, allocates and clears a `thunk_hc` map even though `9b4ea12` removes the ordinary `mk_thunk_hc` producer from `eval`/`infer`. Treat removal of any now-dead thunk cache state as a separate cleanup candidate only after verifying there are no remaining producers elsewhere; do not confuse this small cleanup with the main eager-evaluation effect.

## Gate

A/B exactly:

- `pinned` = `0fab887...`
- `latest` = `9b4ea12...`

Required:

- both compile under the same flags;
- both run the same 161 downloadable Arena cases;
- latest must remain 161/161 with no new declines;
- same frozen 24-case timing workload, randomized arm order;
- record peak RSS;
- do not compose our local candidates until this gate is known.

## Decision rule

- If `latest` is faster and sound on the protected suite, promote it as the new performance substrate and rebase candidate experiments conceptually onto it.
- If neutral/slower, retain the published pinned substrate.
- If any correctness regression appears, do not use the upstream commit as substrate regardless of speed.

## Current lawbook status

- `LATEST_UPSTREAM_BEFORE_INVENTION`: required closure gate, unresolved.
- `STRUCTURAL_IRRELEVANCE`: present in latest upstream; applicability verified statically; runtime effect unresolved.
- `EAGER_ARGUMENT_EVALUATION`: present in latest upstream; broad static applicability verified; runtime/soundness gate unresolved.
