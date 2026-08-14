# V94C Dynamic Signature Calibration — Attested Result

Status: **PASS (AUTHORED CALIBRATION ONLY)**

Primary workflow run: `31790849808`

Artifact: `9215374279` (`v94c-dynamic-signature-calibration`)

Artifact SHA-256: `591574959c797a6467eac15447066be935b89937bd2f0dc29360a3106e882552`

Verdict in primary payload: `PASS_DYNAMIC_SIGNATURE_CALIBRATION_V94C`

## Frozen question

Can the execution-delta measurement used by V94 distinguish three known state-transition mechanisms across held-out problem sizes, and beat a coordinate-permuted null?

Mechanisms:
- RETAIN: collection growth
- FRONTIER: collection contraction
- FIXEDPOINT: numeric descent

## Primary result

- held-out mechanism classifications: **15/15 = 100%**
- coordinate-permuted null: **5/15 = 33.3%**
- all frozen gates passed

Learned prototype deltas were sharply separated:
- RETAIN: dominant `coll_grow`
- FRONTIER: dominant `coll_shrink`
- FIXEDPOINT: dominant `num_down`

## Claim boundary

This is an authored calibration. It establishes only that the V94 dynamic state-transition representation is capable of distinguishing several known mechanisms and that its coordinate identities matter. It is **not** evidence that those mechanisms are induced from natural external tasks, that they form a universal alphabet, or that they expand natural held-out closure.

Natural V94 remains the relevant external test.
