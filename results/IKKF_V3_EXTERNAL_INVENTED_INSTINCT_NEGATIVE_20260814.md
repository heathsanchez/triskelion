# IKKF V3 — External Invented Instinct

Date: 2026-08-14 NZST

Scientific verdict: `FAIL_IKKF_V3_EXTERNAL_INVENTED_INSTINCT`

GitHub Actions run: `31761470384`
Branch: `ikkf-v3-external-invented-instinct`
Run head: `304327cb6a14029f442fb540b251cc1c688daf12`
Evidence artifact: `ikkf-v3-external-invented-instinct`, artifact id `9204884600`
Artifact ZIP SHA-256: `3fb0420af50d4d2b60d61070c05f29bf19e288bc7e4b634b921c8f43868e62a1`

## Infrastructure correction before the rerun

The prior V3 job stopped before River because the export-hygiene guard rejected the literal `optimizer_state` even though that literal occurred only inside the package's explicit `excluded` declaration. The correction made the hygiene scan inspect transferable payload fields while separately requiring the exclusion declaration to remain present. No capability content, training budget, sealed target, control, threshold, or scientific gate was changed.

The rerun therefore reached the frozen scientific endpoint for the first time.

## Explicit algebraic half — PASS

V51 Phase A again returned `PASS_V51_PHASE_A_OPERATOR_CONSTRUCTION` with all frozen Phase-A gates true.

The compact export returned `PASS_IKKF_V3_EXPORT`:

- capability id: `V51_58a32ca35135d99b`
- canonical package SHA-256: `3ce90f7afcf0ef999947ee39395dcaba67be9fca85399783db6b2a787c539c18`
- excluded material explicitly includes discovery source, test log, trajectory, checkpoint, gradient and optimizer state.

Fresh River compilation returned `PASS_IKKF_V3_COMPILE_ARTIFACTS` for two independent correct-scope compilations plus the frozen inverted-scope control.

The sealed explicit V51 Phase B returned `PASS_V51_SEALED_OPERATOR_INVENTION_RATCHET`:

- the sealed Requests target exposed the expected unseen obstruction;
- the explicit constructed operator repaired it;
- operator ablation restored failure;
- later source-distinct counterevidence was found inside the learned scope;
- scope refinement was attempted;
- no valid refined scope survived;
- the explicit capability was therefore revoked/detached.

This is a positive result for the explicit verified algebra / revision path.

## Neural bridge — FAIL

Frozen sealed neural scores:

- cold/base `B0`: **0.75**
- correct compile `C1`: **0.00** — emitted `NOOP` on all eight sealed cases
- independent correct compile `C2`: **0.00** — emitted `NOOP` on all eight sealed cases
- inverted-scope control `W`: **1.00** — emitted the capability id on all eight cases
- uninstall/cold comparison `U`: **0.75**
- reload of correct compile `R`: **0.00** — again emitted `NOOP` on all eight cases

Consequently the frozen neural gates for cold failure, compiled sealed success, causal neural ablation, independent recompile, wrong-scope control rejection, and reload preservation failed.

## Scientific interpretation

V3 does **not** establish the intended chain

`external verified invention -> compact capability package -> fresh neural compilation -> sealed neural instinct`.

The experiment instead separates two claims cleanly:

1. The explicit verified capability was genuinely constructed, transferred to an unseen external target, causally required there, and later revoked under counterevidence.
2. The frozen neural compiler did not preserve that scoped capability semantics; in fact the inverted-scope control generalized in the opposite direction while the two correct-scope compilations collapsed to `NOOP`.

Do not tune or reinterpret V3 as a pass. Any successor must be a newly precommitted experiment targeting the compiler's representation of scope/activation, with V3 retained unchanged as the falsifying precedent.
