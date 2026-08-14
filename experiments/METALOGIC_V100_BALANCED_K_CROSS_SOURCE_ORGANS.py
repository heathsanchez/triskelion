#!/usr/bin/env python3
import importlib.util, os
from pathlib import Path

BASE=Path(__file__).with_name('METALOGIC_V99_CROSS_SOURCE_DYNAMIC_ORGANS.py')
spec=importlib.util.spec_from_file_location('v99base',BASE)
v99=importlib.util.module_from_spec(spec); spec.loader.exec_module(v99)

ORIGINAL_RICH=v99.rich_candidates
OUT=Path(os.environ.get('OUT_DIR','results/v100')); OUT.mkdir(parents=True,exist_ok=True)

# Remove family-order truncation: enumerate a large superset first, then allocate
# approximately equal quota to every observed mutation family before deterministic fill.
def balanced_rich_candidates(src,cap):
    allc=ORIGINAL_RICH(src,max(5000,cap*20))
    groups={}
    for kind,text in allc:
        groups.setdefault(kind,[]).append((kind,text))
    kinds=sorted(groups)
    if not kinds:return []
    q=max(1,cap//len(kinds))
    out=[]; used=set(); cursors={k:0 for k in kinds}
    # Guaranteed family coverage first.
    for k in kinds:
        for item in groups[k][:q]:
            if item[1] not in used:
                out.append(item);used.add(item[1]);cursors[k]+=1
                if len(out)>=cap:return out
    # Deterministic round-robin fill from remaining candidates.
    progress=True
    while len(out)<cap and progress:
        progress=False
        for k in kinds:
            i=cursors[k]
            while i<len(groups[k]) and groups[k][i][1] in used:i+=1
            cursors[k]=i
            if i<len(groups[k]):
                item=groups[k][i];cursors[k]+=1;out.append(item);used.add(item[1]);progress=True
                if len(out)>=cap:break
    return out

v99.rich_candidates=balanced_rich_candidates

if __name__=='__main__':
    # Preserve V99 scientific logic; only constructor candidate allocation changes.
    v99.OUT=OUT
    v99.SEED='V100_BALANCED_K_CROSS_SOURCE_ORGANS_2026-08-14'
    v99.main()
