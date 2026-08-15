# V125 — universe-level schedule discriminator result

**Status:** `NULL_UNIVERSE_NOT_SUFFICIENT`

**External substrate:** `heathsanchez/specimen`

**Valid hosted workflow run:** `31893541675`

**Job:** `95033266282`

**Artifact:** `v125-universe-level-schedule-discriminator`

**Artifact ID:** `9249182587`

**Artifact digest:** `sha256:6a96fb40c7dfc9120f9455d38b88e01a2a13a584487be156dbda6c655be4cdd8`

## Precommit

Protocol frozen before fixture outcomes: `protocols/V125_UNIVERSE_LEVEL_SCHEDULE_DISCRIMINATOR_PRECOMMIT.md`, commit `bb3c884542cf04862637a51bdf32e0cc37180b50`.

## Harness note

Run `31893469385` was invalid because the workflow split left an orphan doc comment before a `derive_mutual` command, causing parse errors in both arms. The split harness was repaired without changing the frozen U0/U1 fixtures or discriminator.

## Valid result

Under exact frozen V120 K2:

- U0 parameter carrier in `Type`: PASS (`rc=0`).
- U1 matched parameter carrier in `Type 1`: PASS (`rc=0`).

Workflow verdict: `NULL_UNIVERSE_NOT_SUFFICIENT`.

## Interpretation

This falsifies the simplest explanation of V124: merely placing a fixed family parameter in `Type 1` is not sufficient to reproduce the Strata residual.

No generic universe-support K3 is justified from V124.

## Claim boundary

V125 is a prospective negative discriminator. It narrows the obstruction but provides no new repair capability by itself.
