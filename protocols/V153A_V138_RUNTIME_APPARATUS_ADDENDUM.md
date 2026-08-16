# V153A — V138 runtime apparatus addendum

Frozen: 2026-08-16 NZST, after V153 run 31944332864 collected zero natural rows.

V153's first diagnostic run is apparatus-invalid. It used Python 3.11 without the original V138 workflow dependencies. The original V138 workflow used Python 3.12 and installed `pytest pytest-timeout`. V153 therefore observed 17 baseline verifier failures, produced 0 programs/0 sites, and incorrectly reached its corpus-ceiling branch. No V153 O3 support conclusion is licensed from that run.

V153A changes only runtime/apparatus fidelity:

- Python 3.12, matching V138;
- install `pytest pytest-timeout`, matching V138;
- require exact replay of V138's already-frozen corpus facts before any V153 diagnostic classification: 17 programs, 24 sites, 281 verifier calls, 8 `RELAX_SAFE`, 16 `RELAX_SENSITIVE`, and the exact QuixBugs commit.

If any replay identity differs, V153A is `R10_V138_REPLAY_IDENTITY_MISMATCH`.

No V153 scientific diagnostic parameter changes: same SHA(program)-ordered consecutive pairing, same labels, features, rule language, training selection, balanced-accuracy metric, >=8 evaluable paired-fold gate, and claim boundary.