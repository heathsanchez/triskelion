# DEVELOPMENTAL IR V6 — pre-outcome workload addendum

Status: **FROZEN BEFORE IMPLEMENTATION OR OUTCOME EXECUTION**

This addendum fixes workload sampling details omitted from the main precommit. No gate or threshold is changed.

## Rank weights

Within each hidden operator pool, operators retain their deterministic pool order and are sampled with integerized Zipf-like rank weights:

- arity 2: (w_i propto 1/(i+1)^{1.10})
- arity 3: (w_i propto 1/(i+1)^{1.15})
- arity 4: (w_i propto 1/(i+1)^{1.20})

Sampling uses only SHA256-derived integers and these frozen cumulative weights.

## Epoch arity mixtures

For non-root internal nodes:

- Epoch A: 100% arity 2.
- Epoch B: 35% arity 2, 65% arity 3.
- Epoch C: 15% arity 2, 30% arity 3, 55% arity 4.
- Frozen transfer: 20% arity 2, 35% arity 3, 45% arity 4.

Every task root is internal.

## Tree shapes

Epochs A-C use depth 2-4 trees with deterministic early-leaf decisions below the root.

Frozen transfer uses strongly unbalanced trees. Root arity cycles deterministically through 2,3,4 so all three grammar arities are exercised. At least one root argument is itself a computed subtree; other arguments are selected by the same frozen SHA256 stream and may repeat variables.

This guarantees only computational structure, not any favorable operator identity.
