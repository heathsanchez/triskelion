from __future__ import annotations

from typing import Any

from .models import Task


def _path(task: Task, dotted: str) -> Any:
    if dotted == "source":
        return task.source
    if dotted == "task_id":
        return task.task_id
    if dotted.startswith("metadata."):
        value: Any = task.metadata
        for part in dotted.split(".")[1:]:
            if not isinstance(value, dict) or part not in value:
                return None
            value = value[part]
        return value
    return None


def matches_scope(scope: dict[str, Any], task: Task) -> bool:
    """Evaluate a deliberately small, serializable scope DSL."""
    if not scope:
        return False
    if "all" in scope:
        return all(matches_scope(item, task) for item in scope["all"])
    if "any" in scope:
        return any(matches_scope(item, task) for item in scope["any"])
    if "not" in scope:
        return not matches_scope(scope["not"], task)
    field = scope.get("field")
    value = _path(task, field)
    if "equals" in scope:
        return value == scope["equals"]
    if "contains" in scope:
        return isinstance(value, str) and scope["contains"] in value
    if "in" in scope:
        return value in scope["in"]
    return False
