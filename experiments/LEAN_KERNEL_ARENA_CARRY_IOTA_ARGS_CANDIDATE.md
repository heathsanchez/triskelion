# Lean Kernel Arena — carried iota arguments candidate

## Status

Candidate formed, **not promoted**. Hosted GitHub Actions currently rejects new jobs before runner assignment (`runner_id=0`, zero steps), so the protected correctness/timing gate has not executed.

## Frozen substrate

- Checker: `intgrah/sokonanoda`
- Revision: `0fab8874080e379a774a9a27f7538d8a1ddd786b`
- Arena downloadable suite artifact: `8931227426`
- Correctness gate: all 161 downloadable Arena cases
- Timing gate: frozen 24 largest cases, hash-ordered, balanced randomized arm order

## Residual

Prior profiling narrowed remaining iota work to successful first-time recursor reduction. The iterative `force_all` path extracts a `SpineArgs` vector in `iota_step`, but when a reducible nested major is encountered, sokonanoda retains only the recursor value:

```rust
enum ForceStep<'a> {
    Reduced(V<'a>),
    Descend(V<'a>),
    Done,
}
```

and later reconstructs the recursor arguments in `fire_value` by calling `spine_apps` again.

The independently optimized sibling `zignodamus` instead carries the already-extracted arguments through descent and reuses them on unwind.

## Candidate operator

\[
\boxed{\text{EXTRACT\_ONCE} \rightarrow \text{CARRY\_THROUGH\_DESCENT} \rightarrow \text{REUSE\_ON\_UNWIND}}
\]

Minimal Rust transformation:

```rust
enum ForceStep<'a> {
    Reduced(V<'a>),
    Descend(V<'a>, SpineArgs<'a>),
    Done,
}
```

The waiting stack changes from:

```rust
Vec<V<'t>>
```

to:

```rust
Vec<(V<'t>, SpineArgs<'t>)>
```

`iota_step` returns the already-built `args` with `Descend`, and `fire_value` consumes the retained slice rather than reconstructing it from the spine.

## Semantic argument

The candidate does not change:

- reduction order,
- the selected recursor,
- the selected major,
- recursor rule choice,
- argument values,
- quotient dispatch,
- iota cache keys.

It only preserves an intermediate value already constructed in the same reduction path. `spine_apps` forces thunks before returning arguments; forcing is memoized, so replay and reuse are intended to be extensionally equivalent. This is a static argument only; external correctness remains mandatory.

## Precommitted causal experiment

Workflow: `.github/workflows/lean-kernel-arena-carry-iota-args.yml`

Arms:

1. `base` — frozen sokonanoda.
2. `carry` — carried iota arguments only.
3. `combo` — carried arguments + previously measured constructor-major fast path.

Required gates:

- all three arms 161/161,
- no accept/reject/decline regressions,
- carry must improve median runtime to be retained as a performance law,
- combo tests compositionality rather than assuming additive gains.

## Infrastructure obstruction

Workflow run `31797274829` attempt 2 was retried after all other in-progress repo workflows had completed. GitHub still created a job with `runner_id=0`, `runner_name=""`, `steps=[]`, then failed it within seconds. Therefore this attempt supplies **no checker result** and must not be counted as a negative experiment.

## Current lawbook state

- `CARRY_IOTA_ARGS`: candidate; unverified.
- Constructor-major fast path: verified on proxy workload, ~0.91% improvement, 161/161.
- Do not promote or compose `CARRY_IOTA_ARGS` into the retained checker until the protected suite executes.
