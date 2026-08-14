# Natural Constructor Audit — V87 through V96

This file pins the primary-artifact interpretation of the natural QuixBugs constructor/ontology sequence. A successful Actions run is not automatically a scientific PASS.

External corpus throughout: QuixBugs commit `4257f44b0ff1181dedaedee6a447e133219fcebf`.

## V87 — structural constructor induction
- Run `31784802703`
- Artifact `9215089519`
- SHA-256 `0181c97c3ce5f9efd9a39156491e64722715b2928165887702373e6a3ac1763c`
- Verdict: `MIXED_STRUCTURAL_CONSTRUCTOR_INDUCTION_V87`
- Raw closure expanded from 1 held-out task under K0 to 4 under the learned structural grammar, but the wrong-pair structural control solved the same 4 tasks. Therefore the gain is attributable to broadening the generic structural search language, not to causally learned training-side structure.

## V90 — protected constructor confirmation
- Run `31786981266`
- Artifact `9214010229`
- SHA-256 `81b998b4f4827382f46b1c9e5208a606358abbbaf4931b28822075cd75e90aaa`
- Verdict: `MIXED_PROTECTED_CONSTRUCTOR_CONFIRMATION_V90`
- Ordinary test closure expanded, but after candidate commitment and sealed human-fix reveal the protected agreement set was empty. Test-suite success did not survive the stronger independently authored repair check.

## V91 — verifier-induced site ontology
- Run `31787205758`
- Artifact `9214285939`
- SHA-256 `22d3966a0b6592fcd866ef115b677875c02ea6bccb6b4cd64c7ab9e53eaa1832`
- Verdict: `MIXED_VERIFIER_INDUCED_SITE_ONTOLOGY_V91`
- The verifier induced a nonempty operational site class, but held-out closure did not expand and the learned class did not beat shuffled-role controls.

## V94 — dynamic state invariants
- Run `31790728003`
- Artifact `9215561586`
- SHA-256 `c9d972a88de12c7c9af64ac33ec3c894f1a6d98a4fc1f1ab40dfdeffc223a4c3`
- Verdict: `MIXED_DYNAMIC_STATE_INVARIANTS_V94`
- Dynamic prototypes were nonempty, but the fixed candidate constructor contained no successful held-out repair (`reachable_success_exists=false`). This is a constructor-reachability negative, not evidence against dynamic geometry.

## V94C — dynamic-signature calibration
- Run `31790849808`
- Artifact `9215374279`
- SHA-256 `591574959c797a6467eac15447066be935b89937bd2f0dc29360a3106e882552`
- Status: calibration only, not natural evidence.
- The dynamic representation separated three known state-transition mechanisms on held-out calibration cases: 15/15 versus 5/15 for the coordinate-permuted null. This establishes that the measurement language itself is capable of distinguishing distinct dynamic mechanisms.

## V95 — anonymous dynamic Collider
- Run `31791105193`
- Artifact `9215816964`
- SHA-256 `e6e57f0baa1c76f322ea4482d5c7d58d8c711ff1b7d2d0a16e879798c2f35a20`
- Verdict: `MIXED_DYNAMIC_COLLIDER_V95`
- Anonymous MDL clusters formed from training-side external fixes, but again no held-out repair was reachable by the fixed candidate language. The Collider therefore remains untested for natural transfer under this K.

## V96 — verifier-only dynamic Collider
- Run `31791344169`
- Artifact `9215945812`
- SHA-256 `90ee045b12661bb34336b3560db31d32e043fdf2a594978462cbae8cae1e134e`
- Verdict: `MIXED_VERIFIER_DYNAMIC_COLLIDER_V96`
- No human correct implementations were read anywhere. Verifier-improving training deltas existed and an anonymous dynamic cluster formed. Two held-out repairs were reachable, but the learned dynamic cluster recovered 0/2 and did not beat the coordinate null. All three training improvements came from one source task (`sqrt`), so this does not establish a cross-world component.

## Current inference

The natural sequence now rules out several false shortcuts:

`broader K -> more solves` does not imply learned development (V87).

`test-suite PASS` does not imply protected structural correctness (V90).

`verifier-induced local category` does not imply transfer (V91).

`dynamic representation exists` is insufficient if K cannot reach any correct held-out repair (V94/V95).

`one-source recurring dynamic pathology` does not imply a reusable organ (V96).

The next admissible natural component therefore requires all of: a fixed sufficiently expressive K shared across controls; cheap probe evidence separated from protected verification; source-distinct support from at least two training worlds; normalized dynamic signatures; nonzero held-out reachability; recovery of protected held-out success; and advantage over coordinate-shuffled and hash baselines.

V97/V98/V99 are the live tests implementing those separations. None should be promoted until their primary artifacts finish and are audited.
