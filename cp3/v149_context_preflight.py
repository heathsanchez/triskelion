from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

# Importing this module installs the frozen V145A exact-runtime/precompiled
# apparatus patches without starting the V145 experiment.
import v145_precompiled_runner  # noqa: F401
import bugsinpy_four_arm as base
import bugsinpy_exact_runtime as exact
from v149_context_resolver import resolve_context

TASKS = [("youtube-dl", 32), ("pandas", 66)]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--bugsinpy', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    if args.out.exists():
        raise SystemExit('preflight output exists; refusing overwrite')
    args.out.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    for project, bug_id in TASKS:
        with tempfile.TemporaryDirectory(prefix=f'v149-preflight-{project}-') as td:
            try:
                work = base.checkout_buggy(args.bugsinpy, project, bug_id, Path(td))
                baseline = exact.native_test(args.bugsinpy, work)
            except Exception as exc:
                rows.append({'project':project,'bug_id':bug_id,'status':'R10','reason':f'{exc.__class__.__name__}: {exc}'})
                continue
            if baseline.get('infrastructure_error'):
                rows.append({'project':project,'bug_id':bug_id,'status':'R10','reason':baseline['infrastructure_error']})
                continue
            if baseline.get('passed'):
                rows.append({'project':project,'bug_id':bug_id,'status':'R10','reason':'buggy checkout did not reproduce frozen failure'})
                continue
            context, files, audit = resolve_context(work, baseline.get('test_output',''))
            bad_selected = [f for f in files if '/test/' in ('/'+f.lower()+'/') or f.lower().startswith('test/') or '/tests/' in ('/'+f.lower()+'/') or 'site-packages' in f.lower() or f.lower().startswith('env/')]
            eligible = audit.get('eligible_exact_hit') and not bad_selected and bool(context)
            rows.append({
                'project':project,'bug_id':bug_id,
                'status':'ELIGIBLE' if eligible else 'R10_CONTEXT_ADAPTER_INCONCLUSIVE',
                'visible_failure_tail':baseline.get('test_output','')[-5000:],
                'audit':audit,
                'selected_files':files,
                'context_chars':len(context),
                'bad_selected':bad_selected,
            })
    verdict = 'PASS_V149_CONTEXT_ADAPTER_ELIGIBLE' if len(rows)==len(TASKS) and all(r['status']=='ELIGIBLE' for r in rows) else 'R10_CONTEXT_ADAPTER_INCONCLUSIVE'
    out={'canonical_id':'V149_CONTEXT_ADAPTER_PREFLIGHT','verdict':verdict,'rows':rows,'claim_boundary':'Adapter eligibility only; no developmental conclusion.'}
    args.out.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,indent=2,sort_keys=True))
    if verdict != 'PASS_V149_CONTEXT_ADAPTER_ELIGIBLE':
        raise SystemExit(42)

if __name__=='__main__':
    main()
