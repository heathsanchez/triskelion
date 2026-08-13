# Implementation-only accelerator for the frozen V75 protocol.
# Loads every constant, family, instance, action semantic and gate from the frozen V75 source,
# but caches candidate verifier outcomes once instead of recomputing them in each null replicate.
import json, random
from pathlib import Path

src=Path('experiments/METALOGIC_EXECUTABLE_MATH_CONTROL_V75.py').read_text()
prefix=src.split('big=fit_bigram(TRAIN);uni=fit_unigram(TRAIN)',1)[0]
ns={}
exec(compile(prefix,'METALOGIC_EXECUTABLE_MATH_CONTROL_V75.py','exec'),ns)

TRAIN=ns['TRAIN'];FAMILIES=ns['FAMILIES'];DATA=ns['DATA'];CHAINS=ns['CHAINS'];OPS=ns['OPS']
SEED=ns['SEED'];INSTANCES=ns['INSTANCES'];MAX_LEN=ns['MAX_LEN'];SHUFFLE_REPS=ns['SHUFFLE_REPS'];LABEL_REPS=ns['LABEL_REPS'];GATESPEC=ns['GATESPEC'];OUT=ns['OUT']
fit_bigram=ns['fit_bigram'];fit_unigram=ns['fit_unigram'];typed_candidates=ns['typed_candidates'];succeeds=ns['succeeds']

big=fit_bigram(TRAIN);uni=fit_unigram(TRAIN)
CANDS={f:typed_candidates(f) for f in FAMILIES}
SUCCESS={f:{p for p in CANDS[f] if succeeds(f,p)} for f in FAMILIES}

def first_rank(f,score):
 cands=CANDS[f];good=SUCCESS[f]
 order=sorted(cands,key=lambda p:(score(p),len(p),p))
 for i,p in enumerate(order,1):
  if p in good:return i,p,len(order),len(good)
 return None,None,len(order),0

rows=[]
for f in FAMILIES:
 rg,pg,n,k=first_rank(f,big);ru,pu,_,_=first_rank(f,uni)
 random_expect=(n+1)/(k+1) if k else float('inf')
 rows.append({'family':f,'typed_candidates':n,'successful_programs':k,'grammar_rank':rg,'grammar_program':pg,'unigram_rank':ru,'unigram_program':pu,'random_expected_rank':random_expect,'grammar_normalized':rg/random_expect if rg else None,'unigram_normalized':ru/random_expect if ru else None})

g_mean=sum(x['grammar_normalized'] for x in rows)/len(rows);u_mean=sum(x['unigram_normalized'] for x in rows)/len(rows)
rng=random.Random(SEED+1);sh=[]
for _ in range(SHUFFLE_REPS):
 q=[]
 for s in TRAIN:
  z=list(s);rng.shuffle(z);q.append(tuple(z))
 sc=fit_bigram(q);vals=[]
 for f in FAMILIES:
  r,_,n,k=first_rank(f,sc);vals.append(r/((n+1)/(k+1)))
 sh.append(sum(vals)/len(vals))
shuffle_p=(1+sum(x<=g_mean for x in sh))/(SHUFFLE_REPS+1)

lp=[]
for _ in range(LABEL_REPS):
 z=OPS[:];rng.shuffle(z);mp=dict(zip(OPS,z))
 def sc(p,mp=mp):return big(tuple(mp[x] for x in p))
 vals=[]
 for f in FAMILIES:
  r,_,n,k=first_rank(f,sc);vals.append(r/((n+1)/(k+1)))
 lp.append(sum(vals)/len(vals))
label_p=(1+sum(x<=g_mean for x in lp))/(LABEL_REPS+1)

R={'implementation':'V75_FAST_CACHE_ONLY','frozen_source':'experiments/METALOGIC_EXECUTABLE_MATH_CONTROL_V75.py','seed':SEED,'instances_per_family':INSTANCES,'max_program_length':MAX_LEN,'nonmath_train_traces':len(TRAIN),'families':FAMILIES,'chains':CHAINS,'rows':rows,'grammar_mean_normalized_rank':g_mean,'unigram_mean_normalized_rank':u_mean,'shuffle_mean':sum(sh)/len(sh),'shuffle_p':shuffle_p,'label_permutation_mean':sum(lp)/len(lp),'label_permutation_p':label_p}
R['gates']={'all_families_solvable':all(x['successful_programs']>0 for x in rows),'beats_random_expectation':g_mean<1.0,'beats_unigram':g_mean<u_mean,'shuffle_p':shuffle_p<=GATESPEC['shuffle_p_max'],'label_permutation_p':label_p<=GATESPEC['label_permutation_p_max']}
R['verdict']='PASS_EXECUTABLE_MATH_CONTROL_V75' if all(R['gates'].values()) else 'MIXED_EXECUTABLE_MATH_CONTROL_V75'
(OUT/'RESULT.json').write_text(json.dumps(R,indent=2,default=list));print(json.dumps(R,indent=2,default=list))
