# V124 — Ix natural binder held-out qualification result

**Status:** `CORPUS_CEILING_NO_IX_BINDER_TARGET`

## Frozen candidate

`argumentcomputer/ix@6e10865ce0750523917b4b1adf5a833dd6d93a8f`

Qualification file: `Ix/Tc/Verify/NatFixture.lean`

## Post-precommit inspection

The pinned source is explicitly a small ambient-Nat **fixture**, not a pre-existing natural application target for the V120 binder-role capability. It constructs a closed Theory model of `Nat`, `Nat.zero`, and `Nat.succ` and states that it is deliberately an ambient model used to exercise verification boundaries.

Although the imported Ix project contains genuine typing judgments, this selected file does not itself provide the frozen qualifying target: an independently authored natural relation/checker producing a value in a value-parameterized inductive family whose constructor reconstruction exhibits the V120 implicit-uniform-parameter distinction.

## Verdict

Do not stretch the eligibility rule merely because Ix is a sophisticated formal project. Under the frozen V124 rule this selected candidate is a corpus ceiling.

`CORPUS_CEILING_NO_IX_BINDER_TARGET`

This is not evidence against K2.
