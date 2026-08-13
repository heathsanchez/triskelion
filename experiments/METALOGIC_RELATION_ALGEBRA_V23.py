import itertools, json
from collections import deque
from pathlib import Path

STATES=('GROUNDED','OPEN','MEMORY')
I=frozenset((s,s) for s in STATES)
ZERO=frozenset()

# Three-state quotient of the frozen V21 signatures.
OPS={
'DISTINGUISH':frozenset({('GROUNDED','OPEN')}),
'GENERATE':frozenset({('OPEN','OPEN'),('MEMORY','OPEN')}),
'RELATE':frozenset({('OPEN','OPEN'),('MEMORY','OPEN')}),
'PROBE':frozenset({('OPEN','OPEN')}),
'COMPOSE':frozenset({('OPEN','OPEN'),('MEMORY','OPEN')}),
'TRANSDUCE':frozenset({('GROUNDED','OPEN'),('OPEN','OPEN'),('MEMORY','OPEN'),('MEMORY','GROUNDED')}),
'CONSTRAIN':frozenset({('OPEN','GROUNDED')}),
'SELECT':frozenset({('GROUNDED','GROUNDED')}),
'RETAIN':frozenset({('GROUNDED','MEMORY')}),
'RECURSE':frozenset({('MEMORY','GROUNDED')}),
}

def compose(a,b):
    # b after a
    return frozenset((x,z) for x,y in a for y2,z in b if y==y2)

def closure(gens):
    out={I,*gens}
    changed=True
    while changed:
        changed=False
        cur=list(out)
        for a in cur:
            for b in cur:
                c=compose(a,b)
                if c not in out:
                    out.add(c);changed=True
    return out

# Structural equivalence classes: same state relation, possibly different semantics.
classes={}
for name,r in OPS.items():classes.setdefault(r,[]).append(name)
unique=list(classes)
full=closure(unique)

# Find all minimum generating sets for the finite relation semigroup.
minsets=[]
for k in range(1,len(unique)+1):
    for ss in itertools.combinations(unique,k):
        if closure(ss)==full:minsets.append(ss)
    if minsets:break

# Give the unique minimum basis short neutral names if one exists.
chosen=minsets[0]
def names_for(r):return classes.get(r,['DERIVED'])
labels={}
for r in chosen:
    ns=names_for(r)
    if set(ns)=={'GENERATE','RELATE','COMPOSE'}:labels[r]='OPEN_TRANSFORM'
    elif ns==['TRANSDUCE']:labels[r]='TRANSDUCE'
    elif ns==['CONSTRAIN']:labels[r]='CONSTRAIN'
    elif ns==['RETAIN']:labels[r]='RETAIN'
    else:labels[r]='/'.join(ns)

# Shortest words in the structural basis.
shortest={I:()};q=deque([I])
while q:
    r=q.popleft()
    for g in chosen:
        c=compose(r,g)
        if c not in shortest:
            shortest[c]=shortest[r]+(labels[g],);q.append(c)

derived={op:list(shortest.get(r,())) for op,r in OPS.items()}
idempotents=[r for r in full if compose(r,r)==r]

# Algebraic law audit. These are properties of the frozen quotient, not semantic claims.
assoc=True
for a,b,c in itertools.product(full,repeat=3):
    if compose(compose(a,b),c)!=compose(a,compose(b,c)):
        assoc=False;break
identity_ok=all(compose(I,r)==r and compose(r,I)==r for r in full)
zero_ok=ZERO in full and all(compose(ZERO,r)==ZERO and compose(r,ZERO)==ZERO for r in full)

R={
 'states':STATES,
 'n_semantic_operators':len(OPS),
 'n_structural_operator_classes':len(unique),
 'structural_classes':{'|'.join(sorted(map(lambda x:x[0]+'>'+x[1],r))):v for r,v in classes.items()},
 'closure_size':len(full),
 'minimum_generator_size':k,
 'number_of_minimum_generator_sets':len(minsets),
 'minimum_basis':[labels[r] for r in chosen],
 'derived_operator_normal_forms':derived,
 'n_idempotents':len(idempotents),
 'associative':assoc,
 'identity_relation_present':identity_ok,
 'zero_relation_present':zero_ok,
 'interpretation_boundary':'This is the finite relation algebra induced by the manually frozen V21 three-state quotient. It establishes structural compression only; semantic distinctions among operators sharing a relation require executable causal tests.',
}
R['gates']={
 'finite_small_closure':len(full)<=32,
 'strict_structural_compression':k<len(unique),
 'unique_minimum_basis':len(minsets)==1,
 'category_like_composition':assoc and identity_ok,
 'semantic_aliases_exposed':any(len(v)>1 for v in classes.values()),
}
R['verdict']='PASS_FINITE_RELATION_ALGEBRA_V23' if all(R['gates'].values()) else 'MIXED_FINITE_RELATION_ALGEBRA_V23'
out=Path('artifacts/relation_algebra_v23');out.mkdir(parents=True,exist_ok=True)
(out/'RESULT.json').write_text(json.dumps(R,indent=2))
print(json.dumps(R,indent=2))
