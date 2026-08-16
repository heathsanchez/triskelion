from __future__ import annotations
import argparse, hashlib, json, re, tempfile, time
from pathlib import Path

import acquire_bugsinpy_capability as acq
import bugsinpy_four_arm_v4 as exact
from river_qwen35_provider import Qwen35ChatRiverProvider

acq.native_test = exact.native_test
SEEDS=[20260815,20260816,20260817,20260818]
MAX_TOKENS=2048
MODEL='Qwen/Qwen3.5-9B'

def patch_path(root:Path, project:str, bug:int)->Path:
    return root/'projects'/project/'bugs'/str(bug)/'bug_patch.txt'

def no_test_edits(diff:str):
    for p in re.findall(r'^\+\+\+ b/(.+)$',diff,flags=re.M):
        q=p.lower().split('/')
        if 'test' in q or 'tests' in q or Path(p).name.lower().startswith('test_') or Path(p).name.lower().endswith('_test.py'):
            raise ValueError('test edit forbidden: '+p)

def extract_diff(text:str)->str:
    blocks=re.findall(r'```(?:diff)?\s*(.*?)```',text,flags=re.S|re.I)
    s=(blocks[0] if len(blocks)==1 else text).strip()+'\n'
    if 'diff --git ' not in s and not s.startswith('--- '): raise ValueError('not unified diff')
    no_test_edits(s); return s

def synth_o1(provider, bugs:Path)->dict:
    with tempfile.TemporaryDirectory(prefix='v146c-o1-') as td:
        w=acq.checkout_buggy(bugs,'httpie',5,Path(td))
        base=exact.native_test(bugs,w)
        if base.get('infrastructure_error') or base.get('passed'):
            return {'status':'R10_OR_REPRODUCTION','baseline':base}
        diff=patch_path(bugs,'httpie',5).read_text(encoding='utf-8')
        no_test_edits(diff); acq.apply_diff(w,diff)
        fixed=exact.native_test(bugs,w)
        if fixed.get('infrastructure_error') or not fixed.get('passed'):
            return {'status':'R10_OR_INTERVENTION_NOT_VERIFIED','baseline':base,'fixed':fixed}
        payload={'failure_class':acq.failure_class(base.get('test_output','')),
                 'failing_test_tail':base.get('test_output','')[-6000:],
                 'successful_intervention':diff,
                 'changed_files':re.findall(r'^\+\+\+ b/(.+)$',diff,flags=re.M)}
        prompt=('Compress this ONE independently authored, native-verified repair into one concise portable repair policy. '
                'Do not name the source project, bug ID, test path, or copy a case-specific patch. '
                'State only reusable diagnostic and repair guidance for a future unrelated repository.\n\n'+json.dumps(payload,sort_keys=True))
        r=provider.sample(prompt,seed=20269815,max_tokens=MAX_TOKENS)
        policy=r.text.strip()
        if not policy:
            return {'status':'O1_REPRESENTATION_REJECTED_EMPTY','baseline':base,'fixed':fixed,'response':r.to_dict()}
        low=policy.lower()
        forbidden=['httpie','httpie/5']
        leaks=[x for x in forbidden if x in low]
        if leaks:
            return {'status':'O1_REPRESENTATION_REJECTED_SOURCE_LEAK','leaks':leaks,'baseline':base,'fixed':fixed,
                    'response':r.to_dict(),'raw_policy_sha256':hashlib.sha256(policy.encode()).hexdigest()}
        artifact={'capability_id':'V146C.O1.RAW_POLICY','policy':policy,'source_case':'httpie/5',
                  'source_diff_sha256':hashlib.sha256(diff.encode()).hexdigest(),
                  'synthesis_prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest(),
                  'policy_sha256':hashlib.sha256(policy.encode()).hexdigest(),
                  'policy_bytes':len(policy.encode()),'response':r.to_dict(),'source_verified':True}
        return {'status':'O1_FROZEN','o1':artifact,'baseline':base,'fixed':fixed}

def sham(text:str)->str:
    parts=re.split(r'(\s+)',text)
    token_idx=list(range(0,len(parts),2))
    tokens=[parts[i] for i in token_idx]
    tokens.reverse()
    for i,tok in zip(token_idx,tokens): parts[i]=tok
    out=''.join(parts)
    assert len(out.encode())==len(text.encode())
    return out

def run_youtube(provider, bugs:Path, arm:str, seed:int, memory:str)->dict:
    t0=time.perf_counter()
    with tempfile.TemporaryDirectory(prefix='v146c-o2-') as td:
        w=acq.checkout_buggy(bugs,'youtube-dl',32,Path(td))
        base=exact.native_test(bugs,w)
        if base.get('infrastructure_error'): return {'status':'R10','baseline':base,'wall_ms':(time.perf_counter()-t0)*1000}
        if base.get('passed'): return {'status':'REPRODUCTION_NEGATIVE','baseline':base,'wall_ms':(time.perf_counter()-t0)*1000}
        context,files=acq.collect_context(w,base.get('test_output',''))
        prompt=acq.visible_request('youtube-dl',32,base.get('test_output',''),context)
        if memory: prompt+='\n\nRETAINED PRIOR VERIFIED REPAIR POLICY:\n'+memory
        r=provider.sample(prompt,seed=seed,max_tokens=MAX_TOKENS)
        row={'arm':arm,'seed':seed,'prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest(),
             'response':r.to_dict(),'response_bytes':len(r.text.encode()),'context_files':files,'baseline':base}
        try:
            diff=extract_diff(r.text); row['diff_sha256']=hashlib.sha256(diff.encode()).hexdigest(); acq.apply_diff(w,diff)
        except Exception as e:
            row.update(status='PATCH_INVALID',patch_error=f'{type(e).__name__}: {e}',wall_ms=(time.perf_counter()-t0)*1000); return row
        verdict=exact.native_test(bugs,w); row['verdict']=verdict
        if verdict.get('infrastructure_error'): row['status']='R10'
        elif verdict.get('passed'): row['status']='VERIFIED_REPAIR'; row['successful_diff']=diff
        else: row['status']='VERIFIER_FAIL'
        row['wall_ms']=(time.perf_counter()-t0)*1000
        return row

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--bugsinpy',type=Path,required=True); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
    a.out.mkdir(parents=True,exist_ok=True)
    provider=Qwen35ChatRiverProvider(MODEL)
    o1=synth_o1(provider,a.bugsinpy)
    (a.out/'O1_FREEZE.json').write_text(json.dumps(o1,indent=2,sort_keys=True)+'\n')
    if o1.get('status')!='O1_FROZEN':
        verdict='R10_INCONCLUSIVE_O1_FREEZE' if str(o1.get('status','')).startswith('R10') else 'NEGATIVE_O1_REPRESENTATION_REJECTED'
        (a.out/'V146_RESULT.json').write_text(json.dumps({'canonical_id':'V146C_NATURAL_O1_O2_RAW_POLICY','verdict':verdict,'o1_status':o1.get('status'),'claim_boundary':'No O2 arms run.'},indent=2,sort_keys=True)+'\n')
        print(json.dumps({'verdict':verdict,'o1_status':o1.get('status')},indent=2)); return
    policy=o1['o1']['policy']; sham_policy=sham(policy)
    (a.out/'O1_POLICY.txt').write_text(policy+'\n'); (a.out/'SHAM_POLICY.txt').write_text(sham_policy+'\n')
    rows=[]
    for arm,mem in [('D',''),('O1',policy),('SHAM',sham_policy)]:
        for seed in SEEDS:
            row=run_youtube(provider,a.bugsinpy,arm,seed,mem); rows.append(row)
            (a.out/f'{arm}_{seed}.json').write_text(json.dumps(row,indent=2,sort_keys=True)+'\n')
    infra=any(r['status']=='R10' for r in rows)
    succ={arm:sum(r['status']=='VERIFIED_REPAIR' for r in rows if r['arm']==arm) for arm in ['D','O1','SHAM']}
    first={arm:next((i for i,r in enumerate([x for x in rows if x['arm']==arm]) if r['status']=='VERIFIED_REPAIR'),None) for arm in succ}
    if infra: verdict='R10_INCONCLUSIVE'
    elif succ['O1']>0 and succ['D']==0 and succ['SHAM']==0: verdict='PASS_V146C_O1_CAUSALLY_ENABLES_O2_REACHABILITY'
    elif succ['O1']>0 and succ['D']>0:
        verdict='FRONTIER_EFFICIENCY_OR_NULL' if (first['O1'] is not None and first['D'] is not None and first['O1']<first['D']) else 'NULL_O2_ALREADY_COLD_REACHABLE'
    else: verdict='NEGATIVE_O1_DOES_NOT_ENABLE_O2'
    result={'canonical_id':'V146C_NATURAL_O1_O2_RAW_POLICY','model':MODEL,'seeds':SEEDS,'max_tokens':MAX_TOKENS,
            'o1_policy_sha256':o1['o1']['policy_sha256'],'o1_bytes':len(policy.encode()),'sham_bytes':len(sham_policy.encode()),
            'success_counts':succ,'first_success_index':first,'verdict':verdict,
            'claim_boundary':'Only a strong PASS licenses a new preregistration to promote the verified O1-assisted youtube episode into O2. No pandas/O3 claim.'}
    (a.out/'V146_RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n'); print(json.dumps(result,indent=2,sort_keys=True))
if __name__=='__main__': main()
