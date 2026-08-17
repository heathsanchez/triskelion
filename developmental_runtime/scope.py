from __future__ import annotations

from typing import Any, Mapping


def _path(context: Mapping[str, Any], dotted: str | None) -> Any:
    if not dotted:
        return None
    value: Any = context
    for part in dotted.split("."):
        if not isinstance(value, Mapping) or part not in value:
            return None
        value = value[part]
    return value


def matches_scope(scope: Mapping[str, Any], context: Mapping[str, Any]) -> bool:
    """Evaluate the portable CP1/CP3-compatible serialized scope DSL.

    Supported forms are deliberately small and deterministic:
    `all`, `any`, `not`, then a leaf with `field` plus one of
    `equals`, `contains`, or `in`.
    """
    if not scope:
        return False
    if "all" in scope:
        return all(matches_scope(item, context) for item in scope["all"])
    if "any" in scope:
        return any(matches_scope(item, context) for item in scope["any"])
    if "not" in scope:
        return not matches_scope(scope["not"], context)

    value = _path(context, scope.get("field"))
    if "equals" in scope:
        return value == scope["equals"]
    if "contains" in scope:
        return isinstance(value, str) and str(scope["contains"]) in value
    if "in" in scope:
        try:
            return value in scope["in"]
        except TypeError:
            return False
    return False
