#!/usr/bin/env python3
import hashlib, importlib.util, json, os, re, subprocess, sys
from pathlib import Path

BASE=Path(__file__).with_name('METALOGIC_V102_FRESH_SPLIT_EXPRESSION_CONSTRUCTOR.py')
spec=importlib.util.spec_from_file_location('v102orig',BASE)
v102=importlib.util.module_from_spec(spec); spec.loader.exec_module(v102)
ROOT=v102.ROOT; base_candidates=v102.base_candidates; expr_candidates=v102.expr_candidates
OUT=Path(os.environ.get('OUT_DIR','results/v102h')); OUT.mkdir(parents=True,exist_ok=True)
SEED='V102H_BYTECODE_SAFE_EXPRESSION_CONSTRUCTOR_2026-08-14'
EXPOSED=set(v102.EXPOSED); TEST_N=12; CAP_BASE=220; CAP_EXPR=260
EXPR_FAMILIES={'CALLABLE_CONSTRUCT','GUARD_EXPR','RETURN_EXPR','EXPR_GROW'}

def h(x): return hashlib.sha256((SEED+'|'+x).encode()).hexdigest()

def parse_score(rc,out):
    if rc==0:return 0
    z=re.search(r'(\d+) failed',out or '')
    if z:return int(z.group(1))
    z=re.search(r'(\d+) error',out or '')
    return 100+int(z.group(1)) if z else 99

def purge_bytecode(name):
    pc=ROOT/'python_programs'/'__pycache__'
    if pc.exists():
        for p in pc.glob(f'{name}.*.pyc'):
            try:p.unlink()
            except Exception:pass

def full_score(name,text):
    p=ROOT/'python_programs'/f'{name}.py'; old=p.read_text()
    env=os.environ.copy(); env['PYTHONDONTWRITEBYTECODE']='1'
    try:
        purge_bytecode(name)
        p.write_text(text)
        r=subprocess.run([sys.executable,'-B','-m','pytest','-q',f'python_testcases/test_{name}.py','--timeout=4'],cwd=ROOT,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=25)
        return parse_score(r.returncode,r.stdout)
    except Exception:return 999
    finally:
        p.write_text(old); purge_bytecode(name)

def reachable(name,cands):
    for kind,text in cands:
        if full_score(name,text)==0:return kind,text
    return None,None

def main():
    buggy=ROOT/'python_programs'; tests=ROOT/'python_testcases'; names=[]
    for p in buggy.glob('*.py'):
        n=p.stem
        if n in EXPOSED or not (tests/f'test_{n}.py').exists():continue
        if full_score(n,p.read_text())>0:names.append(n)
    names=sorted(names,key=lambda n:h('task|'+n)); test=names[:TEST_N]
    rows=[]; base_s=[]; expr_s=[]; replay_ok=True; provenance_ok=True
    for n in test:
        src=(buggy/f'{n}.py').read_text(); b=base_candidates(src,CAP_BASE); e=expr_candidates(src,CAP_EXPR)
        bk,btxt=reachable(n,b); ek,etxt=reachable(n,b+e)
        if bk:base_s.append(n)
        if ek:expr_s.append(n)
        new_here=(not bk and bool(ek))
        winner_origin=None
        if new_here:
            base_texts={t for _,t in b}; expr_texts={t for _,t in e}
            winner_origin='expr' if etxt in expr_texts and etxt not in base_texts and ek in EXPR_FAMILIES else 'invalid'
            provenance_ok=provenance_ok and winner_origin=='expr'
            s1=full_score(n,etxt); s2=full_score(n,etxt)
            replay_ok=replay_ok and (s1==0 and s2==0)
        rows.append({'task':n,'base_candidates':len(b),'expr_candidates':len(e),'base_reachable':bool(bk),'expanded_reachable':bool(ek),'winning_family':ek,'new_here':new_here,'winner_origin':winner_origin})
    new=sorted(set(expr_s)-set(base_s))
    gates={'fresh_hash_split':True,'previously_exposed_tasks_excluded':not any(n in EXPOSED for n in test),'no_correct_implementations_read':True,'generic_expression_substrate_fixed':True,'bytecode_purged_each_candidate':True,'bytecode_writes_disabled':True,'strict_closure_expansion':bool(new),'new_closure_winner_provenance_is_expression_only':bool(new) and provenance_ok,'winning_candidate_replay_consistent':bool(new) and replay_ok,'conservative':set(base_s)<=set(expr_s)}
    verdict='PASS_BYTECODE_SAFE_EXPRESSION_CONSTRUCTOR_V102H' if all(gates.values()) else 'MIXED_BYTECODE_SAFE_EXPRESSION_CONSTRUCTOR_V102H'
    res={'protocol':'V102H_BYTECODE_SAFE_EXPRESSION_CONSTRUCTOR','external_commit':v102.v100.COMMIT,'test':test,'excluded_exposed':sorted(EXPOSED),'base_reachable':base_s,'expanded_reachable':expr_s,'new_closure':new,'rows':rows,'gates':gates,'verdict':verdict,'qualification':'Corrected V102 replication with target bytecode purged before/after every candidate run, Python bytecode writes disabled, explicit winning-candidate provenance, and immediate success replay. The supplied generic expression substrate is still a representation bridge, not autonomous constructor genesis.'}
    (OUT/'RESULT.json').write_text(json.dumps(res,indent=2));print(json.dumps(res,indent=2))
if __name__=='__main__':main()
