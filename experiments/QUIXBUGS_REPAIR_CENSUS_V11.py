import ast, json, subprocess, tempfile
from pathlib import Path

REPO='https://github.com/jkoppel/QuixBugs.git'
COMMIT='4257f44b0ff1181dedaedee6a447e133219fcebf'
OUT=Path('artifacts/quixbugs_census_v11'); OUT.mkdir(parents=True, exist_ok=True)

root=Path(tempfile.mkdtemp())/'QuixBugs'
subprocess.run(['git','clone','-q',REPO,str(root)],check=True)
subprocess.run(['git','checkout','-q',COMMIT],cwd=root,check=True)
actual=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
assert actual==COMMIT

OPNODES=(ast.operator,ast.unaryop,ast.boolop,ast.cmpop)
IGNORE_FIELDS={'lineno','col_offset','end_lineno','end_col_offset','ctx','type_comment'}

def features(a,b,path='root'):
    out=[]
    if type(a) is not type(b):
        if isinstance(a,OPNODES) or isinstance(b,OPNODES):
            out.append(f'OP:{type(a).__name__}->{type(b).__name__}')
        elif isinstance(a,ast.AST) and isinstance(b,ast.AST):
            out.append(f'NODE:{type(a).__name__}->{type(b).__name__}')
        else:
            out.append('VALUE_TYPE_CHANGE')
        return out
    if isinstance(a,ast.AST):
        for f in a._fields:
            if f in IGNORE_FIELDS: continue
            out.extend(features(getattr(a,f),getattr(b,f),path+'.'+f))
        return out
    if isinstance(a,list):
        if len(a)!=len(b): out.append('LIST_LENGTH_CHANGE')
        for x,y in zip(a,b): out.extend(features(x,y,path+'[]'))
        return out
    if a!=b:
        leaf=path.rsplit('.',1)[-1]
        if leaf=='id': out.append('NAME_CHANGE')
        elif leaf=='attr': out.append('ATTR_CHANGE')
        elif leaf=='value': out.append('CONST_CHANGE')
        elif leaf in {'arg'}: out.append('ARG_CHANGE')
        else: out.append('SCALAR_CHANGE:'+leaf)
    return out

rows=[]
for bug in sorted((root/'python_programs').glob('*.py')):
    fix=root/'correct_python_programs'/bug.name
    if not fix.exists(): continue
    try:
        ta=ast.parse(bug.read_text()); tb=ast.parse(fix.read_text())
        fs=features(ta,tb)
    except Exception as e:
        rows.append({'program':bug.stem,'error':repr(e)}); continue
    sig=sorted(set(fs))
    rows.append({'program':bug.stem,'signature':sig,'feature_count':len(sig)})

valid=[r for r in rows if r.get('signature')]
chains=[]
for a in valid:
    A=set(a['signature'])
    for b in valid:
        if a is b: continue
        B=set(b['signature'])
        if not (A < B): continue
        for c in valid:
            if c is a or c is b: continue
            C=set(c['signature'])
            if B < C:
                chains.append({'A':a['program'],'AB':b['program'],'ABC':c['program'],'sigA':sorted(A),'sigAB':sorted(B),'sigABC':sorted(C)})

# Also report repeated feature families useful for constructed multi-bug external tasks.
from collections import Counter,defaultdict
cnt=Counter(f for r in valid for f in r['signature'])
by=defaultdict(list)
for r in valid:
    for f in r['signature']: by[f].append(r['program'])
common=[{'feature':f,'count':n,'programs':by[f]} for f,n in cnt.most_common()]

R={'repo':REPO,'commit':actual,'programs':len(valid),'rows':rows,'natural_nested_chains':chains[:100],'natural_chain_count':len(chains),'common_features':common}
(OUT/'RESULT.json').write_text(json.dumps(R,indent=2))
print(json.dumps({'commit':actual,'programs':len(valid),'natural_chain_count':len(chains),'top_common':common[:10],'first_chains':chains[:10]},indent=2))
