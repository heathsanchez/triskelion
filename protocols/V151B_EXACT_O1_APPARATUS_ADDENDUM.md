# V151B — Exact-O1 apparatus addendum

## Status

**PRECOMMITTED APPARATUS REPAIR AFTER V151 R10, BEFORE ANY V151B MODEL OUTCOME**

The first V151 run terminated `R10_INCONCLUSIVE` before any model call because the runner's literal reconstruction of the already-frozen V149 O1 contained paraphrased preconditions/postconditions/applicability text. Its self-hash correctly rejected that object before scientific execution.

V151B changes exactly one apparatus fact: bind the compiled arm to the exact O1 object recovered from the immutable V149 `V145_RESULT.json`, whose artifact SHA-256 is:

`7ebb7fb26da6d137c13c1a08bafd7e540dbd52f25e04cf4298502e5ce5428546`

The exact source intervention SHA-256 remains:

`b7f419e7993e92164969b7a99689f01dfa279ce2d1615e25fce0bb21486f472d`

No task, model, seed, budget, context adapter, output protocol, verifier, arm, raw-memory object, sham construction, stopping rule, classification rule, or claim boundary changes from V151.

The prior V151 R10 record remains immutable and is not overwritten. V151B receives a separate run identity.

This final metadata-only commit is intentionally made after the workflow file exists so the frozen apparatus receives a push-triggered Actions execution. It changes no scientific parameter.
