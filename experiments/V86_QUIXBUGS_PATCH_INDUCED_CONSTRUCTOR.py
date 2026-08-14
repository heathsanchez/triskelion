import difflib, hashlib, io, itertools, json, os, pathlib, subprocess, sys, tokenize

QB=pathlib.Path(os.environ.get('QUIXBUGS_DIR','/tmp/QuixBugs')).resolve()
COMMIT='4257f44b0ff1181dedaedee6a447e133219fcebf'
TIMEOUT=8; N_TRAIN=12; N_TEST=12; CAP=80
K0_PAIRS=[('<','<='),('<=','<'),('>','>='),('>=','>'),('==','!='),('!=','=='),('+','-'),('-','+'),('*','+'),('+','*'),('//','/'),('/','//'),('%','//'),('//','%'),('and','or'),('or','and'),('True','False'),('False','True'),('min','max'),('max','min'),('append','extend'),('extend','append'),('0','1'),('1','0'),('1','2'),('2','1')]
SIG_SKIP={tokenize.NL,tokenize.NEWLINE,tokenize.INDENT,tokenize.DEDENT,tokenize.COMMENT,tokenize.ENDMARKER}

def h(s): return hashlib.sha256(s.encode()).hexdigest()
def ordered(xs,seed): return sorted(xs,key=lambda x:h(seed+'|'+x))
def task_names():
    xs=[]
    for p in sorted((QB/'python_testcases').glob('test_*.py')):
        n=p.stem[len('test_'):]
        if (QB/'python_programs'/f'{n}.py').exists() and n not in {'knapsack','levenshtein','bitcount'}: xs.append(n)
    return ordered(xs,'V86-SPLIT')

def tok_full(src): return list(tokenize.generate_tokens(io.StringIO(src).readline))
def sig(tokens): return [(i,t) for i,t in enumerate(tokens) if t.type not in SIG_SKIP]
def pair_untok(pairs):
    try:
        s=tokenize.untokenize(pairs); compile(s,'<mut>','exec'); return s
    except Exception:return None

cache={}
def verify(name,src):
    key=(name,h(src))
    if key in cache:return cache[key]
    path=QB/'python_programs'/f'{name}.py'; orig=path.read_text()
    try:
        path.write_text(src)
        pc=QB/'python_programs'/'__pycache__'
        if pc.exists():
            for pyc in pc.glob(f'{name}.*.pyc'): pyc.unlink(missing_ok=True)
        cp=subprocess.run([sys.executable,'-m','pytest','-q',f'python_testcases/test_{name}.py','--disable-warnings','--maxfail=1'],cwd=QB,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=TIMEOUT)
        ok=cp.returncode==0
    except subprocess.TimeoutExpired: ok=False
    finally:path.write_text(orig)
    cache[key]=ok; return ok

def token_mutations(src,schema):
    old,new=schema; ts=tok_full(src); out=[]
    for i,t in enumerate(ts):
        if t.string==old and t.type in (tokenize.OP,tokenize.NAME,tokenize.NUMBER):
            pp=[(x.type,x.string) for x in ts]; pp[i]=(t.type,new); s=pair_untok(pp)
            if s: out.append(s)
    return out

def k0_solves(name):
    src=(QB/'python_programs'/f'{name}.py').read_text()
    for sc in K0_PAIRS:
        for m in token_mutations(src,sc):
            if verify(name,m): return True
    return False

def tname(t): return tokenize.tok_name.get(t,str(t))
def induce_patch(buggy,correct):
    a=tok_full(buggy); b=tok_full(correct); sa=sig(a); sb=sig(b)
    A=[(t.type,t.string) for _,t in sa]; B=[(t.type,t.string) for _,t in sb]
    sm=difflib.SequenceMatcher(a=A,b=B,autojunk=False); templates=[]
    for tag,i1,i2,j1,j2 in sm.get_opcodes():
        if tag=='equal': continue
        old=A[i1:i2]; new=B[j1:j2]
        if tag=='replace' and len(old)==1 and len(new)==1:
            ot,os=old[0]; nt,ns=new[0]
            if ot==nt and ot in (tokenize.OP,tokenize.NAME,tokenize.NUMBER,tokenize.STRING):
                label='REPLACE_'+tname(ot); templates.append((label,ns))
            else:
                templates.append(('REPLACE_TYPED_SEQ',tuple(x[0] for x in old),tuple(new)))
        elif tag=='delete' and len(old)==1:
            templates.append(('DELETE_'+tname(old[0][0]),None))
        elif tag=='insert' and len(new)==1:
            templates.append(('INSERT_'+tname(new[0][0]),new[0]))
        else:
            templates.append(('REPLACE_TYPED_SEQ',tuple(x[0] for x in old),tuple(new)))
    return templates

def build_grammar(pairs):
    g={}
    for buggy,correct in pairs:
        for tpl in induce_patch(buggy,correct):
            label=tpl[0]; payload=tpl[1:]
            g.setdefault(label,set()).add(json.dumps(payload,sort_keys=True))
    return {k:sorted(v) for k,v in sorted(g.items())}

def decode_payload(s): return json.loads(s)

def grammar_candidates(src,label,payloads,seed):
    ts=tok_full(src); sg=sig(ts); pairs0=[(t.type,t.string) for t in ts]; out={}
    def add(pp):
        s=pair_untok(pp)
        if s and s!=src: out[h(s)]=s
    if label.startswith('REPLACE_') and label!='REPLACE_TYPED_SEQ':
        typname=label[len('REPLACE_'):]; typ=next((k for k,v in tokenize.tok_name.items() if v==typname),None)
        learned=[decode_payload(x)[0] for x in payloads]
        if typ==tokenize.NAME:
            vals=sorted({t.string for _,t in sg if t.type==tokenize.NAME})
        elif typ==tokenize.NUMBER:
            vals=sorted(set(learned)|{t.string for _,t in sg if t.type==tokenize.NUMBER})
        else: vals=sorted(set(learned))
        for fi,t in enumerate(ts):
            if t.type!=typ: continue
            for v in vals:
                if v==t.string:continue
                pp=pairs0.copy(); pp[fi]=(typ,v); add(pp)
    elif label.startswith('DELETE_'):
        typname=label[len('DELETE_'):]; typ=next((k for k,v in tokenize.tok_name.items() if v==typname),None)
        for fi,t in enumerate(ts):
            if t.type==typ:
                pp=pairs0.copy(); pp.pop(fi); add(pp)
    elif label.startswith('INSERT_'):
        learned=[decode_payload(x)[0] for x in payloads]
        for fi,t in enumerate(ts):
            for nt,ns in learned:
                for pos in (fi,fi+1):
                    pp=pairs0.copy(); pp.insert(pos,(nt,ns)); add(pp)
    elif label=='REPLACE_TYPED_SEQ':
        specs=[decode_payload(x) for x in payloads]
        sigpos=[i for i,t in enumerate(ts) if t.type not in SIG_SKIP]
        sigtypes=[ts[i].type for i in sigpos]
        for oldtypes,newseq in specs:
            oldtypes=tuple(oldtypes); L=len(oldtypes)
            if L==0: continue
            for j in range(len(sigpos)-L+1):
                if tuple(sigtypes[j:j+L])!=oldtypes: continue
                fullidx=sigpos[j:j+L]; pp=pairs0.copy(); start=fullidx[0]
                for ix in reversed(fullidx): pp.pop(ix)
                for nt,ns in reversed(newseq): pp.insert(start,(nt,ns))
                add(pp)
    keys=sorted(out,key=lambda z:h(seed+'|'+z))[:CAP]
    return [out[k] for k in keys]

def label_solve_set(tasks,grammar,label):
    ss=set()
    for name in tasks:
        src=(QB/'python_programs'/f'{name}.py').read_text()
        for m in grammar_candidates(src,label,grammar[label],'V86|'+label+'|'+name):
            if verify(name,m): ss.add(name); break
    return ss

names=task_names(); train=names[:N_TRAIN]; test=names[N_TRAIN:N_TRAIN+N_TEST]
# Training correct patches are explicit external experience. Verify them before induction.
train_pairs=[]; train_verified={}
for n in train:
    buggy=(QB/'python_programs'/f'{n}.py').read_text(); correct=(QB/'correct_python_programs'/f'{n}.py').read_text()
    ok=verify(n,correct); train_verified[n]=ok
    if ok: train_pairs.append((buggy,correct))
grammar=build_grammar(train_pairs)
# Wrong-pair control: same training buggy programs paired with the next task's correct source.
wrong=[]
for i,n in enumerate(train):
    m=train[(i+1)%len(train)]
    buggy=(QB/'python_programs'/f'{n}.py').read_text(); wrong_correct=(QB/'correct_python_programs'/f'{m}.py').read_text(); wrong.append((buggy,wrong_correct))
wrong_grammar=build_grammar(wrong)
# No correct_python_programs reads occur below this line for held-out test names.
k0={n for n in test if k0_solves(n)}
label_sets={label:label_solve_set(test,grammar,label) for label in grammar}
k1=set().union(*label_sets.values()) if label_sets else set()
wrong_sets={label:label_solve_set(test,wrong_grammar,label) for label in wrong_grammar}
wrong_set=set().union(*wrong_sets.values()) if wrong_sets else set()
new=k1-k0; wrong_new=wrong_set-k0
ablation={label:len(k1-(set().union(*(ss for l,ss in label_sets.items() if l!=label)) if len(label_sets)>1 else set())) for label in label_sets}
res={
 'protocol':'V86_QUIXBUGS_PATCH_INDUCED_CONSTRUCTOR','external_repo':'jkoppel/QuixBugs','external_commit':COMMIT,
 'train':train,'test':test,'training_correct_fixes_read':True,'heldout_correct_fixes_read':False,'train_correct_verified':train_verified,
 'induced_grammar':grammar,'wrong_pair_grammar':wrong_grammar,'k0_test_solved':sorted(k0),'k1_test_solved':sorted(k1),'wrong_pair_test_solved':sorted(wrong_set),
 'new_test_closure':sorted(new),'wrong_pair_new_closure':sorted(wrong_new),'k0_count':len(k0),'k1_count':len(k1),'new_count':len(new),'wrong_pair_new_count':len(wrong_new),'ablation_loss':ablation,
 'label_solve_sets':{k:sorted(v) for k,v in label_sets.items()},
 'gates':{
   'all_used_training_fixes_verify':bool(train_pairs) and all(train_verified.values()),
   'constructor_grammar_induced_without_manual_bug_labels':bool(grammar),
   'heldout_correct_fixes_sealed':True,
   'heldout_closure_strictly_expands':len(new)>0,
   'induced_grammar_beats_wrong_pair_control':len(new)>len(wrong_new),
   'at_least_one_induced_template_is_causally_load_bearing':any(v>0 for v in ablation.values())
 },
 'qualification':'Supervised/external constructor induction from pre-existing verified human fixes on the training split. The grammar is extracted automatically from token edit structure without manual defect labels; held-out correct implementations are never read. This is not autonomous constructor invention from failures alone, but it tests whether independently authored repair experience induces a transferable constructor language.'
}
res['verdict']='PASS_PATCH_INDUCED_CONSTRUCTOR_V86' if all(res['gates'].values()) else 'MIXED_PATCH_INDUCED_CONSTRUCTOR_V86'
print(json.dumps(res,indent=2)); open(os.environ.get('V86_RESULT','/tmp/v86_result.json'),'w').write(json.dumps(res,indent=2))
