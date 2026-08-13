import hashlib, io, json, os, re, shlex, shutil, subprocess, sys, time, tokenize
from collections import Counter
from pathlib import Path

SEED='V52_HISTORICAL_BUG_STREAM_20260814'
ROOT=Path('/tmp/BugsInPy')
WORK=Path('/tmp/v52_worlds')
OUT=Path('artifacts/v52'); OUT.mkdir(parents=True,exist_ok=True); WORK.mkdir(parents=True,exist_ok=True)
MAX_EPISODES=10
MAX_REWRITE_ATTEMPTS=72
MAX_TEST_SECONDS=45
OLD_GENERATORS=['IDENTITY','REVERSE_WINDOW','ROTATE_LEFT','ROTATE_RIGHT','SWAP_ADJACENT']
DESTS=sorted({s for s in tokenize.EXACT_TOKEN_TYPES if len(s)<=2})
FORBIDDEN_NAME='bug_patch.txt'

def H(s): return hashlib.sha256((SEED+'|'+s).encode()).hexdigest()
def run(cmd,cwd=None,timeout=120,env=None):
    try:
        p=subprocess.run(cmd,cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout,env=env,shell=isinstance(cmd,str))
        return p.returncode,p.stdout
    except subprocess.TimeoutExpired as e:
        return 124,(e.stdout or '')+(e.stderr or '') if isinstance(e.stdout,str) else 'TIMEOUT'
def parse_kv(path):
    d={}
    for ln in path.read_text(errors='ignore').splitlines():
        m=re.match(r'([A-Za-z_]+)="(.*)"\s*$',ln.strip())
        if m:d[m.group(1)]=m.group(2)
    return d
def version_tuple(v):
    try:return tuple(int(x) for x in re.findall(r'\d+',v)[:2])
    except:return (0,0)
def eligible_stream():
    eps=[]
    for proj in sorted((ROOT/'projects').iterdir()):
        if not proj.is_dir() or not (proj/'project.info').exists(): continue
        pi=parse_kv(proj/'project.info')
        if pi.get('status','OK')!='OK' or not pi.get('github_url'): continue
        bugs=proj/'bugs'
        if not bugs.exists(): continue
        for b in sorted(bugs.iterdir(),key=lambda p:p.name):
            info=b/'bug.info'
            if not info.exists(): continue
            bi=parse_kv(info)
            if version_tuple(bi.get('python_version','0')) < (3,8): continue
            if not bi.get('buggy_commit_id') or not bi.get('fixed_commit_id'): continue
            # Metadata only: do not read bug_patch.txt.
            eps.append({'project':proj.name,'bug':b.name,'url':pi['github_url'],'python':bi.get('python_version'),'buggy':bi['buggy_commit_id'],'fixed':bi['fixed_commit_id'],'test_file':bi.get('test_file',''),'meta_dir':str(b)})
    return sorted(eps,key=lambda e:H(e['project']+'|'+e['bug']))[:MAX_EPISODES]
def make_env(repo,pyver,meta):
    venv=repo/'.venv'
    rc,out=run(['uv','venv','--python',pyver,str(venv)],cwd=repo,timeout=180)
    if rc: return False,'uv_venv:'+out[-1200:]
    py=venv/'bin/python'; pip=[str(py),'-m','pip']
    # Ensure pip exists in managed env.
    run(['uv','pip','install','--python',str(py),'pip','setuptools','wheel'],cwd=repo,timeout=120)
    req=Path(meta)/'requirements.txt'
    if req.exists() and req.read_text(errors='ignore').strip():
        rc,out=run(['uv','pip','install','--python',str(py),'-r',str(req)],cwd=repo,timeout=240)
        if rc:return False,'requirements:'+out[-1200:]
    setup=Path(meta)/'setup.sh'
    env=os.environ.copy(); env['VIRTUAL_ENV']=str(venv); env['PATH']=str(venv/'bin')+os.pathsep+env['PATH']
    if setup.exists() and setup.read_text(errors='ignore').strip():
        rc,out=run('bash '+shlex.quote(str(setup)),cwd=repo,timeout=180,env=env)
        if rc:return False,'setup:'+out[-1200:]
    return True,env
def prepare(ep):
    repo=WORK/(ep['project']+'_'+ep['bug'])
    if repo.exists(): shutil.rmtree(repo)
    rc,out=run(['git','clone','-q',ep['url'],str(repo)],timeout=180)
    if rc:return None,'clone:'+out[-1000:]
    rc,out=run(['git','checkout','-q',ep['buggy']],cwd=repo,timeout=60)
    if rc:return None,'checkout:'+out[-1000:]
    # Import only fixed-version test files, never production files or human patch.
    for tf in [x for x in ep['test_file'].split(';') if x]:
        rc,blob=run(['git','show',ep['fixed']+':'+tf],cwd=repo,timeout=30)
        if rc:return None,'fixed_test_missing:'+tf
        p=repo/tf; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(blob)
    ok,env=make_env(repo,ep['python'],ep['meta_dir'])
    if not ok:return None,env
    return repo,env
def test_cmd(ep,repo,env):
    rt=Path(ep['meta_dir'])/'run_test.sh'
    cmds=[x.strip() for x in rt.read_text(errors='ignore').splitlines() if x.strip() and not x.strip().startswith('#')]
    if not cmds:return False,'NO_TEST_CMD'
    full=' && '.join(cmds)
    rc,out=run(full,cwd=repo,timeout=MAX_TEST_SECONDS,env=env)
    return rc==0,out
def trace_locations(out,repo,tests):
    hits=[]; seen=set()
    pats=[r'File "([^"]+\.py)", line (\d+)',r'(^|\n)([^\n :]+\.py):(\d+):']
    for m in re.finditer(pats[0],out):
        p=Path(m.group(1)); n=int(m.group(2));
        if not p.is_absolute(): p=repo/p
        try:p=p.resolve()
        except:continue
        if str(p).startswith(str(repo.resolve())) and p.exists() and not any(str(p).endswith(t) for t in tests):
            k=(str(p),n)
            if k not in seen:seen.add(k);hits.append(k)
    for m in re.finditer(pats[1],out):
        p=repo/m.group(2); n=int(m.group(3))
        try:p=p.resolve()
        except:continue
        if str(p).startswith(str(repo.resolve())) and p.exists() and not any(str(p).endswith(t) for t in tests):
            k=(str(p),n)
            if k not in seen:seen.add(k);hits.append(k)
    return hits[:6]
def op_sites_on_lines(path,lines):
    text=path.read_text(errors='ignore'); ts=list(tokenize.generate_tokens(io.StringIO(text).readline)); out=[]
    L=set(lines)
    for t in ts:
        if t.type==tokenize.OP and t.start[0] in L:
            out.append((t.start[0],t.start[1],t.end[1],t.string))
    return out
def rewrite(path,site,dst):
    row,c0,c1,src=site; lines=path.read_text().splitlines(True); line=lines[row-1]; lines[row-1]=line[:c0]+dst+line[c1:]; path.write_text(''.join(lines)); return line.strip()
def old_closure_obstructs(src,dst):
    # Every old generator only permutes token positions, hence preserves token-value multiset.
    return src!=dst and Counter([src])!=Counter([dst])
def discover_repairs(ep,repo,env,failout):
    tests=[x for x in ep['test_file'].split(';') if x]; locs=trace_locations(failout,repo,tests)
    grouped={}
    for p,n in locs:grouped.setdefault(p,[]).append(n)
    candidates=[]
    for ps,ls in grouped.items():
        p=Path(ps); original=p.read_bytes()
        for site in op_sites_on_lines(p,ls):
            src=site[3]
            for dst in DESTS:
                if dst==src:continue
                if len(candidates)>=MAX_REWRITE_ATTEMPTS:break
                p.write_bytes(original)
                try:line=rewrite(p,site,dst)
                except Exception:continue
                ok,_=test_cmd(ep,repo,env)
                candidates.append({'file':str(p.relative_to(repo)),'site':list(site[:3]),'src':src,'dst':dst,'line':line,'pass':ok})
            if len(candidates)>=MAX_REWRITE_ATTEMPTS:break
        p.write_bytes(original)
        if len(candidates)>=MAX_REWRITE_ATTEMPTS:break
    return locs,candidates
def try_operator(ep,repo,env,failout,op):
    tests=[x for x in ep['test_file'].split(';') if x]; locs=trace_locations(failout,repo,tests); grouped={}
    for p,n in locs:grouped.setdefault(p,[]).append(n)
    wins=[]
    for ps,ls in grouped.items():
        p=Path(ps); original=p.read_bytes()
        for site in op_sites_on_lines(p,ls):
            if site[3]!=op['src']:continue
            p.write_bytes(original)
            try:line=rewrite(p,site,op['dst'])
            except:continue
            ok,_=test_cmd(ep,repo,env)
            if ok:wins.append({'file':str(p.relative_to(repo)),'site':list(site[:3]),'line':line})
        p.write_bytes(original)
    return wins

stream=eligible_stream(); result={'protocol':SEED,'forbidden_patch_name':FORBIDDEN_NAME,'stream':[{k:e[k] for k in ('project','bug','python','buggy','fixed','test_file')} for e in stream],'episodes':[],'operator':None,'formation':None,'reuse':None,'verdict':'NO_FORMATION'}
operator=None; formation_project=None
for idx,ep in enumerate(stream,1):
    rec={'index':idx,'project':ep['project'],'bug':ep['bug']}
    repo,env=prepare(ep)
    if repo is None:
        rec.update({'status':'INFRA_NEGATIVE','detail':str(env)[-800:]}); result['episodes'].append(rec); continue
    ok,out=test_cmd(ep,repo,env)
    rec['baseline_pass']=ok
    if ok:
        rec['status']='NONREPRODUCING_NEGATIVE'; result['episodes'].append(rec); continue
    if operator is None:
        locs,cands=discover_repairs(ep,repo,env,out)
        wins=[c for c in cands if c['pass']]
        pairs=sorted(set((w['src'],w['dst']) for w in wins))
        rec.update({'trace_locations':[(str(Path(p).relative_to(repo)),n) for p,n in locs],'attempts':len(cands),'winning_pairs':pairs})
        if len(pairs)==1:
            src,dst=pairs[0]
            if old_closure_obstructs(src,dst):
                operator={'kind':'TOKEN_REWRITE','src':src,'dst':dst,'old_closure_invariant':'token_value_multiset'}
                formation_project=ep['project']; result['operator']=operator; result['formation']={'index':idx,'project':ep['project'],'bug':ep['bug'],'wins':len(wins)}; rec['status']='OPERATOR_FORMED'
            else:rec['status']='OLD_CLOSURE_NOT_OBSTRUCTED'
        else:rec['status']='AMBIGUOUS_OR_NO_REPAIR'
    else:
        if ep['project']==formation_project:
            rec['status']='SAME_PROJECT_AFTER_FORMATION'
        else:
            wins=try_operator(ep,repo,env,out,operator); rec['operator_wins']=wins
            if len(wins)==1:
                # causal ablation = restored original still fails
                ablated,_=test_cmd(ep,repo,env)
                if not ablated:
                    result['reuse']={'index':idx,'project':ep['project'],'bug':ep['bug'],'win':wins[0],'ablation_fails':True}; rec['status']='SOURCE_DISTINCT_CAUSAL_REUSE'; result['verdict']='PASS_V52_HISTORICAL_OPERATOR_RATCHET'; result['episodes'].append(rec); break
                rec['status']='ABLATION_FAILED'
            else:rec['status']='NO_REUSE'
    result['episodes'].append(rec)

if operator and not result['reuse']:result['verdict']='FORMATION_WITHOUT_SOURCE_DISTINCT_REUSE'
result['claim_boundary']='Human bug_patch.txt files were not read by this harness. Fixed commits are accessed only to import regression test files, mirroring BugsInPy checkout semantics. Constructor is limited to traceback-localized single-token operator rewrites under a fixed budget.'
(OUT/'RESULT.json').write_text(json.dumps(result,indent=2)); print(json.dumps(result,indent=2))
# The scientific outcome may be a negative; never fail CI merely because no operator/reuse was found.
