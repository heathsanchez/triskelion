# E0001 — Stream-policy separator

## Observation / residual
The frozen upstream `torch.linalg.eigh` baseline is rejected by GPU MODE before task execution with: `Your code contains work on another stream.` Authentication, workflow dispatch, leaderboard selection, B200 selection, and submission transport all succeeded.

Primary classification: R10 infrastructure / evaluator-policy mismatch. No semantic inference about eigendecomposition performance is licensed.

## Hypotheses
H1 — the current hosted preflight rejects the PyTorch dense eigensolver because it performs GPU work outside the evaluator's permitted current stream.

H2 — the rejection is broader and our GitHub/Popcorn submission path itself is incompatible with this leaderboard.

## Smallest separating intervention
Replace the dense eigensolver with an all-Triton, current-launch-stream diagonal eigendecomposition. It is intentionally incomplete for general matrices. Its purpose is only to determine whether a plain Triton submission reaches the actual correctness verifier rather than the stream-policy rejection.

## Prospective prediction
If H1 is correct, the submission will pass preflight and then fail some non-diagonal correctness cases (while diagonal/identity-like cases may pass). That is a useful PASS for the infrastructure separator even though task correctness as a whole fails.

If the same stream-policy error appears, H1 is weakened and we must inspect the submission-policy boundary rather than continue algorithm work.

## Kill criterion
Do not promote this implementation as a capability. It is a diagnostic only. No leaderboard or performance claim may be made from E0001.
