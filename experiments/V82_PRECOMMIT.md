# V82 IVAG calibration precommit

Frozen scientific boundary before the CI run:

- Two hash-ordered source curricula: `math + numpy + str` and `scipy + mpmath + bytes`.
- Frozen low-level typed synthesis grammars for Evidence, SelectedHypothesis, and StableValue extensions.
- Uniform description length: one unit per low-level instruction token.
- Candidate admission requires cross-target support and minimum description length before support tie-breaking.
- Frozen held-out closure frontier uses distinct `math_hold`, `numpy_hold`, `str_hold` function identities plus a control frontier.
- Required gates: strict closure growth in both streams; no shorter admissible extension; conservative growth; E1 descendant counterfactual; E2→E3 counterfactual; independent extensional quotient convergence; matched-description-length advantage over alternative programs.
- This is a **bounded external-function calibration/bridge**, not the natural heterogeneous IVAG crown-jewel experiment. External callable semantics are independently authored, but task interfaces, dependency classes, and low-level synthesis grammars are authored.
