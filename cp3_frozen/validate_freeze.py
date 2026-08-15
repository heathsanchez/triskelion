#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
ACQ=json.loads((ROOT/'ACQUISITION_BOUNDARY.json').read_text())
MAT=json.loads((ROOT/'PROTECTED_EVAL_MATRIX.json').read_text())

assert ACQ['acquisition_cases']==['httpie/5','youtube-dl/32']
assert ACQ['protected_cases']==['thefuck/32','keras/32','spacy/2','fastapi/5','black/18']
assert MAT['cases']==ACQ['protected_cases']
assert MAT['arms']==['COLD','RAW MEMORY','ALWAYS-ON','VERIFIED']
assert MAT['cell_count']==len(MAT['cases'])*len(MAT['arms'])==20
assert MAT['evaluation_repetitions_per_cell']==1
assert MAT['post_hoc_exclusions'] is False
assert MAT['post_hoc_tuning'] is False
assert MAT['shared_mutable_state_between_cells'] is False

for name in ['ACQUISITION_BOUNDARY.json','PROTECTED_EVAL_MATRIX.json']:
    p=ROOT/name
    print(name, hashlib.sha256(p.read_bytes()).hexdigest())
print('CP3_FROZEN_BOUNDARY_VALID')
