import copy

import pytest

from developmental_runtime import Decision, DevelopmentalState, EvidenceRef


def ev(name: str, *, decision: Decision = Decision.VERIFIED) -> EvidenceRef:
    return EvidenceRef(
        verifier="pytest-frozen-verifier",
        decision=decision,
        artifact=f"artifact://{name}",
        digest=(name.encode().hex() + "0" * 64)[:64],
        scope="unit-test",
    )


def test_nonverified_evidence_cannot_mutate_retained_state():
    state = DevelopmentalState()
    with pytest.raises(ValueError):
        state.install_capability(
            "C1",
            {"provides": ["x"]},
            ev("bad", decision=Decision.REFUTED),
        )
    assert state.O == {}
    assert state.events == []


def test_scope_is_executable_and_revocation_removes_activation():
    state = DevelopmentalState()
    state.install_capability(
        "C1",
        {"provides": ["repair"]},
        ev("install"),
        scope={"language": "python"},
    )
    assert state.active_capabilities({"language": "python"}) == ["C1"]
    assert state.active_capabilities({"language": "lean"}) == []

    state.refine_scope("C1", {"language": "python", "family": "exception-flow"}, ev("scope"))
    assert state.active_capabilities({"language": "python"}) == []
    assert state.active_capabilities({"language": "python", "family": "exception-flow"}) == ["C1"]

    state.revoke("C1", ev("revoke"), reason="protected counterexample")
    assert state.active_capabilities({"language": "python", "family": "exception-flow"}) == []


def test_developmental_compounding_changes_reachable_closure():
    state = DevelopmentalState()

    # O2 is present as a retained recipe but is not reachable from A0 because it
    # requires O1. This is the minimal runtime-level analogue of the V54/V80
    # discoverability relation, not a claim that the unit test reproduces those
    # experiments.
    state.install_capability(
        "O2",
        {"requires": ["O1"], "provides": ["target"]},
        ev("o2"),
    )
    cold = state.closure([])
    assert "O2" not in cold
    assert "target" not in cold

    state.install_capability(
        "O1",
        {"provides": ["O1-ready"]},
        ev("o1"),
    )
    warm = state.closure([])
    assert "O1" in warm
    assert "O2" in warm
    assert "target" in warm

    state.revoke("O1", ev("ancestor-ablation"), reason="causal ancestor ablation")
    ablated = state.closure([])
    assert "O1" not in ablated
    assert "O2" not in ablated
    assert "target" not in ablated


def test_constructor_and_quotient_are_first_class_state():
    state = DevelopmentalState()
    state.install_constructor(
        "K1",
        {"requires": [], "provides": ["expressible:new-family"], "version": 1},
        ev("k1"),
    )
    state.refine_quotient(
        "Q1",
        {"classes": [["a", "b"], ["c"]], "verifier_relative": True},
        ev("q1"),
    )
    state.set_discovery_policy(
        "D1",
        {"budget": 8, "closure_before_invention": True},
        ev("d1"),
    )
    assert "K1" in state.K
    assert state.Pi["Q1"]["classes"][0] == ["a", "b"]
    assert state.D["closure_before_invention"] is True


def test_hash_chain_detects_tampering_and_replay_reconstructs_identical_state():
    state = DevelopmentalState()
    state.install_capability("C1", {"provides": ["x"]}, ev("c1"), scope={"world": "A"})
    state.install_law("L1", {"requires": ["C1"], "provides": ["y"]}, ev("l1"))
    state.install_constructor("K1", {"provides": ["z"]}, ev("k1"))
    state.refine_scope("C1", {"world": "B"}, ev("scope"))
    state.record_obstruction("R1", {"class": "representation", "location": "demo"}, ev("r1"))

    assert state.verify_event_chain()
    event_dicts = state.snapshot()["events"]
    replayed = DevelopmentalState.replay(event_dicts)
    assert replayed.verify_event_chain()
    assert replayed.state_hash() == state.state_hash()

    tampered = copy.deepcopy(event_dicts)
    tampered[1]["payload"]["provides"] = ["forged"]
    with pytest.raises(ValueError, match="event hash mismatch"):
        DevelopmentalState.replay(tampered)
