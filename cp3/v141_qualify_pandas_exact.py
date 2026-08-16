#!/usr/bin/env python3
from __future__ import annotations

import argparse, json, tempfile
from pathlib import Path

import qualify_remaining as q
import bugsinpy_four_arm as base
import bugsinpy_exact_runtime as exact


def checkout_version(bugsinpy: Path, project: str, bug_id: int, version: int, root: Path) -> Path:
    env = base.framework_env(bugsinpy)
    root.mkdir(parents=True, exist_ok=True)
    proc = base.run([
        'bugsinpy-checkout','-p',project,'-v',str(version),'-i',str(bug_id),'-w',str(root)
    ], timeout=1800, env=env)
    if proc.returncode != 0:
        raise RuntimeError(f'checkout_v{version}_failed: {proc.stdout[-8000:]}')
    work = root / project
    if not work.is_dir():
        raise RuntimeError(f'checkout_v{version}_missing_workdir')
    return work


def classify_pair(bugsinpy: Path, project: str, bug_id: int) -> dict:
    with tempfile.TemporaryDirectory(prefix='v141_pair_') as td:
        root=Path(td)
        out={'project':project,'bug_id':bug_id,'rank':q.candidate_rank(project,bug_id)}
        try:
            buggy=checkout_version(bugsinpy,project,bug_id,0,root/'buggy')
            buggy_v=exact.native_test(bugsinpy,buggy)
        except Exception as exc:
            out.update(qualified=None,reason=f'infrastructure_buggy:{exc.__class__.__name__}:{exc}')
            return out
        out['buggy']=buggy_v
        if buggy_v.get('infrastructure_error'):
            out.update(qualified=None,reason='infrastructure_buggy:'+str(buggy_v.get('infrastructure_error')))
            return out
        try:
            fixed=checkout_version(bugsinpy,project,bug_id,1,root/'fixed')
            fixed_v=exact.native_test(bugsinpy,fixed)
        except Exception as exc:
            out.update(qualified=None,reason=f'infrastructure_fixed:{exc.__class__.__name__}:{exc}')
            return out
        out['fixed']=fixed_v
        if fixed_v.get('infrastructure_error'):
            out.update(qualified=None,reason='infrastructure_fixed:'+str(fixed_v.get('infrastructure_error')))
            return out
        if fixed_v.get('passed') and not buggy_v.get('passed'):
            out.update(qualified=True,reason='fixed_pass_buggy_fail')
        else:
            out.update(qualified=False,reason=f"semantic_nonqualification:buggy_pass={buggy_v.get('passed')},fixed_pass={fixed_v.get('passed')}")
        return out


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--out',required=True)
    args=ap.parse_args()
    outp=Path(args.out); outp.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='v141_bugsinpy_') as td:
        repo=Path(td)/'BugsInPy'
        clone=q.run(['git','clone','--depth','1','https://github.com/soarsmu/BugsInPy.git',str(repo)],timeout=600)
        if clone.returncode != 0:
            outp.write_text(json.dumps({'status':'R10_INCONCLUSIVE','reason':'clone_failed','log_tail':clone.stdout[-12000:]},indent=2)+'\n'); return
        manifest=q.enumerate_manifest(repo)
        corpus_ok=len(manifest)==q.EXPECTED_BUG_COUNT and sorted({p for p,_ in manifest})==sorted(q.EXPECTED_PROJECTS)
        if not corpus_ok:
            outp.write_text(json.dumps({'status':'CORPUS_MISMATCH','observed_bug_count':len(manifest),'observed_manifest_sha256':q.canonical_manifest_hash(manifest)},indent=2)+'\n'); return
        ids=sorted([i for p,i in manifest if p=='pandas'],key=lambda i:q.candidate_rank('pandas',i))
        attempts=[]; selected=None
        for bug_id in ids:
            rec=classify_pair(repo,'pandas',bug_id)
            attempts.append(rec)
            print(json.dumps({k:rec.get(k) for k in ['project','bug_id','rank','qualified','reason']}),flush=True)
            if rec.get('qualified') is True:
                selected=f'pandas/{bug_id}'; break
        status='QUALIFIED' if selected else 'EXHAUSTED'
        result={'status':status,'project':'pandas','selected':selected,'attempts':attempts,'candidate_order':'SHA256(project/id) lexical hexadecimal ascending','admission':'fixed_pass_and_buggy_fail','semantic_skipping':False,'observed_bug_count':len(manifest),'observed_manifest_sha256':q.canonical_manifest_hash(manifest),'runtime_adapter':'cp3/bugsinpy_exact_runtime.py'}
        outp.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
        print(json.dumps({'status':status,'selected':selected,'attempt_count':len(attempts)},indent=2))

if __name__=='__main__': main()
