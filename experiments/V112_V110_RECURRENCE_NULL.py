from __future__ import annotations

import ast, json, math, random, subprocess, tempfile
from collections import Counter, defaultdict
from pathlib import Path

COMMIT='4257f44b0ff1181dedaedee6a447e133219fcebf'
REPO='https://github.com/jkoppel/QuixBugs.git'
TOKENS=['<','>','<=','>=','==','!=']
DUAL={'<':'>','>':'<','<=':'>=','>=':'<='}
OBS_COUNTS={'knapsack':2,'next_permutation':4,'quicksort':4}
TRIALS=200_000
SEED=11220260815
OUT=Path('artifacts/v112_v110_recurrence_null'); OUT.mkdir(parents=True,exist_ok=True)
OPNAME={ast.Lt:'<',ast.Gt:'>',ast.LtE:'<=',ast.GtE:'>=',ast.Eq:'==',ast.NotEq:'!='}

def run(cmd,cwd=None,timeout=120):
    p=subprocess.run(cmd,cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout)
    return p.returncode,p.stdout

def qkey(sig):
    s,t,sw=sig
    if s not in DUAL or t not in DUAL:return ('NON_ORDER',s,t,int(sw))
    a=(s,t,int(sw));b=(DUAL[s],DUAL[t],int(sw))
    return ('ORDER',)+min(a,b)

def source_ops(src):
    tree=ast.parse(src);out=[]
    for n in ast.walk(tree):
        if isinstance(n,ast.Compare) and len(n.ops)==1 and len(n.comparators)==1 and type(n.ops[0]) in OPNAME:
            out.append(OPNAME[type(n.ops[0])])
    return out

def universe(ops):
    U=[]
    for site,s in enumerate(ops):
        for sw in (False,True):
            for t in TOKENS:
                if not sw and t==s:continue
                sig=(s,t,int(sw))
                U.append({'site':site,'sig':sig,'q':qkey(sig)})
    return U

def stats(draws):
    groups=defaultdict(list)
    for program, recs in draws.items():
        for r in recs:
            if r['q'][0]=='ORDER':groups[r['q']].append((program,r['sig']))
    recurrent=[]
    for k,m in groups.items():
        progs={p for p,_ in m};lits={s for _,s in m}
        if len(progs)>=2:recurrent.append((k,m,progs,lits))
    diverse=[x for x in recurrent if len(x[3])>=2]
    return {
        'recurrent_count':len(recurrent),
        'diverse_recurrent_count':len(diverse),
        'max_programs':max([len(x[2]) for x in recurrent],default=0),
        'max_members':max([len(x[1]) for x in recurrent],default=0),
    }

def main():
    with tempfile.TemporaryDirectory(prefix='v112_') as td:
        root=Path(td)/'QuixBugs';c,o=run(['git','clone','--quiet',REPO,str(root)],timeout=180)
        if c:raise RuntimeError(o)
        c,o=run(['git','checkout','--quiet',COMMIT],cwd=root,timeout=60)
        if c:raise RuntimeError(o)
        U={}
        for p in OBS_COUNTS:
            src=(root/'python_programs'/f'{p}.py').read_text()
            U[p]=universe(source_ops(src))
        rng=random.Random(SEED)
        event=0
        rc=Counter();dc=Counter();mp=Counter();mm=Counter()
        for _ in range(TRIALS):
            draws={p:rng.sample(U[p],k) for p,k in OBS_COUNTS.items()}
            s=stats(draws)
            rc[s['recurrent_count']]+=1;dc[s['diverse_recurrent_count']]+=1;mp[s['max_programs']]+=1;mm[s['max_members']]+=1
            if s['recurrent_count']>=2 and s['diverse_recurrent_count']>=2:event+=1
        raw=event/TRIALS;p=(event+1)/(TRIALS+1);se=math.sqrt(raw*(1-raw)/TRIALS) if 0<raw<1 else 0.0
        R={
          'canonical_id':'V112_V110_RECURRENCE_NULL',
          'external_commit':COMMIT,
          'seed':SEED,'trials':TRIALS,
          'program_pass_counts':OBS_COUNTS,
          'candidate_universe_sizes':{p:len(u) for p,u in U.items()},
          'event_definition':'recurrent_count>=2 AND diverse_recurrent_count>=2',
          'event_count':event,'raw_frequency':raw,'plus_one_p':p,'mc_standard_error':se,
          'significant_at_0_05':p<=0.05,
          'secondary_distributions':{
             'recurrent_count':dict(sorted(rc.items())),
             'diverse_recurrent_count':dict(sorted(dc.items())),
             'max_programs':dict(sorted(mp.items())),
             'max_members':dict(sorted(mm.items())),
          },
          'interpretation':'Conditional post-V110 identity-randomization null only; not a population-level p-value.'
        }
        (OUT/'RESULT.json').write_text(json.dumps(R,indent=2,sort_keys=True)+'\n')
        print(json.dumps(R,indent=2,sort_keys=True))
if __name__=='__main__':main()
