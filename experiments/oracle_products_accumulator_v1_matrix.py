#!/usr/bin/env python3
import argparse, json, random, pathlib
import torch, torch.nn as nn, torch.nn.functional as F
SEEDS=(0,1,2); STEPS=500; BATCH=256; D=128; H=4; L=2; LR=3e-4
MAX_TERMS=4; MAX_TOTAL=243
torch.set_num_threads(2)

def make_examples(seed,n=12000):
    rr=random.Random(seed); rows=[]
    while len(rows)<n:
        k=rr.randint(1,MAX_TERMS)
        pairs=[(rr.randint(0,9),rr.randint(0,9)) for _ in range(k)]
        prods=[a*b for a,b in pairs]; total=sum(prods)
        if total>MAX_TOTAL: continue
        rows.append((pairs,prods,total,total%10,total//10))
    return rows
class Net(nn.Module):
    def __init__(self,arm):
        super().__init__(); self.arm=arm
        self.de=nn.Embedding(10,D); self.pe=nn.Embedding(82,D); self.te=nn.Embedding(MAX_TERMS+1,D)
        layer=nn.TransformerEncoderLayer(D,H,4*D,batch_first=True,norm_first=True,activation='gelu')
        self.enc=nn.TransformerEncoder(layer,L)
        self.sum_head=nn.Linear(D,10); self.carry_head=nn.Linear(D,MAX_TOTAL//10+2)
    def forward(self,pairs,prods,mask,k):
        x=self.de(pairs[...,0])+self.de(pairs[...,1]) if self.arm=='pairs' else self.pe(prods)
        x=x+self.te(k).unsqueeze(1); x=self.enc(x,src_key_padding_mask=~mask)
        h=(x*mask.unsqueeze(-1)).sum(1)/mask.sum(1,keepdim=True).clamp(min=1)
        return self.sum_head(h),self.carry_head(h)
class AccumNet(nn.Module):
    def __init__(self):
        super().__init__(); self.de=nn.Embedding(10,D); self.pe=nn.Embedding(82,D); self.gru=nn.GRUCell(D,D)
        self.sum_head=nn.Linear(D,10); self.carry_head=nn.Linear(D,MAX_TOTAL//10+2)
    def forward(self,prods,mask):
        h=torch.zeros(prods.size(0),D)
        for j in range(prods.size(1)):
            z=self.pe(prods[:,j]); h2=self.gru(z,h); h=torch.where(mask[:,j:j+1],h2,h)
        return self.sum_head(h),self.carry_head(h)
def batchify(rows,idxs):
    pairs=torch.zeros(len(idxs),MAX_TERMS,2,dtype=torch.long); prods=torch.zeros(len(idxs),MAX_TERMS,dtype=torch.long); mask=torch.zeros(len(idxs),MAX_TERMS,dtype=torch.bool)
    k=torch.zeros(len(idxs),dtype=torch.long); yd=torch.zeros(len(idxs),dtype=torch.long); yc=torch.zeros(len(idxs),dtype=torch.long)
    for i,ix in enumerate(idxs):
        ps,pr,total,dig,car=rows[ix]; k[i]=len(pr); yd[i]=dig; yc[i]=car
        for j,(ab,p) in enumerate(zip(ps,pr)):
            pairs[i,j]=torch.tensor(ab); prods[i,j]=p; mask[i,j]=True
    return pairs,prods,mask,k,yd,yc
@torch.no_grad()
def eval_model(m,rows,idxs,arm):
    m.eval(); tot=digok=carok=both=0; byk={k:[0,0] for k in range(1,MAX_TERMS+1)}
    for st in range(0,len(idxs),512):
        pairs,prods,mask,k,yd,yc=batchify(rows,idxs[st:st+512])
        ld,lc=m(prods,mask) if arm=='accum' else m(pairs,prods,mask,k)
        pd=ld.argmax(-1); pc=lc.argmax(-1); ok=(pd==yd)&(pc==yc)
        digok+=int((pd==yd).sum()); carok+=int((pc==yc).sum()); both+=int(ok.sum()); tot+=len(yd)
        for kk in range(1,MAX_TERMS+1):
            z=(k==kk); byk[kk][0]+=int(ok[z].sum()); byk[kk][1]+=int(z.sum())
    return {'digit':digok/tot,'carry':carok/tot,'joint':both/tot,'by_terms':{str(k):a/max(1,b) for k,(a,b) in byk.items()}}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--seed',type=int,required=True); ap.add_argument('--arm',choices=['pairs','oracle_products','accum'],required=True); ap.add_argument('--out',required=True); a=ap.parse_args()
    seed=a.seed; arm=a.arm
    rows=make_examples(100+seed); rr=random.Random(999+seed); idx=list(range(len(rows))); rr.shuffle(idx); train=idx[:8000]; test=idx[8000:]
    torch.manual_seed(seed); m=AccumNet() if arm=='accum' else Net('pairs' if arm=='pairs' else 'products')
    opt=torch.optim.AdamW(m.parameters(),lr=LR,weight_decay=.01); rng=random.Random(seed); m.train()
    for step in range(STEPS):
        bi=[train[rng.randrange(len(train))] for _ in range(BATCH)]; pairs,prods,mask,k,yd,yc=batchify(rows,bi)
        ld,lc=m(prods,mask) if arm=='accum' else m(pairs,prods,mask,k)
        loss=F.cross_entropy(ld,yd)+F.cross_entropy(lc,yc)
        opt.zero_grad(set_to_none=True); loss.backward(); nn.utils.clip_grad_norm_(m.parameters(),1.0); opt.step()
    r={'seed':seed,'arm':arm,**eval_model(m,rows,test,arm)}
    p=pathlib.Path(a.out); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(r,sort_keys=True)+'\n'); print(json.dumps(r,indent=2,sort_keys=True))
if __name__=='__main__': main()
