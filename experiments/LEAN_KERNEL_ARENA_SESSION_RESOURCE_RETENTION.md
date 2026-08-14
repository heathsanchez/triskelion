# Lean Kernel Arena — SESSION_RESOURCE_RETENTION

## Status

Candidate formed, not promoted. Hosted GitHub Actions is currently rejecting new jobs before runner assignment, so no protected runtime result exists yet.

## Frozen substrate

- checker: `intgrah/sokonanoda`
- revision: `0fab8874080e379a774a9a27f7538d8a1ddd786b`
- Arena downloadable suite artifact: `8931227426`
- correctness gate: 161/161 downloadable Arena cases

## Obstruction

Sokonanoda divides checking into sessions. At a session boundary it currently forgets reusable resource shape in multiple places.

### 1. Hot table capacity is discarded

`shrink_map` and `shrink_set` replace any table whose capacity exceeds `KEEP_CAP = 1 << 15` with a fresh empty table:

```rust
pub(crate) const KEEP_CAP: usize = 1 << 15;

fn shrink_map<K, V>(m: &mut FxHashMap<K, V>) {
    if m.capacity() > KEEP_CAP {
        *m = FxHashMap::default();
    } else {
        m.clear();
    }
}
```

The same policy reaches `TcCache` and `ExprCache` tables, including inference/evaluation/hash-consing/substitution caches.

### 2. Session bump capacity is discarded

Current code:

```rust
pub(crate) fn reset(&mut self) {
    self.inner = bumpalo::Bump::new()
}
```

This reconstructs the bump allocator rather than resetting it for reuse.

### 3. Session budget ignores concurrency

Sokonanoda uses a fixed per-thread budget:

```rust
const SESSION_BUDGET: usize = 1 << 20;
```

Current zignodamus instead scopes session lifetime to both per-thread and whole-machine memory pressure:

```text
per_thread_budget = 6 MiB
machine_budget    = 10 MiB
session_budget    = min(per_thread_budget, machine_budget / num_threads)
```

At four threads this is about 2.5 MiB per session; at two threads it is 5 MiB. Therefore a fixed 1 MiB session is not merely a smaller tuning constant; it ignores concurrency as an applicability condition.

## Independent precedent

The independently optimized sibling `zignodamus` contains a session recycle path that:

- clears caches while retaining capacity,
- clears local DAG state,
- resets its arena for reuse.

A later zignodamus tuning also added a `rebuild_cap` field to custom maps/interners so a table that must be deallocated still remembers the capacity it will need on its next build.

This is evidence for candidate operators, not evidence that the Rust implementation will improve.

## Candidate laws

### SESSION_RESOURCE_RETENTION

\[
\boxed{
\text{resource demand observed in session }t
\rightarrow
\text{retain enough shape for session }t+1
}
\]

Values/results may be cleared at a trust/lifetime boundary while *capacity information* is retained.

### CONCURRENCY_SCOPED_SESSION_BUDGET

\[
\boxed{
B(n)=\min(B_{thread}, B_{machine}/n)
}
\]

Session lifetime is a scoped law of available machine budget and thread count, not a universal constant.

## Causal decomposition

Precommit the following sequence rather than one opaque composite:

1. `base` — frozen sokonanoda.
2. `arena` — reset/reuse session bump only.
3. `tables` — retain large hash-table capacity only.
4. `both` — arena + tables.
5. `budget` — concurrency-scoped budget only.
6. `retention+budget` — arena + tables + concurrency-scoped budget.

Do not combine with PGO, chunk-size, constructor-fastpath, carry-iota-args, or canonical-type-L0 until these session operators are measured independently.

## Minimal patches

### Arena-only

Target:

```rust
impl SessionBump {
    pub(crate) fn reset(&mut self) {
        self.inner.reset();
    }
}
```

Use the pinned `bumpalo 3.16` API; compilation is part of the gate.

### Tables-only first test

The simplest causal probe is to retain capacity unconditionally:

```rust
fn shrink_map<K, V>(m: &mut FxHashMap<K, V>) {
    m.clear();
}

fn shrink_set<K>(s: &mut FxHashSet<K>) {
    s.clear();
}
```

This intentionally tests the performance effect before engineering a bounded/lazy rebuild policy. Peak memory must be recorded because a speed gain that violates Arena memory constraints is not admissible.

### Budget-only

First reproduce the sibling policy structurally rather than copying one fixed value:

```rust
const PER_THREAD_BUDGET: usize = 6 << 20;
const MACHINE_BUDGET: usize = 10 << 20;

fn session_budget(num_threads: usize) -> usize {
    PER_THREAD_BUDGET.min(MACHINE_BUDGET / num_threads.max(1))
}
```

Pass the resolved budget into the session loop. Treat the exact 6/10 MiB constants as candidate scope, not a law.

## Required gates

- all arms compile;
- 161/161 correctness for every arm;
- no new declines;
- same frozen timing workload and randomized arm order;
- record peak RSS for each arm;
- record number of session resets for each arm;
- run at both 2 and 4 checker threads so the concurrency law is actually exercised;
- if the small proxy is neutral, do not reject immediately: this candidate is explicitly session-count-sensitive and requires exact Mathlib A/B before final rejection;
- only promote a suboperator if causal ablation removes its measured gain.

## Why this is higher priority than another micro-cache

Earlier proxy tests found only weak gains from increasing the fixed session budget from 1 MiB to 2 MiB, but that changed only *session frequency*. It did not repair resource forgetting at the boundary and did not test a concurrency-scoped budget. Full Mathlib contains far more declarations/sessions than the 24-case proxy, so repeated table growth and allocator reconstruction can compound while remaining nearly invisible on short workloads.

## Current lawbook status

- `SESSION_RESOURCE_RETENTION`: candidate, unverified.
- `ARENA_REUSE_ACROSS_SESSION`: candidate suboperator.
- `TABLE_CAPACITY_RETENTION`: candidate suboperator.
- `CONCURRENCY_SCOPED_SESSION_BUDGET`: candidate suboperator.
- No performance claim until external execution resumes.
