from pathlib import Path

from developmental_runtime import Decision, DevelopmentalState, EvidenceRef
from developmental_runtime.importers import install_cp3_capability


def ev(name: str) -> EvidenceRef:
    return EvidenceRef(
        verifier="test",
        decision=Decision.VERIFIED,
        artifact=f"test://{name}",
        digest=(name.encode().hex() + "0" * 64)[:64],
    )


def test_frozen_cp3_capability_import_is_scoped_and_replayable():
    state = DevelopmentalState()
    state.set_verifier_config("test-verifier", {"mode": "unit"}, ev("verifier"))
    cid = install_cp3_capability(state, Path("cp3_frozen/acquisition/CAPABILITY.json"))

    assert cid == "CP3.BUGSINPY.ACQUIRED.V1"
    assert cid in state.O
    assert state.S[cid]["scope"] == {"contains": "re.", "field": "source"}
    assert "protected transfer requires separate evidence" in state.O[cid]["claim_boundary"]

    replayed = DevelopmentalState.replay(state.snapshot()["events"])
    assert replayed.state_hash() == state.state_hash()
    assert replayed.O[cid]["source_artifact_sha256"] == state.O[cid]["source_artifact_sha256"]
