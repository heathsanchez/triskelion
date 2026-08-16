# GPU MODE `eigh` — Rigorous transfer experiment

## Target

Public GPU MODE `eigh` leaderboard on NVIDIA B200.

## Objective

Reach the frontier while preserving a prospective causal record of how each retained optimization was discovered.

Primary scientific question: can the same verifier-governed controller used in Lean Kernel Arena discover and compound GPU optimization structure under a hard external evaluator?

## Frozen baseline

Upstream baseline:

```python
values, vectors = torch.linalg.eigh(data)
return vectors, values
```

The official task accepts a single Python submission implementing `custom_kernel`. Correctness is invariant-based: eigen-equation, reconstruction, orthogonality, and ascending eigenvalues. Ranking among passing submissions is by geometric-mean runtime on B200 benchmark cases.

## Trust boundary

GPU MODE execution is authoritative for correctness and leaderboard timing. Local reasoning and profiling generate hypotheses only.

Cheap to propose; expensive to believe.

## Experiment rule

Before each semantic optimization, record:

1. Observation / residual.
2. Hypothesis.
3. Strongest rival explanation.
4. Smallest separating intervention.
5. Prospective prediction.
6. Kill criterion.

One conceptual intervention per experiment until evidence licenses composition.

## Modes

`EXPERIMENT_MODE` controls CI:

- `test` — correctness gate; default on ordinary commits.
- `benchmark` — unranked official B200 timing.
- `leaderboard` — ranked submission; use only for frozen candidates.

## Initial residual classes

Do not assume these are correct; execution decides.

- R2 COST — general eigensolver work may exceed what some input regimes require.
- R3 REDUNDANCY — repeated work may be removable or reusable.
- R4 OBSERVABILITY — profitable structure may exist but not be exposed cheaply enough for routing.
- R5 APPLICABILITY — specialized paths may help only on identifiable regimes.
- R6 REPRESENTATION — the implementation may need a different algorithmic coordinate system rather than more tuning of `torch.linalg.eigh`.
- R9 SOUNDNESS — any speed gain that violates the invariant checker is rejected.
- R10 INFRASTRUCTURE — runner/auth/service failures do not update semantic hypotheses.

## Initial strategy

1. Reproduce the baseline on official B200.
2. Obtain benchmark-shape timings and, where useful, hosted Nsight Compute profiles.
3. Locate the dominant residual rather than writing CUDA immediately.
4. Test routing/specialization only if recognition overhead and hidden-case robustness can be justified by evidence.
5. Retain only externally verified gains.
6. After each retained gain, re-profile: the next residual may differ from the previous one.

## Evidence ledger

Each experiment gets `E####` and a markdown record under `experiments/gpumode_eigh/ledger/` before its intervention is benchmarked.

No leaderboard result may retroactively edit a prospective prediction.
