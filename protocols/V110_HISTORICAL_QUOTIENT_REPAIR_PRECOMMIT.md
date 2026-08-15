# V110 Blind Historical Comparator-Repair Quotient Test — PRECOMMIT

Date: 2026-08-15 NZST

Status: frozen before execution.

## Purpose

V106B–V109 use externally authored natural code but controlled mutations. V110 crosses the next boundary: **actual benchmark buggy programs**.

Question:

> Does the quotient relation induced previously from controlled verifier evidence recur as a useful identity/compression relation among blind successful repairs of historical QuixBugs bugs, when the correct implementations are never consulted?

## External corpus

QuixBugs pinned commit:

`4257f44b0ff1181dedaedee6a447e133219fcebf`

Primary search may read only:

- `python_programs/` (buggy programs)
- `python_testcases/` (upstream verifier)

`correct_python_programs/` is **forbidden** to the V110 primary algorithm and is not read even after candidate selection in this run.

## Frozen program set

Use every Python program with both a buggy implementation file and an upstream Python testcase at the pinned commit, sorted lexicographically. No program is selected by inspecting its correct implementation or known bug type.

## Generic repair grammar

At each single binary comparison site (`<`, `>`, `<=`, `>=`, `==`, `!=`):

- operand coordinate: KEEP or SWAP;
- target comparator: any of the six comparator tokens;
- exclude the exact identity edit at that site.

Only one comparison site may be edited per candidate.

No historical patch, diff, or correct-source token is supplied.

## Verification

1. Run unchanged upstream tests on the buggy source.
2. Search only programs whose baseline tests fail.
3. Enumerate all one-site generic comparator candidates in frozen site/action order.
4. A candidate survives only if unchanged upstream tests pass completely.
5. Keep every passing candidate; do not cherry-pick a preferred one.

Python bytecode caches are purged between variants and Python is invoked with `-B`.

## Retained quotient relation

V108 independently induced the coordinate relation represented by:

- swap operands;
- `< <-> >`;
- `<= <-> >=`.

For V110 analysis, define the previously learned order-token involution:

`dual(<)=>`, `dual(>)=<`, `dual(<=)=>=`, `dual(>=)=<=`.

Equality/inequality repairs are left outside this retained quotient relation; V110 does not invent mappings for them.

A successful literal edit signature on order tokens is:

`(source_op, target_op, swap_bit)`.

Its retained-relation conjugate is computed by applying `dual` to source and target and toggling the coordinate presentation consistently. The quotient class is the canonical minimum of the literal signature and its conjugate.

## Frozen gates

### G1 — blind historical comparator repairs exist
At least 2 distinct failing QuixBugs programs have at least one one-site generic comparator candidate that makes the unchanged upstream tests pass.

### G2 — nontrivial exact repair search
At least one repaired program has competing candidate edits tested and rejected before/alongside a passing edit; this cannot be a direct application of a known patch.

### G3 — quotient recurrence across historical sources
At least one retained quotient class contains passing repairs from at least 2 distinct historical programs.

### G4 — literal diversity inside recurrent quotient class
For at least one recurrent quotient class, the member repairs use at least 2 distinct literal edit signatures. This is the key test that quotient identity collapses a source-presentation distinction that literal identity would keep separate.

### G5 — source-distinctness
Any recurrent quotient class satisfying G3/G4 must contain different program names, not multiple sites from one source.

### G6 — no correct-source leakage
The experiment code contains no read/access path to `correct_python_programs/` and reports that the primary search used only buggy source + upstream tests.

### G7 — ablation
For every reported passing repair candidate, restoring the original buggy source restores baseline failure.

## Verdict

`PASS_V110_HISTORICAL_QUOTIENT_REPAIR` only if G1–G7 all pass.

A failure is informative and must be kept. In particular, if historical comparator repairs exist but do not recur across quotient classes, the controlled-transfer result does not automatically generalize to historical bugs.

## Allowed interpretation

A pass supports only:

> Among blind verifier-confirmed one-comparator repairs of actual QuixBugs buggy programs, a quotient relation learned previously from controlled natural-code experiments recurs across source-distinct historical repairs and collapses literal repair distinctions without consulting correct implementations.

It does not establish general historical repair, autonomous operator invention, or benchmark-wide superiority.
