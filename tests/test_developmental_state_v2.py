from developmental_runtime import Decision, DevelopmentalState, EvidenceRef, SCHEMA_VERSION


def ev(name: str) -> EvidenceRef:
    return EvidenceRef(
        verifier="state-v2-test",
        decision=Decision.VERIFIED,
        artifact=f"artifact://{name}",
        digest=(name.encode().hex() + "0" * 64)[:64],
        scope="unit-test",
    )


def test_verifier_configuration_is_first_class_replayable_state():
    state = DevelopmentalState()
    state.set_verifier_config(
        "native-boundary",
        {"kind": "native-test-suite", "version": "frozen"},
        ev("verifier"),
    )
    state.set_discovery_policy("D", {"budget": 3}, ev("policy"))

    replayed = DevelopmentalState.replay(state.snapshot()["events"])
    assert replayed.V == state.V
    assert replayed.state_hash() == state.state_hash()
    assert replayed.snapshot()["schema"] == SCHEMA_VERSION == "developmental-state-v2"
