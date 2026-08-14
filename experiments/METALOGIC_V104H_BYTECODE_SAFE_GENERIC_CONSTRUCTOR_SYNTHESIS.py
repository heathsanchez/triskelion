#!/usr/bin/env python3
import importlib.util, json, os, re, subprocess, sys
from pathlib import Path

BASE=Path(__file__).with_name('METALOGIC_V104_GENERIC_CONSTRUCTOR_SYNTHESIS.py')
spec=importlib.util.spec_from_file_location('v104base', BASE)
v104=importlib.util.module_from_spec(spec); spec.loader.exec_module(v104)
ROOT=v104.ROOT
OUT=Path(os.environ.get('OUT_DIR','results/v104h')); OUT.mkdir(parents=True,exist_ok=True)

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

def hardened_full_score(name,text):
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

if __name__=='__main__':
    # Scientific protocol is frozen from V104. Only the verifier channel is hardened.
    v104.full_score=hardened_full_score
    v104.OUT=OUT
    v104.main()
    p=OUT/'RESULT.json'
    r=json.loads(p.read_text())
    r['protocol']='V104H_BYTECODE_SAFE_GENERIC_CONSTRUCTOR_SYNTHESIS'
    r['gates']['bytecode_purged_each_candidate']=True
    r['gates']['bytecode_writes_disabled']=True
    r['qualification']=r.get('qualification','')+' V104H changes only verifier hygiene: target bytecode is purged before/after each candidate and Python bytecode writes are disabled. Constructor grammar, split, support threshold, candidate caps, controls, and synthesis logic are unchanged from V104.'
    # Preserve V104 scientific verdict semantics while requiring verifier-hardening gates too.
    passed=all(r['gates'].values())
    r['verdict']='PASS_BYTECODE_SAFE_GENERIC_CONSTRUCTOR_SYNTHESIS_V104H' if passed else 'MIXED_BYTECODE_SAFE_GENERIC_CONSTRUCTOR_SYNTHESIS_V104H'
    p.write_text(json.dumps(r,indent=2))
    print(json.dumps(r,indent=2))
