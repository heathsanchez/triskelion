from __future__ import annotations
import json
from itertools import product
from pathlib import Path
OUT=Path('artifacts/v105_gf4_lattice'); OUT.mkdir(parents=True,exist_ok=True)

def add(x,y): return x^y
def mul(x,y):
    x0,x1=x&1,(x>>1)&1; y0,y1=y&1,(y>>1)&1
    c0=(x0*y0)^(x1*y1); c1=(x0*y1)^(x1*y0)^(x1*y1)
    return c0|(c1<<1)
def comp(f,g): return tuple(f[g[x]] for x in range(4))
ALL={tuple(v) for v in product(range(4),repeat=4)}
AFF={tuple(add(mul(a,x),b) for x in range(4)) for a in range(4) for b in range(4)}
BIJ={tuple(add(mul(a,x),b) for x in range(4)) for a in (1,2,3) for b in range(4)}
NON=ALL-AFF

def orbit(f): return {comp(post,comp(f,pre)) for pre in BIJ for post in BIJ}
def closure(seed,base=None):
    S=set(AFF if base is None else base)|{seed}; front={seed}
    while front:
        new=set();cur=list(S)
        for f in front:
            for g in cur:
                for h in (comp(f,g),comp(g,f)):
                    if h not in S:new.add(h)
        S|=new;front=new
    return S

def profile(S,orbits): return tuple(i for i,o in enumerate(orbits) if o<=S)

orbits=[];rem=set(NON)
while rem:
    s=min(rem);o=orbit(s)&NON;orbits.append(o);rem-=o
reps=[min(o) for o in orbits]
closures=[closure(r) for r in reps]
profiles=[profile(S,orbits) for S in closures]

within=[]
for i,o in enumerate(orbits):
    a,b=min(o),max(o); ca,cb=closure(a),closure(b)
    within.append({'orbit':i,'first_size':len(ca),'last_size':len(cb),'first_profile':profile(ca,orbits),'last_profile':profile(cb,orbits),'pass':len(ca)==len(cb) and profile(ca,orbits)==profile(cb,orbits)})

directed=[]
for i,S in enumerate(closures):
    for j,o in enumerate(orbits):
        if i!=j and o<=S and not (orbits[i]<=closures[j]): directed.append((i,j))

redundant=[]
for i,o in enumerate(orbits):
    a,b=min(o),max(o); ca=closure(a)
    redundant.append({'orbit':i,'second_already_reachable':b in ca,'pass':b in ca})

weak=(0,1,2); witness=None
for a in sorted(AFF):
    for n in sorted(NON):
        if tuple(a[x] for x in weak)==tuple(n[x] for x in weak) and a!=n:
            witness={'old':a,'new':n,'weak_signature':tuple(a[x] for x in weak),'separator_input':3,'old_at_separator':a[3],'new_at_separator':n[3]};break
    if witness:break

consts={f for f in AFF if len(set(f))==1}; false_collapse=None
for n in sorted(NON):
    for c in sorted(consts):
        h=comp(n,c)
        if h in AFF:
            false_collapse={'new':n,'noninvertible_old_pre':c,'collapsed_old':h};break
    if false_collapse:break

def gen(gens):
    S=set(gens);front=set(gens)
    while front:
        new=set();cur=list(S)
        for f in front:
            for g in cur:
                for h in (comp(f,g),comp(g,f)):
                    if h not in S:new.add(h)
        S|=new;front=new
    return S
incomplete=gen(consts|{tuple(add(x,1) for x in range(4))})

G1=len(orbits)>=2
G2=all(x['pass'] for x in within)
G3=len(set(len(S) for S in closures))>=2 or len(set(profiles))>=2
G4=len(directed)>0
G5=all(x['pass'] for x in redundant)
G6=witness is not None and witness['old_at_separator']!=witness['new_at_separator']
G7=false_collapse is not None and len(incomplete)<len(AFF) and BIJ<=AFF
PASS=all((G1,G2,G3,G4,G5,G6,G7))
R={'protocol':'V105_GF4_CAPABILITY_LATTICE_20260815','counts':{'all_functions':len(ALL),'old_affine':len(AFF),'old_bijections':len(BIJ),'nonaffine':len(NON),'orbit_count':len(orbits),'orbit_sizes':[len(o) for o in orbits]},'closures':[{'orbit':i,'orbit_size':len(orbits[i]),'closure_size':len(closures[i]),'reachable_orbits':profiles[i]} for i in range(len(orbits))],'within_orbit_invariance':within,'directed_reachability_edges':directed,'same_class_redundancy':redundant,'verifier_refinement_witness':witness,'negative_controls':{'noninvertible_false_collapse':false_collapse,'incomplete_old_presentation_size':len(incomplete),'full_old_size':len(AFF),'identity_group_subset_old':BIJ<=AFF},'gates':{'G1_nontrivial_quotient':G1,'G2_within_orbit_invariance':G2,'G3_between_orbit_capability_difference':G3,'G4_nontrivial_reachability_order':G4,'G5_same_class_redundant':G5,'G6_verifier_refinement':G6,'G7_negative_controls':G7},'verdict':'PASS_V105_GF4_CAPABILITY_LATTICE' if PASS else 'FAIL_V105_GF4_CAPABILITY_LATTICE','claim_boundary':'Fresh exact GF(4) unary substrate only; supports a nontrivial directed quotient/reachability structure under old affine automorphisms, not a universal lattice theorem or natural-world ontology growth.'}
(OUT/'RESULT.json').write_text(json.dumps(R,indent=2,sort_keys=True)+'\n')
print(json.dumps(R,indent=2,sort_keys=True))
if not PASS: raise SystemExit(1)
