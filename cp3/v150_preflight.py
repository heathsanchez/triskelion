from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

import bugsinpy_four_arm as base
import bugsinpy_exact_runtime as exact_runtime
from v150_exact_definition_slice import resolve_exact_slice

CASES = [('youtube-dl', 32), ('pandas', 66)]
base.native_test = exact_runtime.native_test


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--bugsinpy', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    rows = []
    eligible = True
    for project, bug_id in CASES:
        with tempfile.TemporaryDirectory(prefix=f'v150-pre-{project}-') as td:
            work = base.checkout_buggy(args.bugsinpy, project, bug_id, Path(td))
            baseline = exact_runtime.native_test(args.bugsinpy, work)
            if baseline.get('infrastructure_error'):
                rows.append({'project': project, 'bug_id': bug_id, 'status': 'R10', 'reason': baseline['infrastructure_error']})
                eligible = False
                continue
            if baseline.get('passed'):
                rows.append({'project': project, 'bug_id': bug_id, 'status': 'REPRODUCTION_NEGATIVE'})
                eligible = False
                continue
            context, files, audit = resolve_exact_slice(work, baseline.get('test_output', ''))
            bad = [f for f in files if 'test' in Path(f).parts or 'tests' in Path(f).parts]
            ok = bool(audit.get('eligible_exact_hit')) and len(files) == 1 and bool(context) and not bad
            rows.append({
                'project': project,
                'bug_id': bug_id,
                'status': 'ELIGIBLE' if ok else 'INELIGIBLE',
                'selected_files': files,
                'context_chars': len(context),
                'audit': audit,
                'bad_selected': bad,
            })
            eligible = eligible and ok
    result = {
        'canonical_id': 'V150_EXACT_DEFINITION_SLICE_PREFLIGHT',
        'rows': rows,
        'verdict': 'PASS_V150_SLICE_ELIGIBLE' if eligible else 'R10_CONTEXT_SLICE_INCONCLUSIVE',
        'claim_boundary': 'Representation eligibility only; no developmental conclusion.',
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps(result, indent=2, sort_keys=True))
    if not eligible:
        raise SystemExit(2)

if __name__ == '__main__':
    main()
