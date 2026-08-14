import hashlib, json, os, re, subprocess, sys, tempfile
from pathlib import Path
import requests
import river_client as river

SORRYDB_ROOT=Path(os.environ.get('SORRYDB_ROOT','vendor/SorryDB')).resolve()
sys.path.insert(0,str(SORRYDB_ROOT))
from sorrydb.database.sorry import Sorry
from sorrydb.utils.verify_lean_interact import verify_lean_interact

OUT=Path('artifacts/sorrydb_v77_preflight'); OUT.mkdir(parents=True,exist_ok=True)
DATA_URL='https://raw.githubusercontent.com/SorryDB/sorrydb-data/refs/heads/master/static_100_varied_recent_deduplicated_sorries.json'
SEED='20261017'; N_REPOS=3; BASE='Qwen/Qwen3.5-9B'
MAX_RETRIES=3; MAX_TOKENS=512
OPS={
 'D':'Focus on the smallest exact discrepancy exposed by the Lean feedback. Do not merely patch wording. Use that distinction to choose the next proof construction, then output only the replacement proof.',
 'C':'Treat the theorem statement, local context, imports, and every Lean diagnostic as hard constraints. Produce a proof satisfying all of them simultaneously. Output only the replacement proof.',
 'S':'Commit to one proof route that best fits the current evidence instead of blending incompatible approaches. Finish that route cleanly and output only the replacement proof.',
 'G':'Construct a genuinely different proof route from the previous attempt rather than locally editing it. Use the unchanged theorem and Lean feedback. Output only the replacement proof.',
 'X':'Combine independently supported proof fragments or local facts into one coherent proof candidate. Do not introduce unsupported lemmas or imports. Output only the replacement proof.',
 'T':'Change proof representation while preserving the theorem: for example tactic to term, calc, direct constructor, or helper-style structure. Output only the replacement proof.',
}
ARMS={
 'B_RAW':['RAW','RAW','RAW'],
 'E_DCS':['D','C','S'],
 'E_FLAT':['FLAT','FLAT','FLAT'],
 'E_ORDER':['C','S','D'],
 'E_SEM':['G','X','T'],
}

def sh(cmd,cwd=None,timeout=1800):
    p=subprocess.run(cmd,cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout)
    return p.returncode,p.stdout

def repo_name(remote): return remote.rstrip('/').split('/')[-1].removesuffix('.git')
def hkey(remote): return hashlib.sha256((SEED+'|'+remote).encode()).hexdigest()

def select_tasks():
    data=requests.get(DATA_URL,timeout=60).json()['sorries']
    by={}
    for row in data: by.setdefault(row['repo']['remote'],row)
    remotes=sorted(by,key=hkey)[:N_REPOS]
    rows=[by[r] for r in remotes]
    (OUT/'SELECTION.json').write_text(json.dumps({'seed':SEED,'remotes':remotes,'ids':[r['id'] for r in rows]},indent=2))
    return [Sorry.from_dict(r) for r in rows]

def prepare(sorry):
    r=sorry.repo; name=repo_name(r.remote); path=Path('.lean_v77')/name/r.commit
    if not path.exists():
        path.parent.mkdir(parents=True,exist_ok=True)
        rc,out=sh(['git','clone','-q',r.remote,str(path)],timeout=1200)
        if rc: return None,'clone failed: '+out[-3000:]
        rc,out=sh(['git','checkout','-q',r.commit],cwd=path,timeout=300)
        if rc: return None,'checkout failed: '+out[-3000:]
    rc,out=sh(['lake','build'],cwd=path,timeout=2400)
    if rc: return None,'build failed: '+out[-5000:]
    return path.resolve(),''

def context(repo,sorry):
    text=(repo/sorry.location.path).read_text()
    lines=text.splitlines()
    end=min(len(lines),sorry.location.start_line)
    start=max(0,end-140)
    return '\n'.join(lines[start:end])

def clean(text):
    text=re.sub(r'<think>.*?</think>','',text,flags=re.S).strip()
    blocks=re.findall(r'```(?:lean)?\s*(.*?)```',text,flags=re.S)
    if blocks: text=blocks[-1].strip()
    for prefix in ['Proof:','proof:','Replacement:','replacement:']:
        if text.startswith(prefix): text=text[len(prefix):].strip()
    return text.strip()

def sample(m,prompt):
    g=m.sample(prompts=[prompt],max_tokens=MAX_TOKENS,temperature=0.0)
    return clean(g[0][0].text)

def base_prompt(repo,sorry):
    return f'''You are repairing exactly one SorryDB Lean4 sorry in an independently authored repository.
Return ONLY the replacement proof text for the target sorry: no markdown, no explanation, no imports, no theorem restatement.

Native Lean goal:
{sorry.debug_info.goal}

Source context ending at the target sorry:
{context(repo,sorry)}'''

def retry_prompt(repo,sorry,history,op):
    recent='\n\n'.join(f'Attempt {i+1}:\n{p}\nLean feedback:\n{e[:6000]}' for i,(p,e) in enumerate(history[-3:]))
    if op=='RAW': instr='Use the native Lean feedback to correct the proof. Output only the replacement proof.'
    elif op=='FLAT': instr=OPS['D']+' '+OPS['C']+' '+OPS['S']
    else: instr=OPS[op]
    return base_prompt(repo,sorry)+f'''\n\nPrevious verified failures:\n{recent}\n\nRetry control:\n{instr}'''

def verify(repo,sorry,proof):
    try: return verify_lean_interact(repo,sorry.location,proof,timeout=180)
    except Exception as e: return False,'verifier exception: '+repr(e)

def main():
    tasks=select_tasks(); result={'seed':SEED,'base':BASE,'tasks':[],'plumbing_pass':False}
    client=river.Client(api_key=os.environ['RIVER_API_KEY'],timeout=240.0); assert client.health_check()
    with client.session(project='metalogic-sorrydb-v77-preflight') as sess:
        model=sess.create_model(base_model=BASE,lora=river.LoraConfig(rank=32,seed=20260903))
        for idx,sorry in enumerate(tasks):
            row={'id':sorry.id,'remote':sorry.repo.remote,'commit':sorry.repo.commit,'goal':sorry.debug_info.goal,'arms':{}}
            repo,err=prepare(sorry)
            if repo is None:
                row['infra_error']=err; result['tasks'].append(row); print(json.dumps({'task':idx,'infra_error':err}),flush=True); continue
            first=sample(model,base_prompt(repo,sorry)); ok,fb=verify(repo,sorry,first)
            row['shared_first']={'proof':first,'verified':ok,'feedback':fb}
            print(json.dumps({'task':idx,'repo':sorry.repo.remote,'first_verified':ok}),flush=True)
            for arm,schedule in ARMS.items():
                hist=[(first,fb)]; armrow={'schedule':schedule,'attempts':[],'verified':ok}
                if not ok:
                    for op in schedule:
                        proof=sample(model,retry_prompt(repo,sorry,hist,op)); vok,vfb=verify(repo,sorry,proof)
                        armrow['attempts'].append({'op':op,'proof':proof,'verified':vok,'feedback':vfb})
                        hist.append((proof,vfb))
                        if vok: armrow['verified']=True; break
                row['arms'][arm]=armrow
            result['tasks'].append(row)
            (OUT/'RESULT_PARTIAL.json').write_text(json.dumps(result,indent=2))
    prepared=sum('infra_error' not in r for r in result['tasks'])
    isolated=all(set(r.get('arms',{}))==set(ARMS) for r in result['tasks'] if 'infra_error' not in r)
    result['plumbing_pass']=prepared>=2 and isolated
    result['prepared_tasks']=prepared
    result['arm_success_counts']={a:sum(bool(r.get('arms',{}).get(a,{}).get('verified')) for r in result['tasks']) for a in ARMS}
    (OUT/'RESULT.json').write_text(json.dumps(result,indent=2))
    print(json.dumps({'plumbing_pass':result['plumbing_pass'],'prepared':prepared,'success_counts':result['arm_success_counts']},indent=2),flush=True)
    if not result['plumbing_pass']: raise SystemExit(2)

if __name__=='__main__': main()
