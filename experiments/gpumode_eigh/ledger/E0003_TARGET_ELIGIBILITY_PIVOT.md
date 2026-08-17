# E0003 — Active-target eligibility pivot

## Observation
E0002 removed the source-level preflight trigger and exposed the next external obstruction: GPU MODE reports that the `eigh` submission deadline was 2026-07-15. Therefore `eigh` is not an active public frontier and is invalid for the original post-Lean objective.

This is decision-changing evidence. The earlier target selection is revoked rather than defended.

## Interface fact
GPU MODE's current Popcorn documentation states that the PMPP_v2 problem set is kept open for beginners. We therefore use the always-open PMPP set only as an immediate control-plane and frontier-loop qualification target while continuing to search for a higher-impact active competition.

## Selected target
`matmul_v2` on A100, corresponding to `problems/pmpp_v2/matmul_py`. The official task uses FP16 matrix multiplication and eight benchmark shapes from 128^3 through 4096 x 5120 x 4096.

## Hypotheses
H1 — `matmul_v2` is currently submission-eligible through the authenticated Popcorn path.
H2 — the PMPP documentation is stale or this exact board is not currently eligible.

## Smallest separator
Submit a conventional all-Triton blocked FP16 matrix multiplication in test mode. This simultaneously tests board eligibility, compilation, current evaluator compatibility, and correctness.

## Prediction
A passing or ordinary numerical/compilation result confirms the execution loop. A deadline/not-found result rejects this target immediately. A source-policy result is classified separately and does not update kernel semantics.

## Promotion rule
Only after a full correctness pass do we benchmark. No leaderboard submission before an unranked benchmark exists.
