#!/usr/bin/env python3
import hashlib,json,os,shutil,subprocess
from pathlib import Path
ROOT=Path('checker'); EXE=ROOT/'lean_checker'; VOWC=(ROOT/'vowc').resolve(); ARENA=Path('arena-tests'); BLIND=Path('blind-di-v2'); MANIFEST=Path('/tmp/blind_manifest_v2_eval.json'); CANDIDATES=BLIND/'candidates.json'; PRECOMMIT=BLIND/'precommit.json'; EXPOSED_META=BLIND/'exposed.json'; OUT=BLIND/'result.json'; REGRESSION_N=32

def run_case(exe,rel,timeout=30):
    p=(ARENA/rel).resolve()
    try:
        cp=subprocess.run([str(Path(exe).resolve()),str(p)],capture_output=True,text=True,timeout=timeout); rc=cp.returncode; out,err=cp.stdout,cp.stderr
    except subprocess.TimeoutExpired as e: rc=124; out=e.stdout or ''; err=e.stderr or ''
    status='accept' if rc==0 else ('reject' if rc==1 else ('decline' if rc==2 else 'error'))
    return {'rc':rc,'status':status,'stdout_tail':out[-2000:] if isinstance(out,str) else '','stderr_tail':err[-2000:] if isinstance(err,str) else ''}

def correct(x,expected): return x['status']==expected

def build_checker():
    env=os.environ.copy(); env['VOWC']=str(VOWC)
    cp=subprocess.run(['bash','scripts/build.sh'],cwd=ROOT,env=env,capture_output=True,text=True,timeout=300)
    return cp.returncode==0,cp.stdout[-5000:],cp.stderr[-5000:]

def apply_patch(edit):
    p=ROOT/edit['path']; original=p.read_text(); lines=original.splitlines(); start=int(edit['start_line']); end=int(edit['end_line']); new=str(edit['new_text']).splitlines()
    if start<1 or end<start or end>len(lines) or end-start+1>40: raise ValueError('invalid frozen range')
    if len(new)>80 or len(str(edit['new_text']))>12000: raise ValueError('replacement exceeds frozen budget')
    old=lines[start-1:end]
    if '\n'.join(old).rstrip('\n')==str(edit['new_text']).rstrip('\n'): raise ValueError('noop')
    updated=lines[:start-1]+new+lines[end:]
    p.write_text('\n'.join(updated)+('\n' if original.endswith('\n') else ''))
    return p,original,hashlib.sha256(('\n'.join(old)+'\n').encode()).hexdigest()

def restore(path,text): path.write_text(text)
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    rows=json.loads(MANIFEST.read_text()); pre=json.loads(PRECOMMIT.read_text()); exposed=json.loads(EXPOSED_META.read_text()); candidates=json.loads(CANDIDATES.read_text())
    canonical=json.dumps(rows,separators=(',',':'),sort_keys=True).encode(); commitment=hashlib.sha256(canonical).hexdigest(); commitment_ok=commitment==pre['ordered_manifest_sha256']
    if not commitment_ok: raise SystemExit('corpus commitment mismatch')
    exp_idx=next((i for i,r in enumerate(rows) if r['sha256']==exposed['sha256'] and r['rel']==exposed['rel']),None)
    if exp_idx is None: raise SystemExit('exposed case absent from reproduced manifest')
    exp=rows[exp_idx]; base_exp=run_case(EXE,exp['rel'])
    if correct(base_exp,exp['expected']): raise SystemExit('V2 exposed case is no longer a baseline failure')
    frozen=Path('/tmp/lean_checker_di_v2_frozen'); shutil.copy2(EXE,frozen); os.chmod(frozen,0o755)
    regression=[]; suffix_base={}
    for r in rows[exp_idx+1:]:
        b=run_case(frozen,r['rel']); suffix_base[r['rel']]=b
        if correct(b,r['expected']) and len(regression)<REGRESSION_N: regression.append(r)
        if len(regression)==REGRESSION_N: break
    if len(regression)!=REGRESSION_N: raise SystemExit('insufficient hidden regression cases')
    evaluations=[]; selected=None; selected_path=None; selected_original=None; selected_old_sha=None
    for row in candidates['candidates']:
        ev={'index':row['index'],'admissible':bool(row['admissible']),'candidate_sha256':row['raw_sha256']}
        if not row['admissible'] or not isinstance(row.get('parsed'),dict): ev['outcome']='inadmissible'; evaluations.append(ev); continue
        edit=row['parsed']
        try: path,original,old_sha=apply_patch(edit)
        except Exception as e: ev['outcome']='apply_failed'; ev['error']=repr(e); evaluations.append(ev); continue
        ok,bout,berr=build_checker(); ev['build_ok']=ok
        if not ok: ev['outcome']='build_failed'; ev['build_stderr_tail']=berr; restore(path,original); evaluations.append(ev); continue
        q=run_case(EXE,exp['rel']); ev['exposed_status']=q['status']; ev['exposed_fixed']=correct(q,exp['expected'])
        if not ev['exposed_fixed']: ev['outcome']='exposed_not_fixed'; restore(path,original); evaluations.append(ev); continue
        bad=0
        for rr in regression:
            z=run_case(EXE,rr['rel']); bad+=0 if correct(z,rr['expected']) else 1
        ev['hidden_regression_passed']=REGRESSION_N-bad; ev['hidden_regression_total']=REGRESSION_N; ev['hidden_regressions']=bad
        if bad: ev['outcome']='hidden_regression_reject'; restore(path,original); evaluations.append(ev); continue
        ev['outcome']='retained'; evaluations.append(ev); selected=row; selected_path=path; selected_original=original; selected_old_sha=old_sha; break
    result={'protocol':'DI_BLIND_V2_AUTONOMOUS_CONSTRUCTION','corpus_commitment_reproduced':commitment_ok,'ordered_manifest_sha256':commitment,'base_model':candidates['base_model'],'base_weight_updates':0,'prompt_sha256':candidates['prompt_sha256'],'patch_schema':candidates.get('patch_schema'),'admissible_candidate_count':candidates['admissible_count'],'exposed':{'rank':exp_idx+1,'order':exp['order'],'expected':exp['expected'],'baseline_status':base_exp['status'],'sha256':exp['sha256']},'candidate_evaluations':evaluations,'selected':None,'protected_transfer':None,'ablation':None}
    if selected is None:
        result['verdict']='VALID_NEGATIVE_V2_NO_CONSTRUCTION'; OUT.write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps(result,indent=2)); return
    edit=selected['parsed']; developed=Path('/tmp/lean_checker_di_v2_developed'); shutil.copy2(EXE,developed); os.chmod(developed,0o755)
    result['selected']={'generation_index':selected['index'],'proposal_sha256':selected['raw_sha256'],'hypothesis':edit.get('hypothesis',''),'path':edit['path'],'start_line':int(edit['start_line']),'end_line':int(edit['end_line']),'new_text':edit['new_text'],'replaced_range_sha256':selected_old_sha,'developed_source_sha256':sha(selected_path),'hidden_regression':f'{REGRESSION_N}/{REGRESSION_N}'}
    regression_rels={r['rel'] for r in regression}; transfers=[]; protected=[]
    for r in rows[exp_idx+1:]:
        if r['rel'] in regression_rels: continue
        b=suffix_base.get(r['rel']) or run_case(frozen,r['rel']); d=run_case(developed,r['rel']); b_ok=correct(b,r['expected']); d_ok=correct(d,r['expected']); tr=(not b_ok) and d_ok
        protected.append({'order':r['order'],'sha256':r['sha256'],'expected':r['expected'],'baseline_status':b['status'],'developed_status':d['status'],'transfer_success':tr})
        if tr: transfers.append(r)
    result['protected_transfer']={'evaluated':len(protected),'baseline_incorrect':sum(x['baseline_status']!=x['expected'] for x in protected),'developed_incorrect':sum(x['developed_status']!=x['expected'] for x in protected),'transfer_success_count':len(transfers),'rows':protected}
    restore(selected_path,selected_original); ok0,_,err0=build_checker(); remove_rows=[]
    if ok0:
        for r in transfers:
            q=run_case(EXE,r['rel']); baseline=(suffix_base.get(r['rel']) or run_case(frozen,r['rel']))['status']; remove_rows.append({'order':r['order'],'status':q['status'],'returns_to_baseline':q['status']==baseline})
    path2,orig2,oldsha2=apply_patch(edit); ok1,_,err1=build_checker(); restore_rows=[]
    if ok1:
        for r in transfers:
            q=run_case(EXE,r['rel']); restore_rows.append({'order':r['order'],'status':q['status'],'correct_restored':correct(q,r['expected'])})
    remove_pass=ok0 and len(remove_rows)==len(transfers) and all(x['returns_to_baseline'] for x in remove_rows); restore_pass=ok1 and len(restore_rows)==len(transfers) and all(x['correct_restored'] for x in restore_rows)
    result['ablation']={'remove_build_ok':ok0,'restore_build_ok':ok1,'remove_all_return_to_baseline':remove_pass,'restore_all_return_to_correct':restore_pass,'remove_rows':remove_rows,'restore_rows':restore_rows,'remove_build_error_tail':'' if ok0 else err0,'restore_build_error_tail':'' if ok1 else err1}
    result['verdict']='PASS_DI_BLIND_V2_AUTONOMOUS_CONSTRUCTION' if transfers and remove_pass and restore_pass else 'PARTIAL_V2_EXPOSED_ONLY'
    OUT.write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps(result,indent=2))
if __name__=='__main__': main()
