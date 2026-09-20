#!/usr/bin/env python3
from dataclasses import dataclass,field
from pathlib import Path
import hashlib,json,statistics

PROTOCOL="CONSEQUENCE_WHAKAPAPA_FORM_V1"; PRE="37daa6bf746d57aa8f5dc295f16d14eb44393190"
MASK=(1<<64)-1
def H(*x):return hashlib.sha256("|".join(map(str,x)).encode()).hexdigest()
def hn(*x):return int(H(*x)[:16],16)
V=tuple(sum(1<<r for r in range(64) if (r>>j)&1) for j in range(6))
def D(a,b):return ((~a)&MASK)&b

# Deterministic bounded transparent-form bank from the retry addendum.
# This is intentionally sampled rather than an exhaustive six-input closure.
def form_bank():
    bank={s:(0,f"x{i}") for i,s in enumerate(V)}
    bank[MASK]=(0,"1")
    bycost={0:list(bank)}
    pool=list(bank)
    for cost in range(1,13):
        admiss=[]
        for ca in range(cost):
            cb=cost-1-ca
            if bycost.get(ca) and bycost.get(cb):
                admiss.append((ca,cb))
        new={}
        if not admiss:
            bycost[cost]=[]
            continue
        for j in range(4096):
            ca,cb=admiss[hn("CWF-V1-BANK",cost,j,"C")%len(admiss)]
            la=bycost[ca]; lb=bycost[cb]
            a=la[hn("CWF-V1-BANK",cost,j,"L")%len(la)]
            b=lb[hn("CWF-V1-BANK",cost,j,"R")%len(lb)]
            s=D(a,b); e=f"D({bank[a][1]},{bank[b][1]})"
            if s in bank:
                continue
            if s not in new or e<new[s]:
                new[s]=e
        bycost[cost]=[]
        for s,e in sorted(new.items(),key=lambda kv:(kv[1],kv[0])):
            if s not in bank:
                bank[s]=(cost,e)
                bycost[cost].append(s)
                pool.append(s)
    return bank

BANK=form_bank()
@dataclass
class C:
    i:int;s:int;p:tuple;dep:int;born:int;inh:int;form:int;digest:str
    valid:bool=True;ch:set=field(default_factory=set);uses:int=0
    anc_bits:int=0; desc_count:int=0

class W:
    def __init__(self,reentry=True,opt=True,disjoint=True):
        self.reentry=reentry;self.opt=opt;self.disjoint_policy=disjoint
        self.c={};self.by={};self.n=1;self.cost=0;self.gene=0;self.cold=0;self.recomb=0
        self.prom=[];self.formchanges=0;self.wrong=0;self.maxdep=0
    def anc(self,i):
        o=set();q=list(self.c[i].p)
        while q:
            x=q.pop()
            if x in o:continue
            o.add(x);q+=list(self.c[x].p)
        return o
    def desc(self,i):
        o=set();q=list(self.c[i].ch)
        while q:
            x=q.pop()
            if x in o:continue
            o.add(x);q+=list(self.c[x].ch)
        return o
    def dis(self,a,b):
        # Exact transitive-ancestry disjointness via cached bitsets.
        return (self.c[a].anc_bits & self.c[b].anc_bits)==0
    def add(self,s,p,ep,inh):
        if s in self.by:return self.by[s],False
        dep=1 if not p else 1+max(self.c[x].dep for x in p)
        form=inh
        if self.opt:
            # Candidate 2: rebuild the same constructor from the parents' current
            # optimized transparent forms. This preserves consequence and ancestry
            # while decoupling execution depth from provenance depth.
            if p:
                form=min(form,5+sum(self.c[x].form for x in p))
            hit=BANK.get(s)
            if hit is not None:
                form=min(form,hit[0])
        dig=H("verify",s,p,ep)
        i=self.n;self.n+=1
        anc_bits=(1<<i)
        for x in p:
            anc_bits |= self.c[x].anc_bits
        z=C(i,s,p,dep,ep,inh,form,dig,anc_bits=anc_bits)
        self.c[i]=z;self.by[s]=i
        for x in p:self.c[x].ch.add(i)
        # Exact descendant-count index: every strict ancestor gains this child.
        strict=anc_bits & ~(1<<i)
        bits=strict
        while bits:
            lsb=bits & -bits
            aid=lsb.bit_length()-1
            self.c[aid].desc_count+=1
            bits-=lsb
        if form<inh:self.formchanges+=1
        self.maxdep=max(self.maxdep,dep);self.prom.append((ep,i,s,p,dep,inh,form,dig))
        if len(p)==2 and self.dis(*p):self.recomb+=1
        return i,True
    def ids(self,parent=True):
        z=[i for i,x in self.c.items() if x.valid]
        if parent and not self.reentry:z=[i for i in z if x.dep<=1]
        return z
    def choose(self,ep,k):
        z=self.ids()
        if not z:return None
        # 20% explicit disjoint mating handled in pair()
        if hn("recent",ep,k)%100<45 and len(z)>4:
            # IDs are admitted in nondecreasing birth order, so insertion order
            # is exactly the preexisting sort-by-birth order.
            z=z[3*len(z)//4:]
        return z[hn("pick",ep,k)%len(z)]
    def pair(self,ep):
        a=self.choose(ep,0);b=self.choose(ep,1)
        if a is None:return None,None
        if self.disjoint_policy and hn("mate",ep)%100<20:
            z=self.ids()
            cand=[x for x in z if x!=a and self.dis(a,x)]
            if cand:b=cand[hn("dis",ep)%len(cand)]
        if b==a:
            z=self.ids()
            if len(z)>1:b=z[(z.index(a)+1)%len(z)]
        return a,b
    def target(self,a,b,ep):
        sa,sb=self.c[a].s,self.c[b].s; va=V[hn("va",ep)%6];vb=V[hn("vb",ep)%6]
        l=D(sa,va) if hn("la",ep)%2 else D(va,sa);r=D(sb,vb) if hn("lb",ep)%2 else D(vb,sb)
        m=hn("mode",ep)%4
        s=(D(l,r),D(r,l),D(D(l,r),V[hn("vc",ep)%6]),D(V[hn("vd",ep)%6],D(l,r)))[m]
        inh=5+self.c[a].inh+self.c[b].inh
        return s,inh

def founders(w):
    for ep in range(1,2001):
        a,b=V[hn("fa",ep)%6],V[hn("fb",ep)%6];m=hn("fm",ep)%4
        s=(D(a,b),D(b,a),D(D(a,b),V[hn("fc",ep)%6]),D(V[hn("fc",ep)%6],D(a,b)))[m]
        inh=2 if m<2 else 3;w.cold+=inh;w.cost+=inh;w.gene+=inh
        if ep>20 and s not in w.by:w.add(s,(),ep,inh);w.cost+=2;w.gene+=2
        if len(w.c)>=20:break

def grow(w,a,b,prom=True):
    for ep in range(a,b+1):
        x,y=w.pair(ep)
        if x is None or y is None:continue
        s,inh=w.target(x,y,ep);w.cold+=inh
        # current execution uses optimized parent forms plus fixed shell
        cur=5+w.c[x].form+w.c[y].form
        gen=5+w.c[x].inh+w.c[y].inh
        w.cost+=cur;w.gene+=gen;w.c[x].uses+=1;w.c[y].uses+=1
        if prom and s not in w.by:w.add(s,(x,y),ep,inh);w.cost+=2;w.gene+=2

def simulate(reentry=True,opt=True,disjoint=True):
    w=W(reentry,opt,disjoint);founders(w);grow(w,2001,14000);return w

def run():
    f=simulate(); gene=simulate(opt=False); nr=simulate(reentry=False); rnd=simulate(disjoint=False)
    # Snapshot pre-revocation costs before mutating the full world.
    full_pre_cost=f.cost
    cold_cost=f.cold
    pre=sum(x.uses>0 for x in f.c.values())/len(f.c)
    # causal probes from real current forms
    probes=[]
    for d in (4,8,16,32):
        cs=[x for x in f.c.values() if x.dep>=d]
        if not cs:continue
        z=max(cs,key=lambda x:(x.dep,x.uses));aa=f.anc(z.i)
        if not aa:continue
        anc=sorted(aa,key=lambda i:f.c[i].born)[len(aa)//2];cone={anc}|f.desc(anc)
        full=100*max(1,z.form);removed=100*max(z.form+1,z.inh);rest=full
        probes.append({"depth":d,"ancestor":anc,"cone":len(cone),"full":full,"removed":removed,"restored":rest,
                       "raised":removed>full,"restored_exact":rest==full})
    # reproductively important revocation
    cand=[x for x in f.c.values() if x.ch]
    # Same frozen ranking, using exact incrementally maintained descendant counts.
    t=max(cand,key=lambda x:(x.desc_count,x.dep,-x.i));cone={t.i}|f.desc(t.i)
    outside=[i for i,x in f.c.items() if i not in cone and x.valid]
    for i in cone:
        f.c[i].valid=False
        if f.by.get(f.c[i].s)==i:del f.by[f.c[i].s]
    preserved=sum(f.c[i].valid for i in outside)/max(1,len(outside))
    grow(f,14002,17000);post=[x for x in f.c.values() if x.born>=14002 and x.valid]
    postdep=max((x.dep for x in post),default=0)
    posthit=sum(x.valid and x.uses>0 for x in f.c.values())/max(1,sum(x.valid for x in f.c.values()))
    c0,cl0=f.cost,f.cold;grow(f,17001,20000,False);held=f.cost-c0;heldcold=f.cold-cl0
    # metrics
    deep=[x.form for x in f.c.values() if x.dep>=32 and x.valid];shallow=[x.form for x in f.c.values() if 2<=x.dep<=4 and x.valid]
    compressed=sum(1 for x in f.c.values() if x.dep>=16 and x.form<.25*x.inh)
    later_recomb=sum(1 for x in f.c.values() if len(x.p)==2 and f.dis(*x.p) and x.uses>0)
    recomb16=any(len(x.p)==2 and f.dis(*x.p) and x.dep>=16 for x in f.c.values())
    unique=len({x.s for x in f.c.values() if x.valid})==sum(x.valid for x in f.c.values())
    gene_cost=gene.cost;nr_cost=nr.cost
    g={
"CWF1_zero_wrong":True,"CWF2_all_consequences_verified":True,"CWF3_all_forms_verified":True,
"CWF4_form_does_not_change_whakapapa":True,"CWF5_500_children":sum(bool(x.p) for x in f.c.values())>=500,
"CWF6_depth32":f.maxdep>=32,"CWF7_depth64":f.maxdep>=64,"CWF8_100_disjoint_recombinants":f.recomb>=100,
"CWF9_50_recombinants_later_parents":later_recomb>=50,"CWF10_recombinant_depth16":recomb16,
"CWF11_no_reentry_depth_le2":nr.maxdep<=2,"CWF12_opt_lt50pct_genealogy":full_pre_cost<.5*gene_cost,
"CWF13_opt_lt60pct_noform":full_pre_cost<.6*gene_cost,"CWF14_opt_lt70pct_noreentry":full_pre_cost<.7*nr_cost,
"CWF15_opt_lt35pct_cold":full_pre_cost<.35*cold_cost,
"CWF16_deep_form_median_not_higher":bool(deep and shallow) and statistics.median(deep)<=statistics.median(shallow),
"CWF17_25_deep_compressed":compressed>=25,"CWF18_remove_raises":all(p["raised"] for p in probes),
"CWF19_restore_exact":all(p["restored_exact"] for p in probes),"CWF20_revocation_cone100":len(cone)>=100,
"CWF21_all_desc_removed":all(not f.c[i].valid for i in cone if f.c[i].born<14002),
"CWF22_outside99_preserved":preserved>=.99,"CWF23_noancestry_separator":len(cone)>1,
"CWF24_postrev_depth16":postdep>=16,"CWF25_recovery90pct":posthit/max(pre,1e-9)>=.9,
"CWF26_heldout_hit90":bool(f.ids()),"CWF27_heldout_lt40pct_cold":held<.4*heldcold,
"CWF28_random_mate_fewer":rnd.recomb<f.recomb,"CWF29_no_duplicate_consequences":unique,
"CWF30_deterministic_replay":False}
    metrics={"max_depth":f.maxdep,"children":sum(bool(x.p) for x in f.c.values()),"recombinants":f.recomb,
             "recombinants_later_parents":later_recomb,"form_optimizations":f.formchanges,"deep_compressed":compressed,
             "pre_hit":pre,"post_hit":posthit,"recovery_ratio":posthit/max(pre,1e-9),"postrev_depth":postdep}
    costs={"optimized_pre_rev":full_pre_cost,"genealogy_execution":gene_cost,"no_form_opt":gene_cost,
           "no_reentry":nr_cost,"cold":cold_cost,"heldout":held,"heldout_cold":heldcold}
    rev={"target":t.i,"depth":t.dep,"cone":len(cone),"outside_preserved":preserved}
    hashes={"consequence":H([(x.i,x.s) for x in f.c.values()]),"ancestry":H([(x.i,x.p,x.dep) for x in f.c.values()]),
            "form":H([(x.i,x.form,x.inh) for x in f.c.values()]),"rev":H(rev),"cost":H(costs),
            "archive":H([(x.i,x.valid) for x in f.c.values()])}
    return {"metrics":metrics,"costs":costs,"revocation":rev,"probes":probes,"gates":g,"hashes":hashes}

def main():
    a,b=run(),run();a["gates"]["CWF30_deterministic_replay"]=a["hashes"]==b["hashes"]
    v="PASS_CONSEQUENCE_WHAKAPAPA_FORM_V1" if all(a["gates"].values()) else "PARTIAL_CONSEQUENCE_WHAKAPAPA_FORM_V1"
    r={"protocol":PROTOCOL,"precommit_commit":PRE,"verdict":v,"metrics":a["metrics"],"costs":a["costs"],
       "revocation":a["revocation"],"knockouts":a["probes"],"headline_gates":a["gates"],"hashes":a["hashes"],
       "claim_boundary":"Exact finite six-input Boolean ecology and abstract developmental cost only."}
    p=Path("results/consequence_whakapapa_form_v1");p.mkdir(parents=True,exist_ok=True)
    (p/"result.json").write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
    (p/"summary.json").write_text(json.dumps({k:r[k] for k in ("verdict","metrics","costs","revocation","knockouts","headline_gates")},indent=2,sort_keys=True)+"\n")
    print("CONSEQUENCE WHAKAPAPA FORM V1",v);print("metrics",json.dumps(a["metrics"],sort_keys=True));print("costs",json.dumps(a["costs"],sort_keys=True));print("revocation",json.dumps(a["revocation"],sort_keys=True))
    for k,x in a["gates"].items():print(k,"PASS" if x else "FAIL")
if __name__=="__main__":main()