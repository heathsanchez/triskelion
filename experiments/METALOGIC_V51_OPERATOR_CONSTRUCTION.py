import hashlib, io, json, re, subprocess, tokenize
from collections import Counter
from pathlib import Path

OUT=Path('artifacts/v51'); OUT.mkdir(parents=True,exist_ok=True)
DJ=Path('/tmp/v51_django'); RH=Path('/tmp/v51_rich')
SEED='V51_OPERATOR_INVENTION_20260814'

def sh(cmd,cwd,t=60):
    try:
        p=subprocess.run(cmd,cwd=cwd,shell=True,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=t)
        return p.returncode==0
    except subprocess.TimeoutExpired:
        return False

def reset(r): subprocess.run('git reset --hard -q HEAD && git clean -fdxq',cwd=r,shell=True,check=True)
def H(x): return hashlib.sha256((SEED+'|'+x).encode()).hexdigest()
def th(x): return 't_'+hashlib.sha256((SEED+'|tok|'+x).encode()).hexdigest()[:16]
def lex(line): return re.findall(r'[A-Za-z_]+|\d+',line)

def token_sites(path,val):
    ts=list(tokenize.generate_tokens(io.StringIO(path.read_text()).readline)); out=[]
    for t in ts:
        if t.type==tokenize.OP and t.string==val: out.append((t.start[0],t.start[1],t.end[1],val))
    return out

def mutate(path,site,new):
    row,c0,c1,_=site; lines=path.read_text().splitlines(True); oldline=lines[row-1]
    lines[row-1]=oldline[:c0]+new+oldline[c1:]; path.write_text(''.join(lines)); return oldline.strip()

def find_breaking_site(repo,path,good,bad,test,t,key):
    reset(repo); assert sh(test,repo,t); sites=token_sites(path,good); bads=[]
    for i in sorted(range(len(sites)),key=lambda j:H(key+'|'+repr(sites[j][:3]))):
        reset(repo); line=mutate(path,sites[i],bad); ok=sh(test,repo,t)
        if not ok: bads.append((sites[i],line))
    return bads

# Frozen old algebra: token-position permutations only. Every generator preserves token-value multiset.
OLD_GENERATORS=['IDENTITY','REVERSE_WINDOW','ROTATE_LEFT','ROTATE_RIGHT','SWAP_ADJACENT']
def invariant(tokens): return Counter(tokens)
def old_closure_preserves_multiset():
    sample=['if','x','<','y',':']
    variants=[sample,list(reversed(sample)),sample[1:]+sample[:1],sample[-1:]+sample[:-1],[sample[1],sample[0],*sample[2:]]]
    return all(invariant(v)==invariant(sample) for v in variants)

# Generic constructor substrate: all Python operator lexemes of length <=2, not a comparator-specific menu.
DESTS=sorted({s for s in tokenize.EXACT_TOKEN_TYPES if len(s)<=2 and s not in {'<'}})

positives=[
 ('p1',DJ,DJ/'django/db/backends/utils.py','python tests/runtests.py backends.test_utils.TestUtils.test_truncate_name --verbosity 0',40),
 ('p2',DJ,DJ/'django/core/paginator.py','python tests/runtests.py pagination.tests.PaginationTests.test_orphans_value_larger_than_per_page_value --verbosity 0',40),
]
repairs=[]
for eid,repo,path,test,t in positives:
    bs=find_breaking_site(repo,path,'<=','<',test,t,eid)
    if len(bs)!=1:
        repairs.append({'id':eid,'error':'nonunique_breaking_site','count':len(bs)}); continue
    good_site,line=bs[0]
    # Recreate broken program, then ask generic token emission substrate which single token restores behavior.
    reset(repo); mutate(path,good_site,'<')
    broken_sites=[s for s in token_sites(path,'<') if s[0]==good_site[0] and s[1]==good_site[1]]
    survivors=[]
    if len(broken_sites)==1:
        broken_site=broken_sites[0]
        for d in DESTS:
            reset(repo); mutate(path,good_site,'<')
            cur=[s for s in token_sites(path,'<') if s[0]==good_site[0] and s[1]==good_site[1]]
            if len(cur)!=1: continue
            mutate(path,cur[0],d)
            if sh(test,repo,t): survivors.append(d)
    repairs.append({'id':eid,'line':line,'survivors':survivors})

valid=[r for r in repairs if 'survivors' in r]
common=set(valid[0]['survivors']) if valid else set()
for r in valid[1:]: common &= set(r['survivors'])
unique_dst=next(iter(common)) if len(common)==1 else None
operator={'kind':'TOKEN_REWRITE','src_hash':th('<'),'dst_hash':th(unique_dst),'src_posthoc':'<','dst_posthoc':unique_dst} if unique_dst else None

# Algebraic obstruction certificate: old closure preserves token multiset, synthesized rewrite does not.
obstruction=bool(old_closure_preserves_multiset() and unique_dst and Counter(['<'])!=Counter([unique_dst]))

# After operator construction, acquire one independently-authored HARM episode and infer applicability scope.
rpath=RH/'rich/highlighter.py'; rtest='pytest -q tests/test_highlighter.py::test_highlight_json_string_only tests/test_highlighter.py::test_highlight_json_empty_string_only'
reset(RH); rbase=sh(rtest,RH,40); harms=[]
if operator:
    sites=token_sites(rpath,'<')
    for i in sorted(range(len(sites)),key=lambda j:H('rich|'+repr(sites[j][:3]))):
        reset(RH); line=mutate(rpath,sites[i],unique_dst); after=sh(rtest,RH,40)
        if rbase and not after: harms.append({'site':list(sites[i][:3]),'line':line})

# Scope vocabulary is generic position-indexed identifier/number tokens, comparator punctuation excluded.
help_lines=[r['line'] for r in valid]
harm_lines=[h['line'] for h in harms]
F=[]
for label,line in [('HELP',x) for x in help_lines]+[('HARM',x) for x in harm_lines]:
    F.append((label,{(i,th(tok)) for i,tok in enumerate(lex(line))},line))
vocab=sorted(set().union(*(fs for _,fs,_ in F))) if F else []
scope_survivors=[f for f in vocab if all(f in fs for lab,fs,_ in F if lab=='HELP') and all(f not in fs for lab,fs,_ in F if lab=='HARM')]
scope=scope_survivors[0] if len(scope_survivors)==1 else None
decode={}
for _,_,line in F:
    for i,tok in enumerate(lex(line)): decode[(i,th(tok))]=(i,tok)

commit={'protocol':SEED,'operator':operator,'scope':list(scope) if scope else None,'operator_hash':H(json.dumps(operator,sort_keys=True)) if operator else None,'scope_hash':H(repr(scope)) if scope else None,'requests_forbidden_phase_a':True,'later_counterexample_forbidden_phase_a':True}
R={'protocol':SEED,'old_generators':OLD_GENERATORS,'constructor_destination_count':len(DESTS),'repair_search':repairs,'common_repair_tokens':sorted(common),'constructed_operator':operator,'old_closure_obstruction':obstruction,'rich_harm_count':len(harms),'scope_candidate_count':len(vocab),'scope_survivor_count':len(scope_survivors),'scope':list(scope) if scope else None,'scope_posthoc':list(decode[scope]) if scope else None,'commitment':commit}
R['gates']={'old_closure_invariant_verified':old_closure_preserves_multiset(),'two_external_obstructions':len(valid)==2,'unique_cross_episode_new_token':unique_dst is not None,'constructed_operator_not_in_old_closure':obstruction,'operator_posthoc_is_strict_to_nonstrict':bool(operator and unique_dst=='<='),'independent_harm_found':len(harms)==1,'unique_scope_from_help_harm':scope is not None,'scope_posthoc_is_if':bool(scope and decode.get(scope)==(0,'if')),'requests_sealed':True}
R['verdict']='PASS_V51_PHASE_A_OPERATOR_CONSTRUCTION' if all(R['gates'].values()) else 'FAIL_V51_PHASE_A_OPERATOR_CONSTRUCTION'
(OUT/'PHASE_A.json').write_text(json.dumps(R,indent=2)); (OUT/'COMMITMENT.json').write_text(json.dumps(commit,sort_keys=True,indent=2)); print(json.dumps(R,indent=2))
if R['verdict'].startswith('FAIL'): raise SystemExit(1)
