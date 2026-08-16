# RBS Meta-Episode 001 — Prospective controller decision on V149

Frozen: 2026-08-16 NZST, while GitHub Actions run 31941708089 was still inside the V149 context-adapter eligibility gate and before any V149 T2/T3 model outcome was available.

Controller under test: Rigorous Breakthrough Stack v1.1.

## Inherited immutable evidence

- V141 established `pandas/66` as the natural third eligible acquisition episode; this did not establish developmental dependence.
- V145 froze the three source-distinct natural tasks `httpie/5 -> youtube-dl/32 -> pandas/66`, Qwen/Qwen3.5-9B, three seeds, two-call budget, verifier, capability-construction rules, sham control, ancestor ablation and causal PASS gates.
- V145 exposed an adapter defect on T2: the native failure identified `TestUtil.test_strip_jsonp`, while the supplied visible buggy-source context omitted the `strip_jsonp` implementation and instead contained unrelated source. This is retained as evidence; it is not rewritten as a capability failure.
- V149 changes only the deterministic visible-source resolver and leaves the V145 scientific question and causal controls fixed.

## Live residual

Primary residual: representation / observability at the solver interface. The semantic target may be reachable, but the adapter may fail to expose the implementation implicated by visible verifier evidence.

Competing hypotheses retained prospectively:

H1 — ADAPTER-DISTORTION: V145's null was substantially caused by the source-context adapter omitting the verifier-implicated implementation. Repairing only that adapter will pass the preregistered eligibility gate and may expose a genuine O1-dependent T2 effect.

H2 — SEMANTIC-NULL: Even with verifier-aligned buggy-source context, O1 does not causally improve T2 under the frozen budget. If the V149 eligibility gate passes and T2 remains null, this hypothesis gains weight and the controller must not rescue O1 by another representation change without a new independent separator.

H3 — ADAPTER-STILL-INADEQUATE: The deterministic resolver still cannot expose a verifier-relevant implementation on T2 or T3. If the eligibility gate fails, V149 is infrastructure/adapter-inconclusive and yields no semantic update.

H4 — NONDEVELOPMENTAL-GAIN: T2 may improve, but sham, cold, O1-only/O2-only, or ancestor-ablation controls reproduce the apparent gain. In that case the strong developmental interpretation is rejected or narrowed according to the frozen V145 gates.

## Why V149 is the selected move

RBS selects V149 over broad model changes, extra calls, task substitution, larger context, hand-written paths, or new capability machinery because it is the smallest intervention that separates the strongest live rival explanations while preserving the original causal experiment. It modifies one identified information-exposure mechanism and leaves model, tasks, budgets, verifier, seeds, capability synthesis, controls and PASS criteria unchanged.

Closure-before-invention is satisfied: the controller first repairs access to already-existing buggy-checkout information implicated by the verifier rather than inventing a new O1/O2 primitive.

## Prospective outcome table

1. Eligibility gate fails on T2 or T3 -> `R10_CONTEXT_ADAPTER_INCONCLUSIVE`; retain V145 adapter residual; do not update O1/O2 semantics.
2. Eligibility passes; T2 O1 arm shows no preregistered advantage over cold and sham -> legitimate bounded semantic null for O1->O2 under this substrate/budget; suppress further adapter rescue unless new evidence identifies a distinct information defect.
3. T2 causal advantage passes but O2 cannot be constructed -> partial causal O1 result only; no three-rung claim.
4. T2 passes; T3 full developmental state fails against controls/ancestor ablation -> retain only the passed lower rung; reject strong three-rung development.
5. T2 and T3 satisfy all V145 gates, sham fails to reproduce, and ancestor ablation removes/materially weakens the T3 advantage -> promote bounded source-distinct three-rung causal development.
6. Gain is cost-only rather than reachability -> classify as `FRONTIER_EFFICIENCY`, not expanded reachability.

## Meta-controller score after outcome

This RBS decision receives prospective credit only if the V149 experiment produces decision-changing evidence under the table above. A V149 semantic PASS is not required for the controller decision itself to be useful; a clean semantic null after a valid adapter gate is also informative. A repeated adapter-inconclusive result counts against the controller's diagnosis/experiment selection.

No V149 result may be used to edit this record.
