from __future__ import annotations

from pathlib import Path

import source_context_ranker as base


def _focused_excerpt(path: Path, tokens: list[str], max_chars: int = 6500) -> str:
    """Return exact source text, never synthetic line-number prefixes."""
    text = path.read_text(encoding="utf-8", errors="replace")
    if len(text) <= max_chars:
        return text
    lines = text.splitlines()
    token_set = [t for t in tokens[:50] if len(t) >= 4]
    hits: list[int] = []
    for i, line in enumerate(lines):
        low = line.lower()
        if any(t in low for t in token_set):
            hits.append(i)
            if len(hits) >= 6:
                break
    if not hits:
        return "\n".join(lines[:180])[:max_chars]
    ranges: list[tuple[int, int]] = []
    for i in hits:
        start, end = max(0, i - 35), min(len(lines), i + 70)
        if ranges and start <= ranges[-1][1] + 5:
            ranges[-1] = (ranges[-1][0], max(ranges[-1][1], end))
        else:
            ranges.append((start, end))
    chunks: list[str] = []
    remaining = max_chars
    for start, end in ranges:
        exact = "\n".join(lines[start:end])
        if len(exact) > remaining:
            exact = exact[:remaining]
        chunks.append(exact)
        remaining -= len(exact)
        if remaining <= 0:
            break
    return "\n# ... excerpt boundary ...\n".join(chunks)


# collect_context resolves this helper dynamically in base's module namespace.
base._focused_excerpt = _focused_excerpt
collect_context = base.collect_context
