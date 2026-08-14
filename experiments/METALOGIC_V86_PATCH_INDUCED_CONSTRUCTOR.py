#!/usr/bin/env python3
import hashlib, io, json, os, subprocess, sys, tokenize
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path

ROOT=Path(os.environ.get('QUIXBUGS_DIR','/tmp/QuixBugs'))
OUT=Path(os.environ.get('OUT_DIR','results/v86')); OUT.mkdir(parents=True,exist_ok=True)
SEED='V86_PATCH_INDUCED_CONSTRUCTOR_2026-08-14'
COMMIT='4257f44b0ff1181dedaedee6a447e133219fcebf'

def h(x): return hashlib.sha256((SEED+'|'+x).encode()).hexdigest()
def toks(s):
    return [(t.type,t.string) for t in tokenize.generate_tokens(io.StringIO(s).readline)
            if t.type not in (tokenize.ENCODING,tokenize.NL,tokenize.NEWLINE,tokenize.INDENT,tokenize.DEDENT,tokenize.ENDMARKER)]

def extract_templates(buggy,correct):
    a,b=toks(buggy),toks(correct); sm=SequenceMatcher(a=a,b=b,autojunk=False); out=[]
    for tag,i1,i2,j1,j2 in sm.get_opcodes():
        if tag=='replace' and i2-i1==1 and j2-j1==1:
            old,new=a[i1],b[j1]
            out.append((old[0],old[1],new[0],new[1]))
    return out

def mutate_text(src,templ):
    ot,os_,nt,ns=templ
    ts=list(tokenize.generate_tokens(io.StringIO(src).readline)); outs=[]
    for i,t in enumerate(ts):
        if t.type==ot and t.string==os_:
            z=ts.copy(); z[i]=tokenize.TokenInfo(nt,ns,t.start,t.end,t.line)
            try: outs.append(tokenize.untokenize(z))
            except Exception: pass
    return outs

def test_prog(name,text):
    p=ROOT/'python_programs'/f'{name}.py'; old=p.read_text()
    try:
        p.write_text(text)
        r=subprocess.run([sys.executable,'-m','pytest','-q',f'python_testcases/test_{name}.py','--timeout=4'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=20)
        return r.returncode==0
    except Exception: return False
    finally: p.write_text(old)

def solve_with(name,templates,cap=180):
    src=(ROOT/'python_programs'/f'{name}.py').read_text(); seen=set(); n=0
    for t in templates:
        for m in mutate_text(src,t):
            key=hashlib.sha1(m.encode()).hexdigest()
            if key in seen: continue
            seen.add(key); n+=1
            if test_prog(name,m): return True,t,n
            if n>=cap: return False,None,n
    return False,None,n

def main():
    names=[]
    for p in (ROOT/'python_programs').glob('*.py'):
        n=p.stem
        if n.startswith('__') or not (ROOT/'python_testcases'/f'test_{n}.py').exists(): continue
        if not test_prog(n,p.read_text()): names.append(n)
    names=sorted(names,key=h)
    cut=max(10,len(names)//2); train=names[:cut]; test=names[cut:]
    # Split frozen before any correct file is read.
    learned=[]; support=Counter(); train_details={}
    for n in train:
        buggy=(ROOT/'python_programs'/f'{n}.py').read_text()
        correct=(ROOT/'correct_python_programs'/f'{n}.py').read_text()
        tt=extract_templates(buggy,correct); train_details[n]=[list(x) for x in tt]
        for x in tt: support[x]+=1
    # retain every observed single-token edit; rank by support then MDL proxy
    learned=sorted(support,key=lambda x:(-support[x],len(x[1])+len(x[3]),str(x)))
    # wrong-pair control: independently permute correct programs before extraction
    perm=train[1:]+train[:1]; wrong=[]; wc=Counter()
    for n,c in zip(train,perm):
        for x in extract_templates((ROOT/'python_programs'/f'{n}.py').read_text(),(ROOT/'correct_python_programs'/f'{c}.py').read_text()): wc[x]+=1
    wrong=sorted(wc,key=lambda x:(-wc[x],len(x[1])+len(x[3]),str(x)))
    # Historical K0 exact comparison rewrites used by V83/V84.
    k0=[(54,a,54,b) for a,b in [('<','<='),('<=','<'),('>','>='),('>=','>'),('==','!='),('!=','==')]]
    rows=[]; k0sol=[]; k1sol=[]; wrongsol=[]
    for n in test:
        a,ta,na=solve_with(n,k0,80); b,tb,nb=solve_with(n,learned,180); c,tc,nc=solve_with(n,wrong,180)
        if a:k0sol.append(n)
        if b:k1sol.append(n)
        if c:wrongsol.append(n)
        rows.append({'task':n,'k0':a,'k1':b,'wrong':c,'k1_template':list(tb) if tb else None})
    new=sorted(set(k1sol)-set(k0sol)); ablation={}
    for t in sorted({tuple(r['k1_template']) for r in rows if r['task'] in new and r['k1_template']}):
        reduced=[x for x in learned if x!=t]; lost=[]
        for n in new:
            ok,_,_=solve_with(n,reduced,180)
            if not ok: lost.append(n)
        ablation[str(t)]=lost
    gates={
      'preexisting_external_corpus':True,
      'split_frozen_before_reading_training_fixes':True,
      'heldout_correct_solutions_never_read':True,
      'training_experience_induces_nonempty_constructor':bool(learned),
      'heldout_closure_strictly_expands':len(new)>0,
      'induced_beats_wrong_pair_control':len(k1sol)>len(wrongsol),
      'at_least_one_template_causally_load_bearing':any(ablation.values())
    }
    verdict='PASS_PATCH_INDUCED_CONSTRUCTOR_V86' if all(gates.values()) else 'MIXED_PATCH_INDUCED_CONSTRUCTOR_V86'
    res={'protocol':'V86_PATCH_INDUCED_CONSTRUCTOR','external_repo':'jkoppel/QuixBugs','external_commit':COMMIT,
         'train':train,'test':test,'training_correct_files_read':True,'heldout_correct_files_read':False,
         'learned_template_count':len(learned),'top_templates':[{'template':list(x),'support':support[x]} for x in learned[:30]],
         'k0_solved':k0sol,'k1_solved':k1sol,'wrong_pair_solved':wrongsol,'new_closure':new,'rows':rows,'ablation':ablation,'gates':gates,
         'qualification':'Supervised external constructor induction: human fixes are read on the frozen training split only. Held-out correct implementations remain sealed. This is a bridge for discovering transferable edit grammar, not autonomous constructor invention.',
         'verdict':verdict}
    (OUT/'RESULT.json').write_text(json.dumps(res,indent=2)); print(json.dumps(res,indent=2))
if __name__=='__main__': main()
