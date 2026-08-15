from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXPECTED_ACQUISITION = ["httpie/5", "youtube-dl/32"]
EXPECTED_PROTECTED = ["thefuck/32", "keras/32", "spacy/2", "fastapi/5", "black/18"]
EXPECTED_ARMS = ["COLD", "RAW MEMORY", "ALWAYS-ON", "VERIFIED"]
MODEL = "Qwen3.5-9B"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--acquisition-dir", type=Path, required=True)
    ap.add_argument("--expected-capability-sha256")
    ap.add_argument("--expected-raw-memory-sha256")
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    cap_path = args.acquisition_dir / "CAPABILITY.json"
    raw_path = args.acquisition_dir / "RAW_MEMORY.txt"
    status_path = args.acquisition_dir / "ACQUISITION_STATUS.json"
    for path in (cap_path, raw_path, status_path):
        if not path.is_file():
            raise SystemExit(f"FAIL_CLOSED: missing frozen acquisition artifact {path}")

    cap = json.loads(cap_path.read_text())
    status = json.loads(status_path.read_text())
    boundary = json.loads((HERE / "ACQUISITION_BOUNDARY.json").read_text())
    matrix = json.loads((HERE / "PROTECTED_EVAL_MATRIX.json").read_text())

    cap_sha = sha256(cap_path)
    raw_sha = sha256(raw_path)

    assert status.get("status") == "CAPABILITY_FROZEN", status
    assert status.get("acquisition") == EXPECTED_ACQUISITION, status
    assert status.get("protected_information_used") is False, status
    assert status.get("capability_sha256") == cap_sha, (status.get("capability_sha256"), cap_sha)
    assert status.get("raw_memory_sha256") == raw_sha, (status.get("raw_memory_sha256"), raw_sha)

    assert cap.get("acquired_from") == EXPECTED_ACQUISITION, cap.get("acquired_from")
    assert cap.get("protected_tests") == [], cap.get("protected_tests")
    assert cap.get("status") == "verified", cap.get("status")
    assert cap.get("enabled") is True, cap.get("enabled")

    artifact = cap.get("artifact")
    artifact_blob = json.dumps(artifact, sort_keys=True, separators=(",", ":")).encode()
    artifact_sha = hashlib.sha256(artifact_blob).hexdigest()
    assert cap.get("artifact_sha256") == artifact_sha, (cap.get("artifact_sha256"), artifact_sha)

    assert boundary.get("acquisition_cases") == EXPECTED_ACQUISITION
    assert boundary.get("protected_cases") == EXPECTED_PROTECTED
    assert matrix.get("cases") == EXPECTED_PROTECTED
    assert matrix.get("arms") == EXPECTED_ARMS
    assert matrix.get("cell_count") == 20
    assert matrix.get("model") == MODEL
    assert matrix.get("temperature") == 0
    assert matrix.get("max_calls_per_cell") == 2
    assert matrix.get("max_tokens_per_call") == 2048
    assert matrix.get("evaluation_repetitions_per_cell") == 1
    assert matrix.get("shared_mutable_state_between_cells") is False
    assert matrix.get("post_hoc_exclusions") is False
    assert matrix.get("post_hoc_tuning") is False

    if args.expected_capability_sha256:
        assert cap_sha == args.expected_capability_sha256
    if args.expected_raw_memory_sha256:
        assert raw_sha == args.expected_raw_memory_sha256

    result = {
        "status": "CP3_PROTECTED_PREFLIGHT_OK",
        "capability_sha256": cap_sha,
        "raw_memory_sha256": raw_sha,
        "artifact_sha256": artifact_sha,
        "acquisition": EXPECTED_ACQUISITION,
        "protected": EXPECTED_PROTECTED,
        "arms": EXPECTED_ARMS,
        "cell_count": 20,
        "protected_semantics_opened": False,
    }
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    print(text, end="")


if __name__ == "__main__":
    main()
