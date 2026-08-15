# E0011 — Canonical inference-key quotient / L0 cache

Status: PRECOMMITTED DIAGNOSTIC

Objective: test whether caching at the already-canonical `(key_env(env,e), e)` equivalence-class key reduces inference cost without changing semantics.

Scientific rule: canonicalize first, then cache. This experiment must not use the rejected raw pre-canonical key path.

Frozen implementation source: existing `agent/lean-kernel-arena-canonical-type-l0` workflow, which sweeps direct-mapped capacities 64, 256, 1024, 4096 in front of the existing canonical type cache.

Current execution note: this branch is based on the historical pinned sokonanoda substrate `0fab8874080e379a774a9a27f7538d8a1ddd786b`. Results are diagnostic unless independently rebased onto the current admitted A1 frontier. Do not promote to A2 solely from this run if A1 differs.

Gates:
1. all variants preserve the 178-file downloadable semantic corpus;
2. compare randomized repeated workload medians;
3. reject any capacity that regresses semantics;
4. treat local wall time as screening evidence only;
5. any winning capacity must be rerun on exact paired Mathlib from the current admitted frontier before admission.

Decision discipline: no tuning after result inspection; preserve negative results.
