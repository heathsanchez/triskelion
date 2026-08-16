# V153A result ledger

Recorded after run `31944389267`; this is an outcome ledger only and changes no experiment parameter.

## Exact replay identity

V138 replay identity passed exactly:

- QuixBugs commit `4257f44b0ff1181dedaedee6a447e133219fcebf`;
- 17 programs;
- 24 natural strict-comparison sites;
- 281 verifier calls;
- 8 `RELAX_SAFE` and 16 `RELAX_SENSITIVE` labels.

## Support result

- single-program O3-evaluable programs: `0`;
- deterministic SHA(program)-ordered consecutive-pair holdouts: `9` groups;
- paired O3-evaluable folds: `4`;
- descriptive median held-out balanced accuracy among those four folds: `0.5`;
- preregistered verdict: `CORPUS_CEILING_V153_PAIRED_SUPPORT`.

The four evaluable paired folds had held-out balanced accuracies `0.0`, `0.5`, `0.5`, and `0.75`.

## Structural finding

Every one of the 17 source programs is label-pure: each program contributes only `RELAX_SAFE` sites or only `RELAX_SENSITIVE` sites. This completely explains why V138's original single-program leave-one-program-out O3 evaluation had zero evaluable folds. Deterministic program pairing increases support only to four evaluable folds, below the frozen minimum of eight.

## Claim boundary

V153A does **not** admit O3, upgrade V138 Q8/Q10, or establish a rule-language failure. The frozen classification is corpus/support ceiling because fewer than eight paired folds are evaluable. The observed median `0.5` is descriptive only under that boundary.

The next licensed move is to enlarge/freeze natural source support while preserving V138's O1/O2 definitions, O3 label semantics, feature language, rule selector, verifier and source-distinct holdout discipline. Changing the O3 rule language before adequate support would confound representation with corpus support.