# IKKF V2c — Modular Capability Router

Date: 2026-08-14 NZST

Scientific verdict: `FAIL_IKKF_V2C_MODULAR_CAPABILITY_ROUTER`

GitHub Actions run: `31761615178`
Branch: `ikkf-v2c-modular-capability-router`
Run head: `aeffa5de16960d12a7873a0687b268e851b24484`
Evidence artifact: `ikkf-v2c-modular-capability-router`, artifact id `9204890169`
Artifact ZIP SHA-256: `50abb58c748c8635def92b581f7838b68b2a3e4a36fbb96c9f02e3e80a1e3ced`

Frozen protocol SHA-256: `ea7b9392b112afdd7d8d5f5bf1c78da5dbff5f95a394c371c500d625293081ce`
Experiment SHA-256: `26a1a4427de2b0e1ee118a7ce8bf766cd89983ed82f8643c70048cb162873976`

## Question

V2b showed that one shared C+J repair LoRA collapsed onto capability C. V2c asked whether keeping C and J as separate explicit verified modules and training only a small C-vs-J selector would recover routing on the same semantic-valid held-out universe.

The protocol was frozen before V2c outputs were observed. Held-out programs, suffixes, capability definitions, verifier, threshold and training budget were inherited from V2b.

## Semantic preconditions — PASS

All four prerequisite gates passed:

- practice C verified;
- practice J verified;
- held-out C mutations semantically verified;
- held-out J mutations semantically verified.

Thus the result is interpretable as a routing result rather than a bad-task-definition result.

## Frozen results

- cold/base router: `C=0.6667, J=0.0, joint=0.0, route=0.3333`
- matched monolithic arm: `C=1.0, J=0.0, joint=0.0, route=0.5`
- modular router + explicit modules: `C=1.0, J=0.0, joint=0.0, route=0.5`
- shuffled-label router: `C=0.0, J=1.0, joint=0.0, route=0.5`
- reload of modular router: `C=1.0, J=0.0, joint=0.0, route=0.5`

The matched monolithic arm exactly reproduced the V2b C-only collapse. The modular router also emitted C for every held-out case. The shuffled router emitted J for every held-out case. Reload preserved the corresponding collapse.

Failed frozen gates:

- `modular_J_passes`
- `modular_routes`
- `selected_modules_execute`
- `reload_preserves_modular_routing`

The modular arm improved neither joint success nor route accuracy over the matched monolithic arm.

## Scientific interpretation

Separating capability **execution** into modules is not sufficient. Under this frozen evidence representation and training budget, the learned selector itself fails to generalize the C/J distinction and collapses to one label.

This localizes the next frontier more sharply than V2b did: the problem is not only destructive interference from merging capability procedures into one adapter. It also appears at the activation/selection layer.

Do not tune V2c after observing this result. A successor should be newly precommitted and test a different routing representation or verifier-derived dispatch signal against this exact failure precedent.
