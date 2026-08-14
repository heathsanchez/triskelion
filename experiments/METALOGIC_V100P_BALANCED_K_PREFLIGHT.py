#!/usr/bin/env python3
import importlib.util, json, os
from pathlib import Path
BASE=Path(__file__).with_name('METALOGIC_V100_BALANCED_K_CROSS_SOURCE_ORGANS.py')
spec=importlib.util.spec_from_file_location('v100base',BASE)
v100=importlib.util.module_from_spec(spec); spec.loader.exec_module(v100)
v=v100.v99
OUT=Path(os.environ.get('OUT_DIR','results/v100p')); OUT.mkdir(parents=True,exist_ok=True)
v.OUT=OUT
v.SEED='V100P_BALANCED_K_PREFLIGHT_NONCLAIM_2026-08-14'
v.TRAIN_N=4; v.TEST_N=4; v.TRAIN_CAP=60; v.TEST_CAP=80; v.FULL_BUDGET=5
if __name__=='__main__':
    v.main()
    p=OUT/'RESULT.json'; r=json.loads(p.read_text())
    r['protocol']='V100P_BALANCED_K_PREFLIGHT_NONCLAIM'
    r['status']='NONCLAIM_DIAGNOSTIC_ONLY'
    r['qualification']='Shortened diagnostic only. Same balanced constructor-family allocation and cross-source dynamic admission idea as V100, but reduced task count and verifier budgets. Must not be entered as scientific evidence.'
    p.write_text(json.dumps(r,indent=2)); print(json.dumps(r,indent=2))
