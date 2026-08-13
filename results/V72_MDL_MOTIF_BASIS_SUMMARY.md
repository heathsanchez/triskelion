# V72 MDL Motif Basis

Verdict: PASS_MDL_MOTIF_BASIS_V72

Exact minimum-description-length search over the frozen 51-event corpus selected 5 reusable motifs from 11 candidates after charging for motif definitions.

Exact optimum dictionary:
1. CONSTRAIN -> SELECT -> RETAIN
2. CONSTRAIN -> SELECT
3. DISTINGUISH -> TRANSDUCE
4. RELATE -> COMPOSE
5. SELECT -> RETAIN

Corpus cost:
- raw baseline: 142
- best encoded cost including motif definitions: 120
- net saving: 15.493%
- exact subset search: yes

Matched within-program order-shuffle control:
- mean saving: 5.632%
- mean dictionary size: 3.508
- empirical p: 0.000999

Whole-scale omission transfer:
- held architecture: 15.52% compression
- held control: 20.00%
- held representation: 22.73%
- held task: 19.23%

Interpretation boundary: these are a minimum reusable macro basis for the manually normalized frozen corpus, not five proven universal organs. The basis is nested: CONSTRAIN->SELECT->RETAIN coexists with its shorter submotifs because those submotifs recur independently elsewhere. The strongest emerging macro families are fixation/admission, relation/composition, and distinction/transduction.

Actions run: 31742262476
Artifact SHA-256: ae432cc96822cdf05ebb4e14fc46d2aa371f496d0b0c991bade4c5829abdd21b
