# Canonical Research Registry Schema

This directory is the programme-level source of truth for locating research outcomes across Triskelion and related repositories.

The registry does **not** replace primary artifacts, frozen protocols, the attestation ledger, or external verifier outputs. It points to them and records the current scientific interpretation.

## Identity rule

Bare version numbers are historical labels, not stable identities. A canonical record uses a descriptive `canonical_id`. This is mandatory because unrelated experimental lines reuse labels such as V49, V50 and V51.

## Required fields

| field | meaning |
|---|---|
| `canonical_id` | globally stable descriptive identifier |
| `historical_version` | original V-number / experiment label |
| `lineage` | programme lineage |
| `repo` | repository containing primary or best current evidence |
| `branch_or_ref` | branch, ref, or `main` |
| `status` | controlled scientific status |
| `domain` | code, math, Lean, model-routing, finite-algebra, controller, etc. |
| `primary_evidence` | result/protocol/attestation pointer |
| `mechanism` | concise statement of what was tested |
| `allowed_claim` | strongest statement currently supported |
| `forbidden_claim` | tempting stronger claim explicitly not supported |
| `supersedes` | prior canonical IDs narrowed/replaced by this result |
| `next_residual` | current unresolved obstruction |

## Controlled statuses

- `ATTESTED` — primary artifact/harness/predicate audited and claim is supported.
- `ATTESTED_QUALIFIED` — supported with an explicit adjacent limitation.
- `BOUNDED_PASS` — frozen bounded verdict supported; not necessarily freshly predicate-audited.
- `RESULT_ONLY` — committed result exists but CI/hosted provenance is incomplete.
- `MIXED` — some gates pass and some scientific gate fails.
- `NEGATIVE` — intended scientific mechanism was reached and falsified.
- `INVALID` — result cannot support the intended inference because of leakage/confounding/protocol invalidity.
- `HARNESS` — intended scientific mechanism was not reached because infrastructure failed.
- `CALIBRATION` — validates measurement/search machinery but is not target-domain evidence.
- `OPEN` — frozen or identified target without a completed admitted verdict.
- `HISTORICAL_REVIEW_NEEDED` — historical experiment preserved but not yet independently reconciled into the canonical claim ledger.

## Evidence precedence

When records disagree, use this order:

1. primary external verifier artifact / exact run output;
2. frozen protocol + successful hosted run;
3. `results/ATTESTATION_LEDGER.md` and authoritative addenda;
4. this registry;
5. README / narrative summaries;
6. branch names or historical labels.

A later negative or counterexample may narrow an earlier positive without erasing the earlier event.

## Controller rule

Every developmental record should be interpretable as some subset of:

`state -> residual -> closure test -> discriminator -> intervention -> verifier -> admission/rejection -> ablation -> transfer -> counterevidence -> next residual`.

Failures of provisioning, representation adapters, interpreter compatibility, runner allocation, or test reproduction are infrastructure residuals unless the protocol explicitly makes them the scientific target.
