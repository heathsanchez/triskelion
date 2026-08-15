# V116 — Specimen constructor-development capstone

**Verdict:** `INVALID_LEAKAGE — TARGET MECHANISM ALREADY EXPOSED`

V116 was frozen to test whether a constructor mechanism `K1` could be reconstructed from an acquisition residual and committed before held-out inspection.

That prospective interpretation is no longer valid.

During qualification, the selected first mechanism family in the frozen ordering was `delegated constrained production for equality/function-call premises`. Inspection of Specimen commit `b93d259e0ddf39ee8ab60b680a7964c75c6d2392` exposed both the mechanism implementation and its motivating tests before an independent K1 reconstruction was attempted.

The upstream commit explicitly documents:

- `computeDelegableVars` probing for constrained-producer instances;
- scheduler changes that treat eligible function-call equality arguments as producible;
- `SuchThat` emission for delegated variables;
- per-premise delegability;
- `DelegatedProducerTest`;
- `DelegatedProducerRepeatedVarTest`;
- the Strata `LExpr` well-typed generator example.

The commit added/modified the relevant implementation and test files in one historical patch. Therefore simply reconstructing or re-enabling that mechanism now would be contaminated by solution knowledge.

## Scientific consequence

V116 may still be used as a **historical natural example** that a real Lean constructor system expanded its mechanism vocabulary to handle a previously weak generate-and-test case, but it cannot count as a prospective Triskelion constructor-invention capstone.

Do not report `PASS_V116_CONSTRUCTOR_DEVELOPMENT` from any replay of this already-inspected mechanism.

## Useful surviving observation

The same upstream Strata example states an orthogonal limitation that was deliberately *not* solved by the delegated-producer change:

> the real `LExpr` carries a structure parameter `T : LExprParamsT` in `Type 1`; the constrained deriver does not yet handle that structure parameter and tries to generate it, so the example inlines a monomorphic parameterization instead.

That exposed limitation gives a cleaner fresh constructor-development target because the repository documents the obstruction while not providing a solution in the inspected patch.

A successor must freeze the Type-1/structure-parameter target before inspecting or implementing any solution.
