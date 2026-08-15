#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MATRIX = ROOT / "FROZEN_EVAL_MATRIX.json"
KNOWN = ROOT / "KNOWN_QUALIFIED.json"
PROTOCOL = ROOT / "FOUR_ARM_PROTOCOL.json"

EXPECTED_ARMS = ["COLD", "RAW_MEMORY", "ALWAYS_ON", "VERIFIED"]
EXPECTED_PROTECTED = ["thefuck/32", "keras/32", "spacy/2", "fastapi/5", "black/18"]
EXPECTED_ACQUISITION = ["httpie/5", "youtube-dl/32"]


def main() -> None:
    matrix = json.loads(MATRIX.read_text())
    known = json.loads(KNOWN.read_text())
    protocol = json.loads(PROTOCOL.read_text())

    protected = [x["case"] for x in known["protected"]]
    acquisition = [x["case"] for x in known["acquisition"]]
    assert protected == EXPECTED_PROTECTED, (protected, EXPECTED_PROTECTED)
    assert acquisition == EXPECTED_ACQUISITION, (acquisition, EXPECTED_ACQUISITION)
    assert matrix["cases"] == EXPECTED_PROTECTED
    assert matrix["arms"] == EXPECTED_ARMS
    assert len(matrix["cells"]) == 20
    assert len({(c["case"], c["arm"]) for c in matrix["cells"]}) == 20
    assert {(c, a) for c in EXPECTED_PROTECTED for a in EXPECTED_ARMS} == {
        (x["case"], x["arm"]) for x in matrix["cells"]
    }
    assert matrix["model"] == protocol["model"] == "Qwen3.5-9B"
    assert matrix["temperature"] == protocol["temperature"] == 0
    assert matrix["max_calls_per_case_arm"] == protocol["max_calls_per_case_arm"] == 2
    assert matrix["max_tokens_per_call"] == protocol["max_tokens_per_call"] == 2048
    assert matrix["post_hoc_exclusions"] is False
    assert matrix["post_hoc_tuning"] is False
    assert matrix["isolation"]["fresh_state_per_cell"] is True
    assert matrix["isolation"]["no_shared_mutable_cache"] is True
    assert matrix["isolation"]["no_cross_arm_memory"] is True
    assert matrix["primary_comparison"] == "ALWAYS_ON_vs_VERIFIED"
    print("CP3 FROZEN MATRIX VALID: 2 acquisition / 5 protected / 20 cells")


if __name__ == "__main__":
    main()
