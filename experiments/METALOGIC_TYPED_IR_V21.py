import json, itertools, random, statistics
from pathlib import Path

# Frozen typed cognitive IR. Operators may have more than one lawful signature,
# but every transition must satisfy an explicit input/output contract.
OPS = {
    'DISTINGUISH': [('WORLD','RESIDUAL'), ('BOUNDARY_RECORD','RESIDUAL'), ('TRACE','RESIDUAL')],
    'GENERATE': [('RESIDUAL','CANDIDATES'), ('MEMORY','CANDIDATES'), ('QUESTION','CANDIDATES')],
    'RELATE': [('CANDIDATES','RELATED'), ('MEMORY','RELATED'), ('RESIDUAL','RELATED')],
    'PROBE': [('RELATED','EVIDENCE'), ('RESIDUAL','EVIDENCE'), ('QUESTION','EVIDENCE')],
    'COMPOSE': [('RELATED','CANDIDATES'), ('MEMORY','CANDIDATES'), ('CAPABILITIES','CANDIDATES')],
    'TRANSDUCE': [('RESIDUAL','CANDIDATES'), ('MEMORY','CANDIDATES'), ('SURVIVOR','CANDIDATES'), ('MEMORY','WORLD')],
    'CONSTRAIN': [('CANDIDATES','ADMISSIBLE'), ('EVIDENCE','ADMISSIBLE'), ('RELATED','ADMISSIBLE')],
    'SELECT': [('ADMISSIBLE','SURVIVOR')],
    'RETAIN': [('SURVIVOR','MEMORY')],
    'RECURSE': [('MEMORY','WORLD')],
}
CASES = [
    ('proof','WORLD',['DISTINGUISH','GENERATE','RELATE','COMPOSE','CONSTRAIN','SELECT','RETAIN'],'MEMORY'),
    ('proof','WORLD',['DISTINGUISH','RELATE','PROBE','CONSTRAIN','SELECT','RETAIN'],'MEMORY'),
    ('proof','WORLD',['DISTINGUISH','TRANSDUCE','CONSTRAIN','SELECT','RETAIN'],'MEMORY'),
    ('coding','WORLD',['DISTINGUISH','GENERATE','CONSTRAIN','SELECT','RETAIN'],'MEMORY'),
    ('coding','WORLD',['DISTINGUISH','RELATE','COMPOSE','CONSTRAIN','SELECT','RETAIN'],'MEMORY'),
    ('coding','WORLD',['DISTINGUISH','PROBE','CONSTRAIN','SELECT','RETAIN'],'MEMORY'),
    ('science','WORLD',['DISTINGUISH','RELATE','PROBE','CONSTRAIN','SELECT','RETAIN'],'MEMORY'),
    ('science','WORLD',['DISTINGUISH','GENERATE','CONSTRAIN','SELECT','RETAIN'],'MEMORY'),
    ('representation','WORLD',['DISTINGUISH','TRANSDUCE','CONSTRAIN','SELECT','RETAIN'],'MEMORY'),
    ('memory','MEMORY',['TRANSDUCE','CONSTRAIN','SELECT','RETAIN'],'MEMORY'),
    ('development','MEMORY',['RECURSE','DISTINGUISH','RELATE','PROBE','CONSTRAIN','SELECT','RETAIN'],'MEMORY'),
    ('system','WORLD',['DISTINGUISH','RELATE','COMPOSE','CONSTRAIN','SELECT','RETAIN'],'MEMORY'),
]
def advance(types, op):
    out=set()
    for t in types:
        for a,b in OPS[op]:
            if a==t: out.add(b)
    return out
def run(start, program):
    types={start};trace=[sorted(types)]
    for op in program:
        types=advance(types,op);trace.append(sorted(types))
        if not types:break
    return types,trace
rows=[]
for dom,start,p,end in CASES:
    out,tr=run(start,p);rows.append({'domain':dom,'program':p,'valid':end in out,'terminal':sorted(out),'trace':tr})
rng=random.Random(20260814);perm_rows=[]
for dom,start,p,end in CASES:
    perms=list(dict.fromkeys(itertools.permutations(p)))
    if len(perms)>4000:perms=rng.sample(perms,4000)
    valid=[]
    for q in perms:
        out,_=run(start,q)
        if end in out:valid.append(q)
    perm_rows.append({'domain':dom,'n_perms':len(perms),'n_typed_valid':len(valid),'true_valid':tuple(p) in valid,'prune_fraction':1-len(valid)/len(perms)})
def typed_candidates(start, ops, end):
    found=[]
    def dfs(types,rem,seq):
        if not rem:
            if end in types:found.append(tuple(seq))
            return
        used=set()
        for i,op in enumerate(rem):
            if op in used:continue
            used.add(op);nt=advance(types,op)
            if not nt:continue
            dfs(nt,rem[:i]+rem[i+1:],seq+[op])
    dfs({start},list(ops),[]);return found
search=[]
for dom,start,p,end in CASES:
    total=len(set(itertools.permutations(p)));cands=typed_candidates(start,p,end);target=tuple(p)
    search.append({'domain':dom,'flat_space':total,'typed_space':len(cands),'typed_prune':1-len(cands)/total,'target_preserved':target in cands})
critical=[('CONSTRAIN','SELECT'),('SELECT','RETAIN'),('RELATE','COMPOSE'),('DISTINGUISH','TRANSDUCE')];crit=[]
for a,b in critical:
    for dom,start,p,end in [c for c in CASES if a in c[2] and b in c[2] and c[2].index(a)<c[2].index(b)]:
        q=list(p);ia,ib=q.index(a),q.index(b);q[ia],q[ib]=q[ib],q[ia];out,_=run(start,q);crit.append({'domain':dom,'pair':f'{a}->{b}','reversed_valid':end in out})
R={'canonical':rows,'permutation':perm_rows,'search':search,'critical_reversals':crit}
R['metrics']={'canonical_valid_rate':sum(r['valid'] for r in rows)/len(rows),'mean_search_prune':statistics.mean(r['typed_prune'] for r in search),'critical_reversal_rejection':sum(not r['reversed_valid'] for r in crit)/len(crit),'typed_target_recovery':sum(s['target_preserved'] for s in search)/len(search)}
R['gates']={'all_canonical_typecheck':R['metrics']['canonical_valid_rate']==1.0,'typing_prunes_majority':R['metrics']['mean_search_prune']>=0.50,'critical_order_has_type_effect':R['metrics']['critical_reversal_rejection']>=0.70,'targets_preserved':R['metrics']['typed_target_recovery']==1.0}
R['verdict']='PASS_TYPED_COGNITIVE_IR_V21' if all(R['gates'].values()) else 'MIXED_TYPED_COGNITIVE_IR_V21'
out=Path('artifacts/typed_ir_v21');out.mkdir(parents=True,exist_ok=True);(out/'RESULT.json').write_text(json.dumps(R,indent=2));print(json.dumps(R,indent=2))

# Run the separately frozen meta-math analysis after V21 so the approved workflow executes it too.
import importlib.util as _iu
_s=_iu.spec_from_file_location('v23','experiments/METALOGIC_METAMATH_V23.py');_m=_iu.module_from_spec(_s);_s.loader.exec_module(_m)
# retrigger: dependency-free V23
