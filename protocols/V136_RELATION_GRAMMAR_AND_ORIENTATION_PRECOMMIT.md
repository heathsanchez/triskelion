# V136 Relation-Grammar Invariance + Orientation Forensics — Precommit

Status: FROZEN BEFORE V136 OUTCOMES.

## Purpose

Answer the two live V135 boundary questions without changing the scientific target:
1. diagnose the two failed orientation/presentation transfers from V135;
2. test whether the same verifier-induced capability class survives multiple independently specified candidate-relation grammars, including an expanded family.

This is a bounded follow-up, not a claim of unrestricted representation invariance or open-ended development.

## Frozen evidence discipline

- External corpus: QuixBugs commit `4257f44b0ff1181dedaedee6a447e133219fcebf`.
- Base verification semantics and AST site normalization are inherited unchanged from V135.
- Candidate selection sees acquisition-side verifier pass/fail and exact failure-node signatures only.
- Held-out records are not arguments to relation selection.
- Per-candidate timeout is a failing verifier outcome, never a PASS.
- Full result must report every failed fold; no exclusion after outcome inspection.

## Stage F — forensic replay

Replay the frozen V135 natural-code stratum and emit every orientation fold with:
- direction;
- held-out program;
- acquisition count;
- held-out count;
- number of perfect acquisition candidates;
- selected relation;
- quotient/literal/ablation counts.

Classify each non-perfect orientation fold prospectively:
- `F_NO_UNIQUE_RELATION`: acquisition evidence did not uniquely identify a candidate;
- `F_TRANSFER_BOUNDARY`: unique acquisition candidate existed but quotient transfer failed;
- `F_CORPUS_CEILING`: fold is not evaluable because acquisition or held-out support is absent.

No scientific promotion occurs from Stage F alone.

## Stage G — independently specified relation grammars

Use five grammar generators fixed before outcomes:

- `G0_FULL59`: frozen V135 59-candidate grammar.
- `G1_ACTION_SEQUENCE59`: generate candidate semantics by composing a fixed vocabulary of KEEP/SWAP with strict-token and relaxed-token emission, then deduplicate by compiled semantic tuple `(swap, strict_target, relaxed_target)`; exclude the same frozen literal `< -> <=` relation as V135.
- `G2_DUAL_PRESENTATION59`: generate candidates in the dual comparator coordinate system (`<↔>`, `<=↔>=`) then compile back to the V135 canonical evaluator and deduplicate by semantic tuple; exclude the same frozen literal relation after compilation.
- `G3_HASH_SPLIT_UNION59`: partition G0 deterministically by SHA-256 parity of candidate ID, generate the two partitions independently, then union and deduplicate before selection. This tests construction-path/vocabulary independence while preserving the same final semantic support.
- `G4_EXPANDED60`: use the complete 60 nonidentity one-step comparator relations over KEEP/SWAP × six strict tokens × five distinct relaxed tokens, including the literal `< -> <=` relation deliberately absent from V135. This is the stronger vocabulary-expansion test. If expansion creates an acquisition tie, selects a behaviourally different class, or destroys held-out transfer, full invariance fails.

The grammar generators must be created without reading V136 held-out outcomes.

### G gates

For every evaluable source-held-out fold:
- G0–G3 must induce exactly one acquisition-perfect candidate;
- G4 is permitted to expose a genuine ambiguity; any ambiguity is reported and blocks the full-pass verdict rather than being resolved post hoc;
- selected candidates across grammars must belong to the same **behavioural capability class**, defined prospectively as identical held-out quotient-success and targeted-ablation profile over the frozen fold set;
- literal repair baseline remains below quotient transport;
- targeted ablation removes the quotient advantage.

Report exact fold counts. A single behavioural-class disagreement prevents `PASS_FULL_GRAMMAR_INVARIANCE`.

## Stage H — stronger natural frontier claim

V136 may only report a **candidate next frontier experiment**. It may not claim natural multigeneration compounding, constructor growth, cross-domain generality, economic superiority, or open-ended development from these tests.

The next developmental test is admissible only if V136 localizes the orientation failures and the quotient class is stable across the frozen grammar generators.

## Verdicts

- `PASS_FULL_GRAMMAR_INVARIANCE`: all G gates pass, including G4 expansion, and all orientation failures are localized without post-hoc exclusion.
- `PARTIAL_GRAMMAR_INVARIANCE`: capability class is stable on evaluable folds but one or more orientation, uniqueness, or expanded-family gates fail.
- `REJECT_GRAMMAR_INVARIANCE`: independently generated grammars induce behaviourally different capability classes.
- `INVALID_V136`: information boundary, corpus freeze, or apparatus validity is violated.
