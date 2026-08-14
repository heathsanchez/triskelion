# V55: natural historical two-generation compounding.
# Reuses V53's sealed historical-world preparation/localization machinery.
import json, sys
from collections import Counter
from pathlib import Path

# Importing V53 would execute it, so load definitions only through the marker preceding order=.
src=Path('experiments/METALOGIC_V53_HISTORICAL_CLEANROOM.py').read_text()
head=src.split("order=sorted(CANDIDATES",1)[0]
ns={'__name__':'v55_lib'}; exec(compile(head,'V53_LIB','exec'),ns)
for k,v in ns.items():
    if not k.startswith('__'): globals()[k]=v

SEED='V55_NATURAL_HISTORICAL_COMPOUNDING_20260814'
OUT=Path('artifacts/v55'); OUT.mkdir(parents=True,exist_ok=True)
MAX_READY=8

def obstruction(op): return bool(op and Counter([op['src']]) != Counter([op['dst']]))

def apply_op_all(repo,sites,op):
    """Try O on each matching localized site; retain verified failing states as residuals."""
    residuals=[]; solves=[]
    for s in sites:
        if s[-1]!=op['src']: continue
        reset(repo); mutate(s,op['dst']); ok,out=test(repo)
        rec={'site':[str(s[0].relative_to(repo)),s[1],s[2],s[-1]],'passes':ok,'tail':out[-300:]}
        (solves if ok else residuals).append(rec)
    reset(repo); return residuals,solves

def search_second_from_residual(repo,sites,op,residual_site):
    """Recreate O1 residual, then search exactly one additional rewrite over localized sites."""
    base_site=None
    rel,row,col,_=residual_site['site']
    for s in sites:
        if str(s[0].relative_to(repo))==rel and s[1]==row and s[2]==col and s[-1]==op['src']:
            base_site=s; break
    if base_site is None:return [],[]
    wins=[]
    for s in sites:
        for dst in DESTS:
            if dst==s[-1]: continue
            reset(repo); mutate(base_site,op['dst'])
            # coordinates may shift only on the O1 line; re-localize target by rel,row,col/src where possible
            p=repo/str(s[0].relative_to(repo)); candidates=[]
            try:
                ts=list(tokenize.generate_tokens(io.StringIO(p.read_text(errors='ignore')).readline))
                candidates=[t for t in ts if t.type==tokenize.OP and t.string==s[-1] and t.start[0]==s[1]]
            except: pass
            # Prefer same start column; otherwise skip rather than guess.
            tt=[t for t in candidates if t.start[1]==s[2]]
            if len(tt)!=1: continue
            t=tt[0]; ss=(p,t.start[0],t.start[1],t.end[1],t.string)
            mutate(ss,dst); ok,_=test(repo)
            if ok:wins.append((s[-1],dst,str(p.relative_to(repo)),s[1],s[2]))
    reset(repo)
    pairs=sorted(set((a,b) for a,b,*_ in wins)); return pairs,wins

order=sorted(CANDIDATES,key=lambda x:H('|'.join(x)))
pre={'seed':SEED,'candidate_order':order,'ready_cap':MAX_READY,'max_sites':MAX_SITES,'old_generators':OLD,'human_fix_forbidden':True}
(OUT/'PRECOMMIT.json').write_text(json.dumps(pre,indent=2)); print('PRECOMMIT',json.dumps(pre,sort_keys=True))

# Phase 0: buggy commits/tests only.
ready=[]; screen=[]
for pr,bg,py in order:
    ev={'project':pr,'bug':bg,'python':py}; rc,o,repo=checkout(pr,bg)
    if rc or not repo.exists():ev['status']='CHECKOUT_FAIL';screen.append(ev);continue
    good,so=setup(repo,py)
    if not good:ev['status']='SETUP_FAIL';ev['tail']=so[-300:];screen.append(ev);continue
    base,bout=test(repo);ev['baseline_pass']=base
    if base:ev['status']='NONREPRODUCING';screen.append(ev);continue
    ss=candidate_sites(repo,bout);ev['site_count']=len(ss)
    if not ss:ev['status']='NO_SOURCE_OPERATOR_SITE';screen.append(ev);continue
    ev['status']='READY';ready.append((pr,bg,py));screen.append(ev)
    if len(ready)>=MAX_READY:break
(OUT/'READY.json').write_text(json.dumps({'screen':screen,'selected':ready},indent=2))

O1=None; origin=None; target=None; events=[]
for idx,(pr,bg,py) in enumerate(ready,1):
    rc,o,repo=checkout(pr,bg); good,so=setup(repo,py)
    if rc or not good:events.append({'episode':idx,'project':pr,'bug':bg,'status':'PREP_FAIL'});continue
    base,bout=test(repo); ss=candidate_sites(repo,bout)
    ev={'episode':idx,'project':pr,'bug':bg,'site_count':len(ss)}
    if O1 is None:
        pairs,wins=construct(repo,ss); ev['cold_pairs']=pairs
        if len(pairs)==1:
            cand={'kind':'TOKEN_REWRITE','src':pairs[0][0],'dst':pairs[0][1]}
            if obstruction(cand):
                O1=cand;origin={'project':pr,'bug':bg,'episode':idx};ev['status']='O1_FORMED';ev['O1']=O1
            else:ev['status']='NO_NOVELTY'
        else:ev['status']='NO_UNIQUE_O1'
    elif pr!=origin['project']:
        # Frozen cold horizon: exactly one rewrite from A0.
        cold_pairs,cold_wins=construct(repo,ss); ev['cold_pairs']=cold_pairs
        residuals,solves=apply_op_all(repo,ss,O1);ev['O1_residuals']=residuals;ev['O1_solves']=solves
        # Only a verified still-failing O1 application may expose O2.
        warm=[]
        for residual in residuals:
            pairs,wins=search_second_from_residual(repo,ss,O1,residual)
            if len(pairs)==1:
                O2={'kind':'TOKEN_REWRITE','src':pairs[0][0],'dst':pairs[0][1]}
                if O2!=O1 and obstruction(O2):warm.append((residual,O2,wins))
        ev['warm_candidates']=[{'residual':r,'O2':o2,'wins':w[:10]} for r,o2,w in warm]
        if len(cold_pairs)==0 and len(warm)==1:
            residual,O2,_=warm[0]
            # Final causal replay.
            reset(repo); _,bout=test(repo); ss2=candidate_sites(repo,bout)
            rel,row,col,_=residual['site']; s1=[s for s in ss2 if str(s[0].relative_to(repo))==rel and s[1]==row and s[2]==col and s[-1]==O1['src']]
            final=False; ablated=False; mid=False
            if len(s1)==1:
                mutate(s1[0],O1['dst']); mid=test(repo)[0]
                # Re-localize and try unique O2 matching site; success itself identifies causal application.
                post_out=test(repo)[1]; post_sites=candidate_sites(repo,post_out)
                hits=[]
                for s in post_sites:
                    if s[-1]!=O2['src']:continue
                    # preserve O1 residual state by reset+reapply
                    reset(repo); _,bo=test(repo); base_sites=candidate_sites(repo,bo)
                    q=[x for x in base_sites if str(x[0].relative_to(repo))==rel and x[1]==row and x[2]==col and x[-1]==O1['src']]
                    if len(q)!=1:continue
                    mutate(q[0],O1['dst'])
                    # find O2 by path,row,col
                    p=repo/str(s[0].relative_to(repo)); ts=list(tokenize.generate_tokens(io.StringIO(p.read_text(errors='ignore')).readline))
                    qq=[t for t in ts if t.type==tokenize.OP and t.string==O2['src'] and t.start==(s[1],s[2])]
                    if len(qq)!=1:continue
                    mutate((p,qq[0].start[0],qq[0].start[1],qq[0].end[1],qq[0].string),O2['dst'])
                    if test(repo)[0]:hits.append([str(p.relative_to(repo)),s[1],s[2]])
                final=len(hits)==1
                # Ablation: O2 alone from original buggy state.
                reset(repo); _,bo=test(repo); bs=candidate_sites(repo,bo); ah=[]
                for s in bs:
                    if s[-1]!=O2['src']:continue
                    reset(repo); mutate(s,O2['dst']);
                    if test(repo)[0]:ah.append(1)
                ablated=bool(ah)
            ev['causal']={'cold':False,'after_O1_only':mid,'after_O1_O2':final,'O1_ablated_O2_present':ablated}
            if (not mid) and final and (not ablated):
                target={'project':pr,'bug':bg,'episode':idx,'O2':O2};ev['status']='TWO_GENERATION_CAUSAL';events.append(ev);break
        ev.setdefault('status','NO_TWO_GENERATION_EVENT')
    else:ev['status']='SAME_PROJECT_CONTROL'
    events.append(ev)

# Human-fix metadata only after termination.
audit={}
for role,obj in [('origin',origin),('target',target)]:
    if obj:
        bi=info(BIP/'projects'/obj['project']/'bugs'/obj['bug']/'bug.info');audit[role]={'project':obj['project'],'bug':obj['bug'],'buggy_commit':bi.get('buggy_commit_id'),'fixed_commit':bi.get('fixed_commit_id')}
projects=set(x[0] for x in ready)
gates={
 'at_least_two_ready_two_projects':len(ready)>=2 and len(projects)>=2,
 'O1_constructed_outside_old_closure':O1 is not None and obstruction(O1),
 'later_different_project_target':bool(target and origin and target['project']!=origin['project']),
 'cold_horizon_zero':bool(target),
 'O1_progress_not_success':bool(target),
 'unique_new_O2_after_O1':bool(target),
 'O2_outside_old_closure':bool(target and obstruction(target['O2'])),
 'O1_plus_O2_passes':bool(target),
 'O1_ablation_fails':bool(target),
 'fix_withheld_until_terminal':True,
}
adequate=len(ready)>=2 and len(projects)>=2
verdict='PASS_V55_NATURAL_HISTORICAL_COMPOUNDING' if all(gates.values()) else ('FAIL_V55_NATURAL_HISTORICAL_COMPOUNDING' if adequate else 'INCOMPLETE_V55_NATURAL_HISTORICAL_COMPOUNDING')
R={'protocol':SEED,'precommit':pre,'screen':screen,'ready':ready,'events':events,'O1':O1,'origin':origin,'target':target,'terminal_fix_metadata':audit,'gates':gates,'coverage_ge_6':len(ready)>=6,'verdict':verdict,'claim_boundary':'Natural historical BugsInPy worlds; fixes sealed until terminal audit. Generic token-rewrite constructor and traceback localization remain supplied.'}
(OUT/'RESULT.json').write_text(json.dumps(R,indent=2));print(json.dumps(R,indent=2))
