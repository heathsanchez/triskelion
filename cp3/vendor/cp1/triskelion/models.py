from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


CAPABILITY_STATUSES = {
    "candidate", "verified", "scoped", "installed", "inactive",
    "superseded", "revoked", "recompressed",
}


@dataclass
class Task:
    task_id: str
    source: str
    tests: list[dict[str, Any]]
    metadata: dict[str, Any]
    split: str = "protected"
    source_group: str = "local"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Task":
        return cls(**value)


@dataclass
class Verdict:
    passed: bool
    task_id: str
    candidate_sha256: str
    tests_run: int
    failures: list[str]
    duration_ms: float
    replay_passed: bool
    infrastructure_error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Capability:
    capability_id: str
    name: str
    version: str
    type: str
    artifact: dict[str, Any]
    interface: dict[str, Any]
    preconditions: list[str]
    postconditions: list[str]
    scope: dict[str, Any]
    applicability_test: str
    dependencies: list[str] = field(default_factory=list)
    composes_with: list[str] = field(default_factory=list)
    conflicts_with: list[str] = field(default_factory=list)
    acquired_from: list[str] = field(default_factory=list)
    evidence: list[dict[str, Any]] = field(default_factory=list)
    verifier: str = "python-subprocess-v1"
    protected_tests: list[str] = field(default_factory=list)
    source_distinct_transfer: list[str] = field(default_factory=list)
    ablation_status: str = "untested"
    counterexamples: list[dict[str, Any]] = field(default_factory=list)
    revocation_conditions: list[str] = field(default_factory=list)
    discovery_cost: dict[str, Any] = field(default_factory=dict)
    execution_cost: dict[str, Any] = field(default_factory=dict)
    token_cost: dict[str, Any] = field(default_factory=dict)
    status: str = "candidate"
    enabled: bool = False
    artifact_sha256: str = ""

    def __post_init__(self) -> None:
        if self.status not in CAPABILITY_STATUSES:
            raise ValueError(f"invalid capability status: {self.status}")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Capability":
        return cls(**value)
