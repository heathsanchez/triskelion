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

`LATEST_UPSTREAM_BEFORE_INVENTION`: required closure gate, unresolved.
