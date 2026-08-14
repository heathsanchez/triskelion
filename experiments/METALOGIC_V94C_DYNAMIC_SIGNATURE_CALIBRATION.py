#!/usr/bin/env python3
import hashlib,json,math,sys
from pathlib import Path
OUT=Path('results/v94c'); OUT.mkdir(parents=True,exist_ok=True)
SEED='V94C_DYNAMIC_SIGNATURE_CALIBRATION_2026-08-14'
DIMS=['events','calls','returns','exceptions','max_depth','unique_lines','revisits','coll_grow','coll_shrink','num_up','num_down','locals_grow','locals_shrink']

def h(x):return hashlib.sha256((SEED+'|'+x).encode()).hexdigest()
def norm(v):
 z=math.sqrt(sum(x*x for x in v));return [x/z for x in v] if z else [0]*len(v)
def sim(a,b):return sum(x*y for x,y in zip(norm(a),norm(b)))
def delta(a,b):return [b[k]-a[k] for k in DIMS]

def trace_run(fn,n):
 m={k:0 for k in DIMS};seen=set();last={};depth=0
 def snap(fr):
  coll=0;num=0.0
  for v in fr.f_locals.values():
   try:
    if isinstance(v,(list,tuple,set,dict,str,bytes)):coll+=len(v)
    elif isinstance(v,(int,float)) and not isinstance(v,bool):num+=float(v)
   except:pass
  return coll,num,len(fr.f_locals)
 def tr(fr,ev,arg):
  nonlocal depth
  if fr.f_code.co_filename!=__file__:return tr
  if ev=='call':m['calls']+=1;depth+=1;m['max_depth']=max(m['max_depth'],depth)
  elif ev=='return':m['returns']+=1;depth=max(0,depth-1)
  elif ev=='exception':m['exceptions']+=1
  if ev=='line':
   m['events']+=1;key=fr.f_lineno
   if key in seen:m['revisits']+=1
   else:seen.add(key);m['unique_lines']+=1
   s=snap(fr);k=id(fr)
   if k in last:
    p=last[k]
    m['coll_grow']+=s[0]>p[0];m['coll_shrink']+=s[0]<p[0]
    m['num_up']+=s[1]>p[1];m['num_down']+=s[1]<p[1]
    m['locals_grow']+=s[2]>p[2];m['locals_shrink']+=s[2]<p[2]
   last[k]=s
  return tr
 old=sys.gettrace();sys.settrace(tr)
 try:fn(n)
 finally:sys.settrace(old)
 return m

def retain_bug(n):
 s=set()
 for i in range(n):
  _=i in s
 return len(s)
def retain_fix(n):
 s=set()
 for i in range(n):
  if i not in s:s.add(i)
 return len(s)
def frontier_bug(n):
 q=list(range(n));steps=0
 while q and steps<n:
  _=q[0];steps+=1
 return len(q)
def frontier_fix(n):
 q=list(range(n));steps=0
 while q and steps<n:
  q.pop(0);steps+=1
 return len(q)
def fixed_bug(n):
 x=n;steps=0
 while x>0 and steps<n:
  x=x;steps+=1
 return x
def fixed_fix(n):
 x=n;steps=0
 while x>0 and steps<n:
  x-=1;steps+=1
 return x
F={'RETAIN':(retain_bug,retain_fix),'FRONTIER':(frontier_bug,frontier_fix),'FIXEDPOINT':(fixed_bug,fixed_fix)}

def perm(v):
 order=sorted(range(len(DIMS)),key=lambda i:h('perm|'+DIMS[i]));return [v[i] for i in order]

def main():
 train_ns=[3,5,7,9];test_ns=[4,6,8,10,12]
 prot={};rows=[]
 for name,(b,f) in F.items():
  ds=[]
  for n in train_ns:ds.append(delta(trace_run(b,n),trace_run(f,n)))
  prot[name]=[sum(x[i] for x in ds)/len(ds) for i in range(len(DIMS))]
 correct=0;null_correct=0;total=0
 for true,(b,f) in F.items():
  for n in test_ns:
   d=delta(trace_run(b,n),trace_run(f,n));pred=max(prot,key=lambda k:sim(d,prot[k]))
   pp={k:perm(v) for k,v in prot.items()};np=max(pp,key=lambda k:sim(d,pp[k]))
   correct+=pred==true;null_correct+=np==true;total+=1
   rows.append({'family':true,'n':n,'pred':pred,'null_pred':np,'scores':{k:round(sim(d,v),5) for k,v in prot.items()}})
 gates={'three_distinct_mechanisms':len(F)==3,'heldout_accuracy_ge_80':correct/total>=.8,'beats_permuted_null':correct>null_correct}
 verdict='PASS_DYNAMIC_SIGNATURE_CALIBRATION_V94C' if all(gates.values()) else 'MIXED_DYNAMIC_SIGNATURE_CALIBRATION_V94C'
 res={'protocol':'V94C_DYNAMIC_SIGNATURE_CALIBRATION','dims':DIMS,'prototypes':prot,'accuracy':correct/total,'null_accuracy':null_correct/total,'rows':rows,'gates':gates,'verdict':verdict,'qualification':'Authored calibration only. Establishes whether the V94 execution-delta measurement can distinguish three known state-transition mechanisms across held-out sizes; it is not natural-world evidence.'}
 (OUT/'RESULT.json').write_text(json.dumps(res,indent=2));print(json.dumps(res,indent=2))
if __name__=='__main__':main()
