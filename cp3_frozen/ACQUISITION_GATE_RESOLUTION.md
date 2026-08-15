# CP3 acquisition-count gate resolution

Status: **RESOLVED BEFORE PROTECTED SEMANTIC EVALUATION**

## Decision

The recovered frozen CP3 operational protocol admits progression with **at least 2 qualified acquisition cases and at least 5 qualified protected cases**.

Therefore, with the frozen known-qualified set:

- acquisition: `httpie/5`, `youtube-dl/32` (2)
- protected: `thefuck/32`, `keras/32`, `spacy/2`, `fastapi/5`, `black/18` (5)

the acquisition-count gate is satisfied once the acquisition-only capability is successfully frozen.

This resolution does **not** assert that five acquisition cases were never an aspirational target. It establishes only that no accessible frozen protocol artifact makes five acquisition cases a hard admissibility precondition, while multiple frozen recovery artifacts explicitly encode the 2+5 threshold and transition.

## Evidence

1. `.github/workflows/cp3-recovery-qualification.yml` (blob `5423cb66f21cf88a4e1ca7ed10eb53b902b3040e`) constructs the frozen known set as 2 acquisition + 5 protected and sets:

   `next_gate = PROTECTED_SANITIZATION_AND_FOUR_ARM` when `acquisition_count >= 2` and `protected_count >= 5`.

2. `cp3/STATUS.md` (blob `1edc8851556b5e302a34b37ef9d2022ae6c39ea0`) records:

   `Known qualified corpus before relaunch: 2 acquisition + 5 protected.`

   and states that the next gate after qualification merge is acquisition-capability freeze, followed by protected sanitization and four-arm evaluation.

3. `cp3/RECOVERY_NOTE.md` (blob `a1159a2eed75d1f5e46747d469b7da4d40bd1850`) explicitly labels its contents as preserved frozen protocol facts and records the same two acquisition and five protected cases.

4. `cp3/EXPECTED_NEXT_GATE.txt` (blob `c7c33b340de77e5326ad41dcf52ffca38493e1f2`) encodes:

   `qualification merge -> acquisition capability freeze -> protected sanitization -> COLD/RAW MEMORY/ALWAYS-ON/VERIFIED`.

5. `cp3/FROZEN_PROJECTS.json` (blob `8f1bb45da396bbe4c5a54dd44d189ce00f7e2484`) records the same known-qualified set and identifies only pandas, scrapy and luigi as unresolved qualification projects; it does not impose a five-acquisition minimum.

6. Search of accessible repository history found no frozen CP3 artifact or commit establishing `5 acquisition` as a hard protected-evaluation gate.

## Interpretation of the historical "5 acquisition" language

The historical notes referring to five acquisition cases are retained as a **target/recovery aspiration**, not silently deleted. They cannot override the explicit executable frozen gate without stronger authoritative evidence.

If later recovered pre-protected material explicitly states that five acquisition cases were mandatory, this resolution must be superseded and any protected run performed after this resolution must be classified accordingly. Until such evidence appears, the explicit frozen 2+5 gate is authoritative for this recovery lineage.

## Remaining gate

Protected semantic evaluation is still blocked until:

1. both frozen acquisition cases reproduce under the native historical environment;
2. acquisition produces verified repair evidence under the frozen call budget;
3. `CAPABILITY.json` and `RAW_MEMORY.txt` are serialized and SHA-256 frozen;
4. the information-boundary checks pass.

Only then may protected sanitization/evaluation begin.
