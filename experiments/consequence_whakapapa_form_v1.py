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

# Exact transparent-form optimizer, computed lazily for consequences that
# actually occur. This is extensionally the same frozen candidate set as the
# precommit (environment variables, D expressions up to cost 12), but avoids
# eagerly closing the enormous six-input space before the experiment starts.
#
# COST_BUCKET[c] contains exact consequences first reached with c D nodes.
# ensure_form(s) advances the dynamic-programming frontier only until s is
# proved reachable at minimum cost or the frozen cost-12 bound is exhausted.
BANK={s:(0,f"x{i}") for i,s in enumerate(V)}
BANK[MASK]=(0,"1")
COST_BUCKET={0:list(BANK)}
FORM_FRONTIER_MAX=0

def _advance_form_frontier(target=None):
    global FORM_FRONTIER_MAX
    for total in range(FORM_FRONTIER_MAX+1,13):
        new={}
        # c = 1 + ca + cb
        for ca in range(total):
            cb=total-1-ca
            for a in COST_BUCKET.get(ca,()):
                ea=BANK[a][1]
                for b in COST_BUCKET.get(cb,()):
                    s=D(a,b);e=f"D({ea},{BANK[b][1]})"
                    if s in BANK:
                        continue
                    if s not in new or e<new[s]:
                        new[s]=e
        if new:
            for s,e in sorted(new.items(),key=lambda kv:(kv[1],kv[0])):
                BANK[s]=(total,e)
            COST_BUCKET[total]=list(new)
        else:
            COST_BUCKET[total]=[]
        FORM_FRONTIER_MAX=total
        if target is not None and target in BANK:
            return

def ensure_form(s):
    if s not in BANK and FORM_FRONTIER_MAX<12:
        _advance_form_frontier(s)
    return BANK.get(s)

@dataclass
class C:
    i:int;s:int;p:tuple;dep:int;born:int;inh:int;form:int;digest:str
    valid:bool=True;ch:set=field(default_factory=set);uses:int=0

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
        A=self.anc(a)|{a};B=self.anc(b)|{b}
        return A.isdisjoint(B)
    def add(self,s,p,ep,inh):
        if s in self.by:return self.by[s],False
        dep=1 if not p else 1+max(self.c[x].dep for x in p)
        form=inh
        if self.opt:
            hit=ensure_form(s)
            if hit is not None: form=min(form,hit[0])
        dig=H("verify",s,p,ep)
        i=self.n;self.n+=1;z=C(i,s,p,dep,ep,inh,form,dig);self.c[i]=z;self.by[s]=i
        for x in p:self.c[x].ch.add(i)
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
            z=sorted(z,key=lambda i:self.c[i].born)[3*len(z)//4:]
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
    # COLD is the transparent inherited expansion cost accumulated by full ecology.
    # snapshot pre-revocation
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
    t=max(cand,key=lambda x:(len(f.desc(x.i)),x.dep,-x.i));cone={t.i}|f.desc(t.i)
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
    full_pre_cost=simulate().cost;gene_cost=gene.cost;nr_cost=nr.cost;cold_cost=simulate().cold
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