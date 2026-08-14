# QuixBugs verifier bytecode audit — 2026-08-14

## Trigger

Primary V102 (`run 31795259308`, artifact `9217573682`, digest `sha256:b722010e305183cb20ad23e21324c21d08f5ac5b2cf45290b6c187279a79800a`) reported:

- `rpn_eval` unreachable under the frozen base candidate list;
- then reachable under the exact same base list concatenated with expression candidates;
- the winning family was `CALL_ARG_SWAP`, which belongs to the base constructor, not the added expression constructor.

Because the same concrete base candidates occur before the added candidates, this row is internally inconsistent under a deterministic verifier.

The independently authored QuixBugs repair for `rpn_eval` is indeed `op(token, a, b) -> op(token, b, a)`, so the winning repair is real; the inconsistency is that it was missed in the first pass and found in the second pass over the same base candidates.

## Likely mechanism

The natural-repair harnesses repeatedly overwrite the same `python_programs/<task>.py` path and launch fresh Python/pytest subprocesses. The inherited `full_score` restores source text after each run but does not purge `python_programs/__pycache__` and does not disable Python bytecode writes.

Timestamp/size-based `.pyc` reuse can therefore execute stale candidate bytecode when multiple source rewrites occur within the timestamp resolution window, especially when candidate variants preserve file size. This is a plausible explanation for order-dependent replay of an identical candidate list.

## Status correction

`PASS_EXPRESSION_CONSTRUCTOR_BRIDGE_V102` is **INVALID / NEEDS BYTECODE-SAFE REPLICATION**. It must not be used as evidence for expression-constructor closure expansion.

V103 and later natural QuixBugs experiments that inherit the same `full_score` implementation are not promotable until reproduced with a hardened verifier. Earlier V83–V101 natural results should be treated conservatively and selectively revalidated before they support any headline claim, especially results whose scientific conclusion depends on candidate ordering or isolated one-off successes.

This does not automatically falsify all earlier results; many negatives may remain negatives. It means the verifier channel has a newly identified contamination risk and the evidence standard now requires replication.

## Hardened verifier protocol

The corrected verifier must, for every candidate execution:

1. purge target `python_programs/__pycache__/<task>.*.pyc` before the subprocess;
2. execute Python with bytecode writes disabled (`-B` and `PYTHONDONTWRITEBYTECODE=1`);
3. restore original source in `finally`;
4. purge target bytecode again after restoration;
5. require immediate replay consistency for any winning candidate;
6. for any claimed closure gain `Cl(K1) \ Cl(K0)`, prove that the winning candidate is absent from K0 and originates in the added constructor class.

An even stronger alternative is a clean isolated checkout per candidate, but the bytecode-safe protocol above is the current minimum.

## Frozen corrective experiments

### V102H — bytecode-safe expression-constructor replication

Branch: `v102h-bytecode-safe-expression-constructor`

The protocol reproduces V102 with bytecode purging, disabled writes, winning-candidate provenance, and immediate success replay. New runner attempts currently fail before allocation (`runner_id=0`, no steps), so there is no scientific V102H result yet.

### V104 — generic constructor synthesis

Branch: `v104-generic-constructor-synthesis`

V104 removes named high-level expression families and synthesizes programs from a generic substrate:

`SELECT(parent_type, field) -> BUILD(generic AST/value expression) -> REPLACE`.

Programs require verifier improvement on at least two source-distinct training tasks, are quotient-compared by their abstract action signature, frozen, and then tested on a held-out split against matched wrong-program controls.

V104 runner attempts also currently fail before runner allocation; no scientific result exists yet.

## Binding interpretation

Until the hardened replication lands, the strongest valid lesson from the latest sequence is methodological:

`failure -> exhaust lawful closure -> prove constructor obstruction -> harden verifier -> only then admit or synthesize K1`.

No V102/V103/V104 headline should be promoted before that chain is externally executed under the hardened verifier.
