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

## Independent precedent

The independently optimized sibling `zignodamus` contains a session recycle path that:

- clears caches while retaining capacity,
- clears local DAG state,
- resets its arena for reuse.

A later zignodamus tuning also added a `rebuild_cap` field to custom maps/interners so a table that must be deallocated still remembers the capacity it will need on its next build.

This is evidence for a candidate operator, not evidence that the Rust implementation will improve.

## Candidate law

\[
\boxed{
\text{resource demand observed in session }t
\rightarrow
\text{retain enough shape for session }t+1
}
\]

Name: `SESSION_RESOURCE_RETENTION`.

The principle is deliberately narrower than generic memoization: values/results may be cleared at a trust/lifetime boundary while *capacity information* is retained.

## Causal decomposition

Precommit four arms:

1. `base` — frozen sokonanoda.
2. `arena` — replace session bump reconstruction with reset/reuse only.
3. `tables` — retain large hash-table capacity across session clears only.
4. `both` — arena + tables.

Do not combine with PGO, chunk-size, constructor-fastpath, carry-iota-args, or canonical-type-L0 until these four arms are measured independently.

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

## Required gates

- all four arms compile;
- 161/161 correctness for every arm;
- no new declines;
- same frozen timing workload and randomized arm order;
- record peak RSS for each arm;
- if the small proxy is neutral, do not reject immediately: this candidate is explicitly session-count-sensitive and requires exact Mathlib A/B before final rejection;
- only promote a suboperator if causal ablation removes its measured gain.

## Why this is higher priority than another micro-cache

Earlier proxy tests found only weak gains from increasing session budget, but that changed *session frequency* without repairing the resource-forgetting behavior at the boundary. Full Mathlib contains far more declarations/sessions than the 24-case proxy, so repeated table growth and allocator reconstruction can compound while remaining nearly invisible on short workloads.

## Current lawbook status

- `SESSION_RESOURCE_RETENTION`: candidate, unverified.
- `ARENA_REUSE_ACROSS_SESSION`: candidate suboperator.
- `TABLE_CAPACITY_RETENTION`: candidate suboperator.
- No performance claim until external execution resumes.
