from __future__ import annotations

import json
import re

import structured_edit_protocol as base


def _complete_missing_closers(text: str) -> str | None:
    """Append only unambiguous missing JSON container closers.

    This performs no semantic repair: it never changes strings, keys, values or
    punctuation already emitted by the model. It is accepted only when the
    output ends outside a string, all observed closers match, and at most three
    closing braces/brackets are missing at EOF.
    """
    stack: list[str] = []
    in_string = False
    escaped = False
    for ch in text:
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == '{':
            stack.append('}')
        elif ch == '[':
            stack.append(']')
        elif ch in '}]':
            if not stack or stack[-1] != ch:
                return None
            stack.pop()
    if in_string or escaped or not stack or len(stack) > 3:
        return None
    return text + ''.join(reversed(stack))


def _json_object(text: str) -> dict:
    blocks = re.findall(r"```(?:json)?\s*(.*?)```", text, flags=re.DOTALL | re.IGNORECASE)
    candidates = blocks + [text]
    last: Exception | None = None
    for raw in candidates:
        candidate = raw.strip()
        variants = [candidate]
        completed = _complete_missing_closers(candidate)
        if completed is not None:
            variants.append(completed)
        for variant in variants:
            try:
                value = json.loads(variant)
                if isinstance(value, dict):
                    return value
            except Exception as exc:
                last = exc
        # Also try the first JSON object prefix if the model added surrounding text.
        start = candidate.find('{')
        if start >= 0:
            suffix = candidate[start:]
            completed = _complete_missing_closers(suffix)
            if completed is not None:
                try:
                    value = json.loads(completed)
                    if isinstance(value, dict):
                        return value
                except Exception as exc:
                    last = exc
    raise ValueError(f"model output is not valid structured-edit JSON: {last}")


def extract_edits(text: str) -> str:
    value = _json_object(text)
    edits = value.get('edits')
    if not isinstance(edits, list) or not 1 <= len(edits) <= 3:
        raise ValueError('structured edit must contain 1-3 edits')
    normalized = []
    for edit in edits:
        if not isinstance(edit, dict):
            raise ValueError('each edit must be an object')
        path = edit.get('path')
        old = edit.get('old')
        new = edit.get('new')
        if not all(isinstance(x, str) for x in (path, old, new)):
            raise ValueError('edit path/old/new must be strings')
        if not path or not old or old == new:
            raise ValueError('edit must have nonempty path/old and make a real change')
        normalized.append({'path': path, 'old': old, 'new': new})
    return json.dumps({'edits': normalized}, sort_keys=True, separators=(',', ':'))


apply_edits = base.apply_edits
changed_files = base.changed_files
visible_request = base.visible_request
