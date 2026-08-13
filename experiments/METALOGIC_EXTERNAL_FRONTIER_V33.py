import ast,hashlib,json,subprocess,tempfile
from pathlib import Path
OUT=Path('artifacts/external_frontier_v33');OUT.mkdir(parents=True,exist_ok=True)
SEED='V33_20260814'
REPOS=[
 ('requests','https://github.com/psf/requests.git','8068356288978c4f54661ae6f95afe0e0831885e'),
 ('flask','https://github.com/pallets/flask.git','2a8a38b051fc248865730bf3511bf2e2ea325e81'),
 ('rich','https://github.com/Textualize/rich.git','9d8f9a372cc5916fd4781fec207ced7ddac2f08f'),
]
OPS=('EXCEPTION_FLOW','CONTEXT_FLOW','COMPREHENSION_FLOW')
COMP=(ast.ListComp,ast.SetComp,ast.DictComp,ast.GeneratorExp)
def req(n):
 if isinstance(n,(ast.Try,ast.Raise)):return OPS[0]
 if isinstance(n,(ast.With,ast.AsyncWith)):return OPS[1]
 if isinstance(n,COMP):return OPS[2]
 return None
def frontier(n,A):
 r=req(n)
 if r and r not in A:return (r,type(n).__name__)
 for c in ast.iter_child_nodes(n):
  z=frontier(c,A)
  if z:return z
 return None
def funcs(t):return [n for n in ast.walk(t) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))]
rows=[];inventory=[]
for name,url,commit in REPOS:
 root=Path(tempfile.mkdtemp())/name
 subprocess.run(['git','clone','-q',url,str(root)],check=True)
 subprocess.run(['git','checkout','-q',commit],cwd=root,check=True)
 inventory.append({'repo':name,'commit':commit})
 for p in sorted(root.rglob('*.py')):
  try:
   if p.stat().st_size>300000:continue
   tree=ast.parse(p.read_text(encoding='utf-8'))
  except:continue
  for fn in funcs(tree):
   chain=[frontier(fn,frozenset()),frontier(fn,frozenset({OPS[0]})),frontier(fn,frozenset(OPS[:2])),frontier(fn,frozenset(OPS))]
   if chain[0] and chain[1] and chain[2] and [x[0] for x in chain[:3]]==list(OPS) and chain[3] is None:
    rel=str(p.relative_to(root));sid=f'{name}|{commit}|{rel}|{fn.name}|{getattr(fn,"lineno",0)}'
    rows.append({'rank':hashlib.sha256((SEED+'|'+sid).encode()).hexdigest(),'repo':name,'commit':commit,'path':rel,'function':fn.name,'line':getattr(fn,'lineno',0),'chain':chain,'node':fn})
rows.sort(key=lambda x:x['rank'])
R={'protocol':'V33 fixed first-frontier discovery over three independently authored fixed repositories','seed':SEED,'inventory':inventory,'candidate_count':len(rows)}
if not rows:
 R['verdict']='NO_TARGET';(OUT/'RESULT.json').write_text(json.dumps(R,indent=2));print(json.dumps(R,indent=2));raise SystemExit
sel=rows[0];fn=sel.pop('node');R['selected']=sel
A0=frozenset();A1=frozenset({OPS[0]});A2=frozenset(OPS[:2]);A3=frozenset(OPS)
obs={'A0':frontier(fn,A0),'A1':frontier(fn,A1),'A2':frontier(fn,A2),'A3':frontier(fn,A3)};R['obs']=obs
R['ablations']={'A1_minus_O1':frontier(fn,A1-{OPS[0]}),'A2_minus_O1':frontier(fn,A2-{OPS[0]}),'A2_minus_O2':frontier(fn,A2-{OPS[1]})}
R['oracle']={'inject_O1':frontier(fn,frozenset({OPS[0]})),'inject_O1_O2':frontier(fn,frozenset(OPS[:2]))}
R['gates']={
 'O1_first':obs['A0'] and obs['A0'][0]==OPS[0],
 'O1_exposes_O2':obs['A1'] and obs['A1'][0]==OPS[1],
 'O1O2_expose_O3':obs['A2'] and obs['A2'][0]==OPS[2],
 'all_three_close':obs['A3'] is None,
 'ablate_O1_removes_O2_discovery':R['ablations']['A1_minus_O1'] and R['ablations']['A1_minus_O1'][0]==OPS[0],
 'ablate_O2_removes_O3_discovery':R['ablations']['A2_minus_O2'] and R['ablations']['A2_minus_O2'][0]==OPS[1],
 'ablate_O1_from_A2_returns_O1':R['ablations']['A2_minus_O1'] and R['ablations']['A2_minus_O1'][0]==OPS[0],
}
R['verdict']='PASS_EXTERNAL_FRONTIER_DISCOVERABILITY_V33' if all(R['gates'].values()) else 'MIXED_EXTERNAL_FRONTIER_DISCOVERABILITY_V33'
(OUT/'RESULT.json').write_text(json.dumps(R,indent=2));print(json.dumps(R,indent=2))