# Lean Kernel Arena — LEVEL_EQ_CACHE

## Status

Candidate formed, not promoted. Protected execution is blocked by the current hosted Actions admission failure.

## Frozen substrate

- `intgrah/sokonanoda`
- revision `0fab8874080e379a774a9a27f7538d8a1ddd786b`
- protected downloadable Arena suite artifact `8931227426`

## Obstruction

Sokonanoda currently computes universe-level definitional equality as:

```rust
pub fn eq_antisymm(&mut self, l: LevelPtr<'t>, r: LevelPtr<'t>) -> bool {
    l == r || (self.leq(l, r) && self.leq(r, l))
}
```

For non-identical pointers, repeated comparisons recompute two recursive `leq` traversals. This function is used pervasively inside conversion, including rigid-head universe comparisons.

The independently optimized sibling `zignodamus` stores a symmetric pair cache around the same final predicate.

## Candidate operator

\[
\boxed{
(l,r)\xrightarrow{\text{first equality decision}}b
\rightarrow
\{l,r\}\mapsto b
\rightarrow
\text{reuse on later comparisons}
}
\]

Name: `LEVEL_EQ_CACHE`.

Key is canonicalized by pointer order so `(l,r)` and `(r,l)` share one entry.

## Scope / lifetime

In sokonanoda the per-thread `TcCtx` and its local DAG outlive individual value sessions. Local `LevelPtr`s therefore remain valid across `SessionBump` resets. The cache should live with `TcCtx::expr_cache`, not with value-level `TcCache`.

The cache must be cleared/dropped with `TcCtx`; session-boundary capacity policy is an independent variable and should not be silently coupled into the first test.

## Independent second candidate

Sokonanoda's `unify_spine` already has pointer-equality fast exit but lacks the cheap length mismatch exit present in zignodamus. Since every `Spine::Snoc` stores `len`, add:

```rust
if sx.len() != sy.len() {
    return false;
}
```

after the pointer-equality check.

Name: `SPINE_LENGTH_OBSTRUCTION`.

## Causal arms

1. `base`
2. `levelcache`
3. `spinelen`
4. `combo` = `levelcache + spinelen`

Every arm must pass 161/161 before timing is interpreted.

## Why this is high priority

Callgrind previously put `unify_general / unify_no_cache` around ~70% of the hot dynamic path. `LEVEL_EQ_CACHE` sits below many rigid-head conversion comparisons, so unlike recursor-only micro-optimizations it can affect a broad fraction of the dominant path.

## Lawbook status

- `LEVEL_EQ_CACHE`: candidate, unverified.
- `SPINE_LENGTH_OBSTRUCTION`: candidate, unverified.
