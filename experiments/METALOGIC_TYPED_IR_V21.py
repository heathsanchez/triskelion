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

# Cross-domain executable words. Start type and expected terminal type are frozen.
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
    types={start}
    trace=[sorted(types)]
    for op in program:
        types=advance(types,op)
        trace.append(sorted(types))
        if not types: break
    return types,trace

rows=[]
for dom,start,p,end in CASES:
    out,tr=run(start,p)
    rows.append({'domain':dom,'program':p,'valid':end in out,'terminal':sorted(out),'trace':tr})

# Permutation falsification: same operator multiset, all distinct permutations up to cap.
rng=random.Random(20260814)
perm_rows=[]
for dom,start,p,end in CASES:
    perms=list(dict.fromkeys(itertools.permutations(p)))
    if len(perms)>4000: perms=rng.sample(perms,4000)
    valid=[]
    for q in perms:
        out,_=run(start,q)
        if end in out: valid.append(q)
    true=tuple(p)
    perm_rows.append({'domain':dom,'n_perms':len(perms),'n_typed_valid':len(valid),'true_valid':true in valid,'prune_fraction':1-len(valid)/len(perms)})

# Search benchmark: one hidden target program per domain. Compare flat permutations vs type-guided DFS.
# Goal is to recover any well-typed program with the same multiset and terminal type;
# verifier then accepts only the frozen target order. This measures how much typing removes nonsense.
def typed_candidates(start, ops, end):
    seen=set(); count=0; found=[]
    def dfs(types, rem, seq):
        nonlocal count
        if not rem:
            count+=1
            if end in types: found.append(tuple(seq))
            return
        used=set()
        for i,op in enumerate(rem):
            if op in used: continue
            used.add(op)
            nt=advance(types,op)
            if not nt: continue
            dfs(nt, rem[:i]+rem[i+1:], seq+[op])
    dfs({start}, list(ops), [])
    return count,found

search=[]
for dom,start,p,end in CASES:
    total=len(set(itertools.permutations(p)))
    checked,cands=typed_candidates(start,p,end)
    target=tuple(p)
    target_in=target in cands
    # deterministic verifier cost: target position in lexicographic candidate order + 1
    cands_sorted=sorted(cands)
    verifier_cost=cands_sorted.index(target)+1 if target_in else None
    flat_sorted=sorted(set(itertools.permutations(p)))
    flat_cost=flat_sorted.index(target)+1
    search.append({'domain':dom,'flat_space':total,'typed_space':len(cands),'typed_prune':1-len(cands)/total,'flat_verifier_cost':flat_cost,'typed_verifier_cost':verifier_cost})

# Critical pair ablations from observed grammar.
critical=[
 ('CONSTRAIN','SELECT'),
 ('SELECT','RETAIN'),
 ('RELATE','COMPOSE'),
 ('DISTINGUISH','TRANSDUCE'),
]
crit=[]
for a,b in critical:
    affected=[c for c in CASES if a in c[2] and b in c[2] and c[2].index(a)<c[2].index(b)]
    for dom,start,p,end in affected:
        q=list(p); ia,ib=q.index(a),q.index(b); q[ia],q[ib]=q[ib],q[ia]
        out,_=run(start,q)
        crit.append({'domain':dom,'pair':f'{a}->{b}','reversed_valid':end in out})

R={
 'types':sorted({x for sigs in OPS.values() for sig in sigs for x in sig}),
 'operator_signatures':OPS,
 'canonical':rows,
 'permutation':perm_rows,
 'search':search,
 'critical_reversals':crit,
}
R['metrics']={
 'canonical_valid_rate':sum(r['valid'] for r in rows)/len(rows),
 'mean_permutation_prune':statistics.mean(r['prune_fraction'] for r in perm_rows),
 'mean_search_prune':statistics.mean(r['typed_prune'] for r in search),
 'median_search_prune':statistics.median(r['typed_prune'] for r in search),
 'critical_reversal_rejection':sum(not r['reversed_valid'] for r in crit)/len(crit),
 'typed_target_recovery':sum(s['typed_verifier_cost'] is not None for s in search)/len(search),
}
R['gates']={
 'all_canonical_typecheck':R['metrics']['canonical_valid_rate']==1.0,
 'typing_prunes_majority':R['metrics']['mean_search_prune']>=0.50,
 'critical_order_has_type_effect':R['metrics']['critical_reversal_rejection']>=0.70,
 'targets_preserved':R['metrics']['typed_target_recovery']==1.0,
}
R['verdict']='PASS_TYPED_COGNITIVE_IR_V21' if all(R['gates'].values()) else 'MIXED_TYPED_COGNITIVE_IR_V21'
out=Path('artifacts/typed_ir_v21');out.mkdir(parents=True,exist_ok=True)
(out/'RESULT.json').write_text(json.dumps(R,indent=2))
print(json.dumps(R,indent=2))
