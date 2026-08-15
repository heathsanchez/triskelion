# Canonical Attestation Addendum — V104 / V105

Date: 2026-08-15 NZST

This addendum supplements `results/ATTESTATION_LEDGER.md` and is authoritative for the two entries below until the main ledger is next reconciled.

## `ADVERSARIAL_QUOTIENT_IDENTITY_V104`

Status: **ATTESTED — BOUNDED**

Primary lineage:
- frozen protocol: `protocols/V104_ADVERSARIAL_QUOTIENT_IDENTITY_PRECOMMIT.md`
- experiment: `experiments/V104_ADVERSARIAL_QUOTIENT_IDENTITY.py`
- successful hosted rerun of workflow run: `31866821184`
- successful hosted job: `94971782783`
- head: `914703653930e204c2677971fb253f239f0d3764`
- artifact: `9242555784`, `v104-adversarial-quotient-identity`
- artifact digest: `sha256:1ae531a0805c7225f7af62c0bf50638fc4b2e64aaa068825b0c2152540c92040`

Hosted execution evidence:
- checkout PASS
- Python setup PASS
- frozen adversarial quotient-identity test PASS
- artifact upload PASS

Exact allowed wording:

> In two exact finite algebraic substrates, novelty classification is invariant under tested old-language-preserving generator/coordinate redescriptions, deliberately disappears when the old capability is genuinely enlarged enough to subsume the class, and can refine when verifier authority increases. Literal operator identity is therefore not the stable unit in these bounded worlds; the supported unit is a verifier-indexed behavioral orbit modulo invertible transformations already realizable by the old capability state.

Important boundary:
- bounded B2 and GF(3) finite worlds only;
- does not establish representation-independent invention;
- does not establish natural-world/open-ended reasoning-language growth;
- the first pre-public Actions attempts failed before runner allocation and are infrastructure history, not scientific negatives.

## `GF4_CAPABILITY_LATTICE_V105`

Status: **ATTESTED — BOUNDED**

Primary lineage:
- frozen protocol: `protocols/V105_GF4_CAPABILITY_LATTICE_PRECOMMIT.md`
- experiment: `experiments/V105_GF4_CAPABILITY_LATTICE.py`
- successful hosted rerun of workflow run: `31866960458`
- successful hosted job: `94971776388`
- head: `832d552bf4e778ea47c5b3c64d05a770729a3dcc`
- artifact: `9242554905`, `v105-gf4-capability-lattice`
- artifact digest: `sha256:fd550486908c7d7e16bda611ebba191a37776acbd3e72629616a829791f348dc`

Hosted execution evidence:
- checkout PASS
- Python setup PASS
- frozen GF(4) capability-lattice experiment PASS
- artifact upload PASS

Frozen primary results:
- 256 unary GF(4) functions;
- 16 old affine maps;
- 240 non-affine candidates;
- four non-affine old-automorphism orbits with sizes 48, 36, 144, 12;
- representative closure sizes 64, 52, 244, 28 respectively;
- directed quotient reachability includes orbit `2 -> 0` and `2 -> 1`, without the converse relation;
- first/last tested representatives within every orbit have the same closure cardinality and reachable-orbit profile;
- adding a second tested representative from an admitted orbit adds no further closure;
- weak-verifier collision `(0,0,0,0)` vs `(0,0,0,1)` splits at the withheld fourth input;
- non-invertible coordinate maps demonstrably create false collapses and are excluded from the identity relation.

Exact allowed wording:

> In a fresh exact GF(4) unary substrate under a frozen protocol, old-automorphism quotient classes have distinct causal reachability consequences, same-class representatives are redundant after admission, and the induced quotient reachability relation is nontrivially directed. This supports a verifier-indexed capability preorder/reachability structure rather than an unordered bag of literal primitives.

Important boundary:
- fresh finite GF(4) unary world only;
- `lattice` remains a hypothesis/name for the broader structure; V105 establishes a nontrivial directed preorder/reachability relation, not a general lattice theorem;
- does not establish natural code/operator invention or open-ended ontology growth.

## Reconciliation consequence

The V104/V105 public hosted reruns remove the previous `local exact / not Actions-attested` qualification from these two results. Future summaries should cite this addendum until the main canonical ledger is updated.
