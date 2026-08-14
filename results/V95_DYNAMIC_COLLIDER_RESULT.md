# V95 Dynamic Collider — Attested Result

Status: **MIXED / REACHABILITY NEGATIVE**

Primary workflow run: `31791105193`

Artifact: `9215816964` (`v95-dynamic-collider`)

Artifact SHA-256: `e6e57f0baa1c76f322ea4482d5c7d58d8c711ff1b7d2d0a16e879798c2f35a20`

Primary verdict: `MIXED_DYNAMIC_COLLIDER_V95`

## Result

Ten training-side independently authored fixes produced nonzero anonymous execution-state delta vectors. A frozen MDL objective selected five medoids (`k=5`, objective `1.7526258858134427`) without semantic labels.

However on all eight held-out tasks the frozen generic candidate constructor contained **zero successful repair**. Therefore:

- unrestricted reachable success = 0/8
- learned-cluster success = 0/8
- coordinate-null success = 0/8

## Binding interpretation

V95 demonstrates that the clustering machinery can form a compact anonymous dynamic basis from natural training-side behavior, but it does **not** establish transfer usefulness because held-out K contains no correct candidate to prioritize.

This is the same reachability bottleneck exposed by V94. Future dynamic-ranking tests must first establish a nonzero held-out reachability ceiling under a constructor K held identical across learned and control arms.

Also, V95 obtains dynamic candidate traces via the full test verifier; therefore it cannot support an economic claim about saving expensive verification. V97/V98 explicitly separate cheap probe traces from protected full-suite calls.
