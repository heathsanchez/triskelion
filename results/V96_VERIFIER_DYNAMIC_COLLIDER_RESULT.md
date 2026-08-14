# V96 Verifier-Only Dynamic Collider — Attested Result

Status: **MIXED / INTERPRETABLE TRANSFER NEGATIVE**

Primary workflow run: `31791344169`

Artifact: `9215945812` (`v96-verifier-dynamic-collider`)

Artifact SHA-256: `90ee045b12661bb34336b3560db31d32e043fdf2a594978462cbae8cae1e134e`

Primary verdict: `MIXED_VERIFIER_DYNAMIC_COLLIDER_V96`

## What passed

- pre-existing external QuixBugs corpus
- no correct implementations read anywhere
- verifier-improving training deltas existed
- anonymous dynamic clustering formed
- held-out successful candidates genuinely existed in the frozen K

Held-out reachability ceiling included:
- `breadth_first_search`
- `get_factors`

## What failed

The learned dynamic ranking recovered neither reachable repair; the coordinate-permuted null also recovered neither.

Training-side evidence was extremely narrow: 7/8 training tasks produced no improving mutation; `sqrt` alone produced three one-test improvements. MDL therefore selected a single medoid from one source task. Its dominant coordinates included an approximately `-1.62M` change in events/revisits, so the retained object largely represented one task's execution-pathology scale rather than a source-distinct recurrent mechanism.

## Binding interpretation

V96 is the first dynamic test in this line with a nonzero held-out reachability ceiling, so its ranking failure is interpretable. It does **not** support transferable verifier-induced dynamic structure under the tested protocol.

It also exposes a missing admission rule: multiple variants from one task must not establish a reusable organ/component. Future dynamic components require support from multiple source-distinct training tasks, and per-task dynamic signatures should be normalized before cross-task clustering so raw execution length cannot dominate the ontology.

V96 still cannot support economic savings because its dynamic candidate signatures were obtained through the full verifier. V97+ separates cheap probe traces from protected full-suite verification.
