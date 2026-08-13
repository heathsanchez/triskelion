import json, importlib.util, itertools, statistics
from pathlib import Path
spec=importlib.util.spec_from_file_location('v2','experiments/METALOGIC_ALPHABET_FALSIFICATION_V2.py');v2=importlib.util.module_from_spec(spec);spec.loader.exec_module(v2)
# Minimal four-state machine discovered only after V21.
SIG={
'DISTINGUISH':[('WORLD','OPEN'),('FIXABLE','OPEN')],
'GENERATE':[('OPEN','OPEN'),('MEMORY','OPEN')],
'RELATE':[('OPEN','OPEN'),('MEMORY','OPEN')],
'PROBE':[('OPEN','OPEN')],
'COMPOSE':[('OPEN','OPEN'),('MEMORY','OPEN')],
'TRANSDUCE':[('OPEN','OPEN'),('MEMORY','OPEN'),('FIXABLE','OPEN'),('MEMORY','WORLD')],
'CONSTRAIN':[('OPEN','FIXABLE')],
'SELECT':[('FIXABLE','FIXABLE')],
'RETAIN':[('FIXABLE','MEMORY')],
'RECURSE':[('MEMORY','WORLD')],
}
def step(types,op): return {b for t in types for a,b in SIG[op] if a==t}
def run(start,p):
 t={start}
 for op in p:
  t=step(t,op)
  if not t: break
 return t
rows=[]
for dom,text,decisive,p in v2.E:
 # Most recorded transitions are world-facing; explicit memory/development starts are identified conservatively.
 start='MEMORY' if (dom in {'memory','development'} and p and p[0] in {'TRANSDUCE','RECURSE','COMPOSE','RELATE','SELECT','RETAIN'}) else 'WORLD'
 out=run(start,p)
 rows.append({'domain':dom,'program':p,'start':start,'valid':bool(out),'terminal':sorted(out)})
valid=sum(r['valid'] for r in rows)/len(rows)
# For each valid program compare its operator multiset permutations (cap long programs by first 2000 deterministic permutations).
prs=[]
for r in rows:
 p=r['program']; perms=list(dict.fromkeys(itertools.permutations(p)))
 if len(perms)>2000: perms=perms[:2000]
 ok=sum(bool(run(r['start'],q)) for q in perms)
 prs.append(1-ok/len(perms))
R={'n':len(rows),'valid_rate':valid,'mean_permutation_prune':statistics.mean(prs),'median_permutation_prune':statistics.median(prs),'rows':rows}
R['gates']={'coverage':valid>=0.90,'strong_pruning':R['mean_permutation_prune']>=0.70}
R['verdict']='PASS_FOUR_STATE_IR_V22' if all(R['gates'].values()) else 'MIXED_FOUR_STATE_IR_V22'
out=Path('artifacts/four_state_ir_v22');out.mkdir(parents=True,exist_ok=True);(out/'RESULT.json').write_text(json.dumps(R,indent=2));print(json.dumps(R,indent=2))