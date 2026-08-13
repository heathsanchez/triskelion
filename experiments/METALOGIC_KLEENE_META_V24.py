import itertools, json
from pathlib import Path

S=('G','O','M')
PAIRS=list(itertools.product(S,S))
ZERO=frozenset(); ONE=frozenset((s,s) for s in S)
OPS={
'D':frozenset({('G','O')}),
'U':frozenset({('O','O'),('M','O')}),
'T':frozenset({('G','O'),('O','O'),('M','O'),('M','G')}),
'C':frozenset({('O','G')}),
'S':frozenset({('G','G')}),
'M':frozenset({('G','M')}),
'R':frozenset({('M','G')}),
}

def seq(a,b): return frozenset((x,z) for x,y in a for y2,z in b if y==y2)
def plus(a,b): return a|b
def star(a):
    # finite reflexive transitive closure on 3 states
    r=ONE|a
    changed=True
    while changed:
        n=r|seq(r,r)
        changed=n!=r;r=n
    return r

def word(xs):
    r=ONE
    for x in xs:r=seq(r,OPS[x])
    return r

# Canonical cognitive macros at the structural quotient.
MACROS={
'FIX':['T','C','S','M'],
'OPEN_FIX':['C','S','M'],
'WAKE':['R','D'],
'DEVELOP':['R','D','C','S','M'],
}
macro_rel={k:word(v) for k,v in MACROS.items()}

# Algebra laws that should hold for binary relations/Kleene structure.
allrels=[]
for mask in range(1<<len(PAIRS)):
    allrels.append(frozenset(p for i,p in enumerate(PAIRS) if (mask>>i)&1))
assoc=all(seq(seq(a,b),c)==seq(a,seq(b,c)) for a,b,c in itertools.product(allrels[:32],repeat=3))
choice_assoc=all(plus(plus(a,b),c)==plus(a,plus(b,c)) for a,b,c in itertools.product(allrels[:32],repeat=3))
choice_idem=all(plus(a,a)==a for a in allrels)
seq_identity=all(seq(ONE,a)==a and seq(a,ONE)==a for a in allrels)

# Structural fixed-point laws for experimentally motivated words.
fix_idem=seq(macro_rel['FIX'],macro_rel['FIX'])==macro_rel['FIX']
develop_idem=seq(macro_rel['DEVELOP'],macro_rel['DEVELOP'])==macro_rel['DEVELOP']
wake_then_fix=seq(macro_rel['WAKE'],macro_rel['OPEN_FIX'])

# Choice+sequence generation from observed structural classes.
def closure(gens):
    out={ZERO,ONE,*gens};changed=True
    while changed:
        changed=False;cur=list(out)
        for a in cur:
            for b in cur:
                for z in (seq(a,b),plus(a,b)):
                    if z not in out:out.add(z);changed=True
    return out
observed=[OPS['D'],OPS['U'],OPS['T'],OPS['C'],OPS['S'],OPS['M'],OPS['R']]
full=closure(observed)
mins=[]
for k in range(1,len(observed)+1):
    for ss in itertools.combinations(observed,k):
        if closure(ss)==full:mins.append(ss)
    if mins:break

def opname(r):
    for n,x in OPS.items():
        if x==r:return n
    return '?'
R={
 'states':S,
 'algebra':'binary relations on three states with union, relational composition, identity, and reflexive-transitive closure',
 'all_relation_count':len(allrels),
 'generated_relation_count':len(full),
 'minimum_observed_generator_count_with_choice':k,
 'number_minimum_observed_generator_sets':len(mins),
 'minimum_observed_basis':[opname(x) for x in mins[0]],
 'macros':{k:{'word':v,'relation':sorted(macro_rel[k])} for k,v in MACROS.items()},
 'laws':{
   'sequence_associative_sample':assoc,
   'choice_associative_sample':choice_assoc,
   'choice_idempotent_full':choice_idem,
   'sequence_identity_full':seq_identity,
   'fixation_idempotent':fix_idem,
   'development_idempotent':develop_idem,
 },
 'boundary':'Structural algebra only. Semantic operators with the same state relation remain distinct effects and must be separated by executable verifier behavior.',
}
R['gates']={
 'choice_sequence_span_all_relations':len(full)==512,
 'small_basis':k<=3,
 'unique_basis':len(mins)==1,
 'fixation_is_projection':fix_idem,
 'development_is_fixed_point':develop_idem,
}
R['verdict']='PASS_COGNITIVE_PROGRAM_ALGEBRA_V24' if all(R['gates'].values()) else 'MIXED_COGNITIVE_PROGRAM_ALGEBRA_V24'
out=Path('artifacts/kleene_meta_v24');out.mkdir(parents=True,exist_ok=True)
(out/'RESULT.json').write_text(json.dumps(R,indent=2))
print(json.dumps(R,indent=2))
