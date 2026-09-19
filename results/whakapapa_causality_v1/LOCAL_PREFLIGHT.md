# WHAKAPAPA CAUSALITY V1 — deterministic local preflight

Status: **NON-AUTHORITATIVE PREFLIGHT**. The authoritative verdict remains the GitHub Actions result produced by `.github/workflows/whakapapa-causality-v1.yml`.

The prospective protocol and clarification were frozen before outcome implementation. A deterministic local reproduction of the committed logic was then used to diagnose the harness and estimate the frozen scientific outcome.

## Headline

All five headline worlds constructed successfully.

Across binary, ternary, symbolic, temporal, and graph worlds:

- DMI lineage depth: **8/8** in every world.
- generated DMI dependency DAG exactly matched the hidden construction DAG in every world.
- DMI_COLD lineage depth: 1, 1, 2, 1, 1 respectively.
- MI lineage depth: 2 in every world.
- DM lineage depth: 1, 1, 2, 1, 1.
- DI lineage depth: 0 in every world.
- TRUE_MIN future discovery: **4 parent checks** vs FLAT **32** in every world.
- TRUE_MIN recombination: **1 check / success** vs FLAT **8 checks / budget failure** in every world.
- TRUE_MIN selective G2 revocation: safe with **7 requalification checks** in every world.
- TRUE_MIN L3 regeneration: **1 check / success** vs FLAT **12 checks / budget failure** in every world.
- TRUE_MIN direct ancestry: **16 edges** vs FULL_CLOSURE **51 edges**, with the same T1–T4 correctness class.
- RECONSTRUCT recovered the exact direct graph in every headline world, but required positive search work (222 parent-subset tests in binary; 197 in each other headline world).
- value-relabel metamorphism preserved the preregistered signature in binary, ternary, symbolic, and temporal worlds.

The preregistered SHAM revocation separator is not universal: in the ternary headline world the false DAG happened to induce the same G2 descendant cone and the same 7-check requalification cost as TRUE_MIN. That headline gate therefore fails as frozen; it is not rescued.

## 125-world sweep

The finite exact-parent world constructor exhausted its complete relation family in **18/125** frozen sweep worlds:

- binary: 8 exhausted worlds;
- temporal: 9 exhausted worlds;
- graph: 1 exhausted world;
- ternary: 0;
- symbolic: 0.

Per the harness-repair note, these worlds remain in the fixed denominator and count against success thresholds.

Among the **107 admissible worlds**:

- DMI full 8-node lineage: **107/107**;
- generated dependency DAG exact: **107/107**;
- DMI_COLD full lineage: **0/107**;
- DM reach loss vs DMI: **107/107**;
- DI reach loss vs DMI: **107/107**;
- MI reach-or-cost penalty vs DMI: **107/107**;
- TRUE_MIN T1 success: **107/107**;
- TRUE_MIN T1 cheaper than FLAT: **107/107**;
- TRUE_MIN T2 success within budget: **107/107**;
- TRUE_MIN safe selective revocation: **107/107**;
- TRUE_MIN T4 regeneration success: **107/107**;
- TRUE_MIN T4 cheaper than FLAT: **107/107**;
- TRUE_MIN/FULL_CLOSURE correctness equivalence: **107/107**;
- SHAM unsafe or more expensive than TRUE_MIN: **102/107**.

Against the frozen 125-world thresholds, V1 is therefore expected to classify as:

`PARTIAL_WHAKAPAPA_CAUSALITY_V1`

This is not an authoritative verdict until CI commits the result artifact.

## Interpretation boundary

The positive signal is conditional on an admissible world: every admissible sweep world in the local reproduction showed full DMI lineage generation, exact generated ancestry, causal value of TRUE_MIN on discovery/recombination/regeneration, and no cold full-lineage success.

The two V1 limitations are kept separate rather than narrated away:

1. **world-constructor admissibility** — 18 frozen seeds admit no relation satisfying the preregistered exact-parent topology under the supplied finite relation family;
2. **SHAM control identifiability** — a false DAG can sometimes preserve the same tested descendant cone and therefore be behaviorally indistinguishable on that revocation probe.

A V2, if run, must preregister an admissible-world sampler and a causally distinct sham control before inspecting V2 outcomes.
