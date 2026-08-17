from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .state import Decision, EvidenceRef
from .state_v2 import DevelopmentalState


def load_cp3_capability(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    obj = json.loads(raw)
    required = {
        "capability_id", "status", "verifier", "artifact", "artifact_sha256",
        "preconditions", "postconditions", "scope", "evidence",
    }
    missing = sorted(required - set(obj))
    if missing:
        raise ValueError(f"CP3 capability missing fields: {missing}")
    if obj["status"] != "verified":
        raise ValueError("CP3 capability is not verified")
    if not obj["evidence"] or any(e.get("status") != "VERIFIED_REPAIR" for e in obj["evidence"]):
        raise ValueError("CP3 capability lacks all-verified acquisition evidence")
    # artifact_sha256 is the frozen hash of the capability's executable/prompt
    # artifact payload, while source_file_sha256 protects the serialized record.
    obj["source_file_sha256"] = hashlib.sha256(raw).hexdigest()
    return obj


def install_cp3_capability(state: DevelopmentalState, path: Path) -> str:
    obj = load_cp3_capability(path)
    cid = str(obj["capability_id"])
    evidence = EvidenceRef(
        verifier=str(obj["verifier"]),
        decision=Decision.VERIFIED,
        artifact=str(path),
        digest=str(obj["artifact_sha256"]),
        scope="acquisition-only verification; protected transfer not implied",
        metadata={
            "source_file_sha256": obj["source_file_sha256"],
            "acquired_from": obj.get("acquired_from", []),
            "evidence": obj["evidence"],
        },
    )
    capability = {
        "name": obj.get("name"),
        "type": obj.get("type"),
        "artifact": obj["artifact"],
        "applicability_test": obj.get("applicability_test"),
        "preconditions": obj["preconditions"],
        "postconditions": obj["postconditions"],
        "requires": list(obj.get("dependencies", [])),
        "provides": [cid],
        "source_artifact_sha256": obj["artifact_sha256"],
        "claim_boundary": "verified acquisition artifact; protected transfer requires separate evidence",
    }
    state.install_capability(cid, capability, evidence, scope=obj["scope"])
    return cid
