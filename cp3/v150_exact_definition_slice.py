from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

from v149_context_resolver import _excluded, _project_py, identifier_candidates, visible_test_names

MAX_CHARS = 12000
BEFORE_LINES = 12
AFTER_LINES = 80


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def resolve_exact_slice(work: Path, baseline_output: str) -> tuple[str, list[str], dict[str, Any]]:
    root = work.resolve()
    tests = visible_test_names(baseline_output)
    identifiers = identifier_candidates(tests)
    hits: list[tuple[int, str, str, Path, int]] = []

    for p in _project_py(work):
        try:
            text = p.read_text(encoding='utf-8', errors='replace')
        except Exception:
            continue
        rel = str(p.resolve().relative_to(root))
        for ident in identifiers:
            pat = re.compile(r'(?m)^\s*(?:async\s+)?def\s+' + re.escape(ident) + r'\s*\(')
            m = pat.search(text)
            if m:
                line_no = text.count('\n', 0, m.start())
                hits.append((-len(ident), ident, rel, p, line_no))

    hits.sort(key=lambda x: (x[0], x[2], x[1], x[4]))
    if not hits:
        return '', [], {
            'visible_test_names': tests,
            'identifier_candidates': identifiers,
            'selected_hit': None,
            'eligible_exact_hit': False,
            'context_sha256': _sha(''),
        }

    _, ident, rel, p, line_no = hits[0]
    rel_path = Path(rel)
    if _excluded(rel_path):
        return '', [], {
            'visible_test_names': tests,
            'identifier_candidates': identifiers,
            'selected_hit': {'identifier': ident, 'path': rel, 'line': line_no + 1},
            'eligible_exact_hit': False,
            'reason': 'selected path excluded',
            'context_sha256': _sha(''),
        }

    text = p.read_text(encoding='utf-8', errors='replace')
    lines = text.splitlines()
    lo = max(0, line_no - BEFORE_LINES)
    hi = min(len(lines), line_no + AFTER_LINES + 1)
    slice_text = '\n'.join(lines[lo:hi]) + '\n'
    if len(slice_text) > MAX_CHARS:
        slice_text = slice_text[:MAX_CHARS]
    context = f"\n### FILE {rel} — exact-definition slice for {ident}\n```python\n{slice_text}```\n"
    audit = {
        'visible_test_names': tests,
        'identifier_candidates': identifiers,
        'selected_hit': {'identifier': ident, 'path': rel, 'line': line_no + 1},
        'slice_start_line': lo + 1,
        'slice_end_line': hi,
        'slice_chars': len(slice_text),
        'eligible_exact_hit': True,
        'context_sha256': _sha(context),
    }
    return context, [rel], audit
