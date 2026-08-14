# Attested evidence snapshots

This directory vendors the key primary result payloads that were directly audited during the 2026-08-14 evidence reconciliation. Its purpose is to make a downloaded ZIP of `main` useful even if GitHub Actions artifacts later expire.

The authoritative scientific status and exact allowed wording remain in [`../ATTESTATION_LEDGER.md`](../ATTESTATION_LEDGER.md). The original Actions run ID and artifact ZIP SHA-256 remain the provenance anchors.

## Included

- `V34_SOURCE_DISTINCT/RESULT.json` — copied from `metalogic-source-distinct-ratchet-v34`, run `31724783160`, artifact digest `sha256:7cb14558b24f4a7894fa68e6ed5a2ec7d3fee56223af5901e2f38cf568e1256f`.
- `V49_SEALED_TRANSFER/PRIMARY_ARTIFACT_SNAPSHOT.md` — audited V49 `COMMITMENT.json`, `PHASE_A.json`, `PHASE_B.json`; run `31749682731`; artifact digest `sha256:1079cae6f06085dc59bfa23cf548807d4219ecae811dd2d424dab5b9d3113a47`.
- `V50_OUTCOME_LABELED/PRIMARY_ARTIFACT_SNAPSHOT.md` plus `PHASE_A_FULL.json` — audited V50 payload; run `31749833138`; artifact digest `sha256:6a97a3e5978d03c5f495f01ca11c0620c822b12e13c963f7df31e01a7cdebddd`.
- `V51_OPERATOR_INVENTION/PRIMARY_ARTIFACT_SNAPSHOT.md` — audited V51 `COMMITMENT.json`, `PHASE_A.json`, `PHASE_B.json`; run `31759857216`; artifact digest `sha256:e3c10a4ba1011876e5df7248de4f3cb468e90195f6c331e625c3bb5d6c2f93d0`.

## Important integrity note

A vendored result snapshot is not a substitute for the harness. The corresponding experiment source and workflow must still be read when evaluating what a gate actually proves. This is especially important for V49–V51, where some `sealed`/`unseen` fields are declarative booleans; the behavioral transition predicates are executable, while temporal sealing is supported by phase-separated workflow/code structure.

The repository intentionally does **not** vendor evidence for `EXCEPTION_FLOW_EXTERNAL_STREAM` because no primary evidence for that reported result was located in this repo. The canonical ledger marks it `NOT ATTESTED IN THIS REPO`.
