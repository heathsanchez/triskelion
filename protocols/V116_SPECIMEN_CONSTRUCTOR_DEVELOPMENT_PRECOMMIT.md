# V116 — Specimen constructor-development capstone precommit

**Status:** FROZEN BEFORE TARGET EXECUTION

## Question

Can verifier-grounded failure demonstrate that a fixed constructor meta-language `K0` cannot construct a required capability, justify a minimal extension to `K1`, and then show that the extension changes held-out constructibility on independently authored Lean relations while preserving soundness?

This targets the remaining Triskelion constructor-development gap:

`Constructible(K0) ⊊ Constructible(K1)`

under an externally meaningful verifier-backed protocol.

## External substrate

Target repository: `heathsanchez/specimen`.

Specimen is a Lean 4 derivation system for generators, enumerators and checkers over inductive relations. Lean compilation / unchanged tests are the external correctness boundary. The Triskelion controller may propose constructor-language extensions but may not declare them correct.

## Frozen scientific distinction

A new constructor mechanism counts only if all of the following hold:

1. **K0 obstruction:** the target derivation cannot be produced by any admissible K0 schedule/mechanism under the frozen search/resource budget.
2. **No hidden old-language composition:** widening only lawful K0 composition to the frozen closure horizon does not solve the target.
3. **Minimal K1 intervention:** one predeclared mechanism family is added; unrelated search budget is held fixed.
4. **Verifier acceptance:** generated Lean code compiles and the unchanged target tests pass.
5. **Source-distinct transfer:** the committed K1 mechanism is applied without modification to at least one held-out relation from a different test/source family.
6. **Causal ablation:** disabling only K1 restores the held-out failure while K0, budget and verifier stay unchanged.
7. **Protected behavior:** existing K0-solvable derivations continue to compile/pass.
8. **Complexity accounting:** charge the added constructor/scheduling mechanism explicitly; do not call mere search expansion an invention.

## Frozen K0 boundary

Use the current Specimen mechanism vocabulary as exposed by the target commit selected before execution, but construct a restricted experimental `K0` by disabling exactly one mechanism family already present in the repository rather than inventing a toy DSL.

Candidate mechanism families eligible for removal are frozen to:

- delegated constrained production for equality/function-call premises;
- multi-output production;
- automatic dependency derivation;
- mutual-recursive shared derivation.

The target family is selected mechanically by source-distinct corpus qualification: choose the first family in the above order for which at least two independently authored existing Specimen test families satisfy:

- K0 fails for a mechanism-specific reason;
- full current Specimen succeeds;
- at least one additional protected K0-solvable case exists.

No outcome-based switching after examining held-out transfer results.

## Acquisition / held-out split

For the selected mechanism family:

- acquisition evidence: first qualifying existing test family in lexical path order;
- held-out evidence: second qualifying test family in lexical path order;
- protected controls: first three lexical K0-solvable test families not requiring the selected mechanism.

A test family means a distinct existing Specimen test module or directory, not a synthetic duplicate created for V116.

## K1 construction rule

The experiment is not allowed simply to re-enable the full upstream implementation and call that construction.

K1 must be reconstructed from the acquisition residual using only:

- the failing derivation trace / scheduler state;
- the inductive relation and types available to the derivation process;
- Lean elaboration / instance-synthesis feedback;
- the frozen generic mechanism family specification above.

The implementation may not read the held-out target module before K1 is committed.

The K1 patch must be frozen before held-out execution.

## Primary gates

- **G0 reproducibility:** pinned Specimen commit builds/tests before intervention.
- **G1 K0 genuine obstruction:** acquisition fails under K0 after frozen lawful closure search.
- **G2 full-system positive control:** upstream mechanism solves acquisition, proving the world is solvable.
- **G3 K1 acquisition:** reconstructed K1 solves acquisition under unchanged verifier/budget.
- **G4 held-out transfer:** same frozen K1 solves held-out source-distinct relation without modification.
- **G5 ablation:** disabling K1 restores held-out failure.
- **G6 protected preservation:** protected K0 cases remain passing with K1 installed.
- **G7 specificity:** K1 is invoked only on structurally eligible residuals; broad ALWAYS-ON application is separately tested when meaningful.
- **G8 complexity:** K1 does not merely increase generic enumeration/search limit; the new admissible production/dependency/composition operation is named and charged.

## Strong pass

`PASS_V116_CONSTRUCTOR_DEVELOPMENT` requires G0–G8.

## Negative / null outcomes

- `NULL_K0_NOT_OBSTRUCTED`: lawful K0 closure solves acquisition.
- `NULL_NO_TRANSFER`: K1 solves acquisition but not held-out.
- `NULL_NO_CAUSALITY`: ablation does not restore failure.
- `HARMFUL`: K1 breaks protected behavior or overactivates in a precommitted harmful control.
- `INVALID_LEAKAGE`: held-out source/solution influenced K1 before commitment.
- `INVALID_BOUNDARY`: result is only extra search/compute rather than constructor-language growth.
- `INFRA`: target repo cannot be reproduced independently of scientific mechanism.

## Claim boundary

A pass would support only:

> Within a pinned natural Lean metaprogramming system, a verifier-grounded obstruction in a restricted but real constructor mechanism set justified a minimal constructor-language extension that causally transferred to an independently authored held-out relation.

It would not establish arbitrary autonomous meta-language invention, open-ended recursive self-improvement, or representation-independent novelty.
