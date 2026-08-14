#!/usr/bin/env python3
import importlib.util, json, os
from collections import Counter
from pathlib import Path
ROOT=Path(os.environ.get('QUIXBUGS_DIR','/tmp/QuixBugs'))
OUT=Path(os.environ.get('OUT_DIR','results/v100k')); OUT.mkdir(parents=True,exist_ok=True)
P=Path(__file__).with_name('METALOGIC_V98_RICH_K_PROTECTED_DYNAMIC_RANKING.py')
s=importlib.util.spec_from_file_location('v98',P); v98=importlib.util.module_from_spec(s); s.loader.exec_module(v98)
Q=Path(__file__).with_name('METALOGIC_V100_BALANCED_K_CROSS_SOURCE_ORGANS.py')
s2=importlib.util.spec_from_file_location('v100',Q); v100=importlib.util.module_from_spec(s2); s2.loader.exec_module(v100)

def counts(xs): return dict(sorted(Counter(k for k,_ in xs).items()))
rows=[]
for p in sorted((ROOT/'python_programs').glob('*.py')):
    n=p.stem
    if not (ROOT/'python_testcases'/f'test_{n}.py').exists(): continue
    src=p.read_text()
    orig=v98.rich_candidates(src,220)
    bal=v100.balanced_rich_candidates(src,220)
    rows.append({'task':n,'ordered_n':len(orig),'balanced_n':len(bal),'ordered_families':counts(orig),'balanced_families':counts(bal),'ordered_family_count':len(counts(orig)),'balanced_family_count':len(counts(bal))})
summary={
 'protocol':'V100K_CONSTRUCTOR_COVERAGE_AUDIT_NONCLAIM',
 'status':'NONCLAIM_DIAGNOSTIC_ONLY',
 'tasks':len(rows),
 'mean_ordered_family_count':sum(r['ordered_family_count'] for r in rows)/len(rows),
 'mean_balanced_family_count':sum(r['balanced_family_count'] for r in rows)/len(rows),
 'tasks_balanced_has_more_families':sum(r['balanced_family_count']>r['ordered_family_count'] for r in rows),
 'tasks_same_family_count':sum(r['balanced_family_count']==r['ordered_family_count'] for r in rows),
 'rows':rows,
 'qualification':'Static candidate-allocation audit only. No verifier outcomes are used and this is not scientific evidence for transfer. It tests whether balanced-K changes effective mutation-family coverage under the same cap.'
}
(OUT/'RESULT.json').write_text(json.dumps(summary,indent=2)); print(json.dumps(summary,indent=2))
