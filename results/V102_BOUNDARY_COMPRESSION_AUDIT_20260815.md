# V102 Boundary Robustness + Compression Audit — exploratory

Date: 2026-08-15 NZST

Status: **MIXED — boundary robustness partially supported; durable compression not established**

Execution note: the audit script was committed as `experiments/V102_BOUNDARY_COMPRESSION_AUDIT.py`. GitHub Actions run `31863873912` failed before any step acquired a runner (`runner_id=0`, `steps=[]`), so this result is **not Actions-attested**. The deterministic audit calculations were executed separately against the attested V51 snapshot and the pinned V101P/V101F results. Do not promote this file to the attested ledger without an independent rerun.

## Question 1 — boundary robustness

Bao's test: if operator granularity or admissible composition changes, does the claimed new operator remain outside the old closure?

### V51 structural boundary lattice

V51 constructed the scoped token rewrite `< -> <=` after an old-closure obstruction. The old generators were `IDENTITY`, `REVERSE_WINDOW`, `ROTATE_LEFT`, `ROTATE_RIGHT`, and `SWAP_ADJACENT`.

All of these are rearrangement operations. Their lawful composition preserves token identity / token multiset. Therefore the obstruction survives the following redescriptions:

1. the original shallow generator set;
2. unbounded lawful composition of the same generators;
3. collapsing all reorder operations into a single coarse arbitrary-permutation primitive;
4. refining the structural basis to adjacent swaps with unbounded composition.

All four still cannot synthesize a new token identity `<=` from `<`.

Positive control: if the effective language is changed semantically to admit token substitution / comparator relabelling, the obstruction disappears by construction. So this is **not** a representation-independent invention claim.

### Independent empirical boundary sensitivity

V101P provides the complementary observation: changing lawful composition depth really can change the verdict. On four held-out natural-code tasks:

- depth 1 reachable: 0/4;
- depth 2 reachable: 1/4;
- `sieve` became reachable by lawful `CMP_OP -> NEGATE_GUARD` composition and therefore ceased to count as a missing-constructor obstruction;
- three tasks remained unreachable under depth 2.

V101F subsequently identified structural closure invariants for those three residuals, but that audit is explicitly post-hoc/nonclaim and requires a fresh split.

### Boundary verdict

**PASS_PARTIAL_BOUNDARY_ROBUSTNESS**

The obstruction is robust to substantial changes of granularity and composition depth **within the same structural/reordering semantic class**, and the method demonstrably withdraws an obstruction when a richer lawful composition actually solves it. It is still dependent on the semantic boundary: adding substitution makes the V51 operator ordinary old-language behavior.

## Question 2 — compression vs displaced complexity

Bao's test: does the new operator unify a class at lower total cost after charging its definition and activation condition, rather than moving complexity into the operator/scope?

### Description-length audit

The normalized governed package was charged as:

`operator = replace_token(<, <=)` plus `scope = ancestor_kind(if)`.

One-off controls used short case IDs rather than long source paths, deliberately making the baseline hard to beat.

| Encoding | operator + scope | 2 training one-offs | 3 positive one-offs incl. sealed transfer |
|---|---:|---:|---:|
| canonical JSON bytes | 90 | 83 | 131 |
| zlib-9 bytes | 82 | 57 | 74 |

Result: the apparent description saving is **encoding-sensitive**. Raw canonical length favors the reusable operator by the third positive case; compressed length still favors the repetitive one-off table. Under the same normalization, zlib break-even occurs only around ten similarly structured cases. Therefore the current three-positive-case evidence does not establish encoding-robust description compression.

### Search-cost signal

V51 exposed 42 constructor destinations. A simple candidate-menu proxy therefore favors warm reuse over reconstructing a repair each time, but this is only a search-menu proxy, not a measured runtime ratio. It cannot substitute for an explicit prospective cost ledger.

### Full governed-class test

The decisive result is stronger and negative. V51's later counterexample:

- fell **inside** the learned scope;
- had no admissible refined-scope candidate;
- forced the ratchet decision `REVOKE`.

So once activation/scope validity is charged over the full observed evidence class, the V51 operator is not a durable compressed abstraction. The experiment correctly withdraws it.

### Compression verdict

**FAIL_DURABLE_COMPRESSION_V51_REVOKED / ENCODING-SENSITIVE_ON_POSITIVE_SUBSET**

There is evidence of reusable search economy on the helpful subset, but Bao's stronger compression-vs-displacement falsification is **not closed** by V51.

## Joint conclusion

**MIXED_BOUNDARY_PARTIAL_COMPRESSION_NOT_CLOSED**

The useful result is not a rescued headline. One of Bao's added falsifications partly survives and the other currently does not.

The next clean experiment should prospectively freeze:

- several reasonable effective-language boundaries;
- the description/cost encoding before outcomes are seen;
- operator + scope + withdrawal logic as the charged retained object;
- an old-language search baseline;
- an equal-budget case-table/dispatcher baseline;
- source-distinct held-out tasks and counterexamples.

Only if the same constructed operator remains outside the reasonable old-boundary family **and** wins total held-out description/search cost after all governance terms are charged should a compression claim be promoted.
