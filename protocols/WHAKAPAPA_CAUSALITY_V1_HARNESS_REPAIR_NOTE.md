# WHAKAPAPA CAUSALITY V1 — harness repair note

Status: **recorded after infrastructure diagnosis, before any authoritative scientific result**

A local deterministic reproduction of the frozen implementation exposed a world-construction failure on some sweep seeds: after exhausting the finite relation family, no relation satisfied the preregistered exact-parent admissibility constraints for that seed/topology position.

This is not a scientific success and is not rescued by changing the target, topology, seed, budget, arm, or gate.

The implementation is repaired only to:

1. detect finite-relation-family exhaustion exactly rather than looping through repeated hash collisions up to the old hard counter limit; and
2. record an exhausted/inadmissible sweep world as a failed scientific world in the fixed 125-world denominator rather than crashing the whole workflow as infrastructure failure.

Headline seeds are unchanged. All thresholds, worlds, candidate nuclei, ancestry arms, causal tests, budgets, and verdict definitions remain unchanged.

Any inadmissible sweep world counts against the relevant nucleus/whakapapa success criteria. It may not be skipped or replaced.
