# V106 Natural-Code Quotient Bridge — PRECOMMIT

Date: 2026-08-15 NZST

Status: frozen before qualification/execution.

## Purpose

V104/V105 establish quotient-level capability identity in exact finite algebraic worlds. V106 asks a narrower bridge question on externally authored natural code:

> When two literal repair operators differ only by an invertible source-coordinate transformation already available in the old language, does quotient-level identity preserve causal repair transfer across a deliberate presentation change where literal operator identity fails?

This is **not** a natural operator-discovery claim. The source code and tests are natural/external; the mutation and presentation perturbation are controlled.

## External corpus

QuixBugs repository pinned at commit:

`4257f44b0ff1181dedaedee6a447e133219fcebf`

Use only `correct_python_programs/` plus the repository's existing `python_testcases/` verifier. Do not inspect the buggy implementation or use the buggy/correct diff for candidate selection.

Frozen non-graph program list:

`bucketsort, find_first_in_sorted, find_in_sorted, flatten, gcd, get_factors, hanoi, is_valid_parenthesization, kth, lcs_length, lis, longest_common_subsequence, max_sublist_sum, mergesort, next_palindrome, next_permutation, pascal, possible_change, powerset, quicksort, rpn_eval, shunting_yard, sieve, sqrt, subsequences, to_base, wrap`

Slow/problematic `knapsack`, `levenshtein`, graph programs and timeout-prone `bitcount` are excluded prospectively.

## Frozen old coordinate transformation

`DUAL_CMP` on a single binary strict comparison:

- `a < b  <->  b > a`
- `a > b  <->  b < a`

This transformation is syntactically invertible and semantics preserving in Python for the ordinary values exercised by the external verifier. Every admitted task must empirically pass the original upstream tests under both presentations before mutation.

No non-invertible transformation is allowed to define identity.

## Candidate capability class

Controlled mutation class:

`RELAX_STRICT`
- `< -> <=`
- `> -> >=`

Corresponding repair class:

`TIGHTEN_STRICT`
- `<= -> <`
- `>= -> >`

Under `DUAL_CMP`, these two literal repairs are hypothesized to be one capability identity class.

## Task generation

Eligible sites are single-comparator `<` or `>` AST comparisons. To keep the unchanged external verifier tractable, qualification is prospectively capped to the **first three eligible sites in deterministic AST preorder per frozen program**. Sites after the first three are not inspected or used.

For each selected site:

1. start from the externally authored correct program;
2. create canonical-LT presentation by dualizing the site if necessary;
3. create canonical-GT presentation by dualizing the site if necessary;
4. verify both unmutated presentations pass the program's upstream pytest file;
5. apply `RELAX_STRICT` at that site in each presentation;
6. retain the site only if both relaxed presentations fail at least one upstream test;
7. verify `LE_TO_LT` repairs the LT presentation and `GE_TO_GT` repairs the GT presentation.

A task is one `(program, eligible-site-index)` pair satisfying all qualification predicates.

## Frozen source-distinct split

Split by **program name**, never by site:

`sha256(program_name).digest()[0] % 2 == 0` -> acquisition

odd -> held-out.

All sites from a program inherit the same split. This prevents source-file leakage between acquisition and held-out evidence.

Acquisition exposes only canonical-LT relaxed tasks. Held-out exposes only canonical-GT relaxed tasks.

## Baselines

### Literal-retention baseline
Retain exactly the literal repair token observed in acquisition: `LE_TO_LT`. No coordinate conversion is allowed.

### Quotient-retention arm
Retain the class `TIGHTEN_STRICT` plus the already-admitted invertible coordinate relation `DUAL_CMP`. At invocation it may instantiate the class as `LE_TO_LT` or `GE_TO_GT` according to the current presentation.

Both arms receive the same failing source and same verifier access. The difference is retained identity representation, not extra search.

## Frozen gates

### G1 — enough qualified natural-code tasks
At least 8 qualified tasks total, from at least 4 distinct programs, with at least 2 acquisition programs and 2 held-out programs.

### G2 — presentation invariance
For every qualified task, both unmutated LT and GT presentations pass the unchanged upstream test file.

### G3 — causal mutation
For every qualified task, both relaxed presentations fail the unchanged upstream verifier.

### G4 — quotient transfer beats literal identity
On held-out GT tasks:
- literal retained `LE_TO_LT` must solve **0** tasks because that literal edit is inapplicable;
- quotient retained `TIGHTEN_STRICT` instantiated as `GE_TO_GT` must solve **100%** of qualified held-out tasks.

### G5 — repair ablation
Removing the quotient repair from each held-out task restores the relaxed failing state for 100% of held-out tasks.

### G6 — representative equivalence
For every qualified task, repaired LT and repaired GT presentations both pass the same unchanged upstream tests.

### G7 — no file leakage
No program name appears in both acquisition and held-out sets.

### G8 — negative identity control
The report must explicitly show that a non-invertible map such as replacing one comparison operand by a constant cannot be admitted as an identity transformation merely because it can collapse some expressions. This is a structural exclusion, not a performance gate.

## Primary verdict

`PASS_V106_NATURAL_CODE_QUOTIENT_BRIDGE` only if G1–G7 pass and G8 is reported.

## Allowed interpretation

A pass supports only:

> On source-distinct externally authored QuixBugs Python programs with unchanged upstream tests, quotienting a controlled strict-bound repair by an invertible semantics-preserving comparison dualization preserves causal transfer across a deliberate source presentation change where literal operator retention fails.

It does **not** establish:
- natural discovery of the quotient relation;
- natural historical bug repair;
- autonomous operator invention;
- a natural-code capability lattice;
- representation-independent novelty.

## Next-step trigger

If V106 passes, the next experiment must remove the hand-specified quotient relation: infer candidate equivalence from verifier-equivalent transformations or dynamic behavior on acquisition programs, freeze it, and test source-distinct held-out transfer.
