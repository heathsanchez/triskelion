// Exact browser/Node port of the frozen V103 finite-world quotient experiment.
// No model calls, no prerecorded verdict toggles: this computes the result from scratch.

const SEED_ACQ = 202608151703;
const SEED_HOLD = 202608151704;
const XOR = 0b0110;

export function ttValue(tt, x, y) {
  return (tt >> ((x << 1) | y)) & 1;
}

export function isAffineBinary(tt) {
  const vals = [ttValue(tt,0,0), ttValue(tt,0,1), ttValue(tt,1,0), ttValue(tt,1,1)];
  const c = vals[0], a = vals[2] ^ c, b = vals[1] ^ c;
  return vals.join(',') === [c, b ^ c, a ^ c, a ^ b ^ c].join(',');
}

export function transformTT(tt, swap, nx, ny, no) {
  let out = 0;
  for (let idx=0; idx<4; idx++) {
    let x=(idx>>1)&1, y=idx&1;
    if (nx) x ^= 1;
    if (ny) y ^= 1;
    if (swap) [x,y]=[y,x];
    let v=ttValue(tt,x,y);
    if (no) v ^= 1;
    out |= v << idx;
  }
  return out;
}

export function orbit(tt) {
  const s = new Set();
  for (const sw of [0,1]) for (const nx of [0,1]) for (const ny of [0,1]) for (const no of [0,1]) s.add(transformTT(tt,sw,nx,ny,no));
  return [...s].sort((a,b)=>a-b);
}

function varFunc(n,j) {
  let out=0;
  for (let a=0;a<(1<<n);a++) out |= (((a>>j)&1) << a);
  return out;
}
function constFunc(n,c) { return c===0 ? 0 : (1 << (1<<n)) - 1; }
function applyBinary(n,f,g,tt) {
  let out=0;
  for (let a=0;a<(1<<n);a++) {
    const x=(f>>a)&1, y=(g>>a)&1;
    out |= ttValue(tt,x,y) << a;
  }
  return out;
}

function exactCostTable(n,candidate,maxCost=17) {
  const cost=new Map(), byCost=new Map();
  const add=(c,f)=>{ if(!byCost.has(c)) byCost.set(c,[]); byCost.get(c).push(f); };
  for(let j=0;j<n;j++){ const f=varFunc(n,j); cost.set(f,1); add(1,f); }
  for(const c of [0,1]){ const f=constFunc(n,c); if(!cost.has(f)){cost.set(f,1); add(1,f);} }
  const ops = candidate===null ? [XOR] : [XOR,candidate];
  const admitted=[...new Set(cost.keys())].sort((a,b)=>a-b), rank=new Map();
  admitted.forEach((f,i)=>rank.set(f,i+1));
  const seen=new Set(admitted);
  for(let total=3;total<=maxCost;total+=2){
    const fresh=[];
    for(let lc=1;lc<total-1;lc+=2){
      const rc=total-1-lc;
      for(const f of (byCost.get(lc)||[])) for(const g of (byCost.get(rc)||[])) for(const op of ops){
        const h=applyBinary(n,f,g,op);
        if(!cost.has(h)){cost.set(h,total); fresh.push(h);}
      }
    }
    if(fresh.length){
      const uniq=[...new Set(fresh)].sort((a,b)=>a-b); byCost.set(total,uniq);
      for(const h of uniq) if(!seen.has(h)){seen.add(h); admitted.push(h); rank.set(h,admitted.length);}
    }
    if(cost.size === (1 << (1<<n))) break;
  }
  return {cost,rank};
}

// Python random.Random compatibility is not needed for the demo because the frozen
// hidden representatives and generated target sets are part of the precommitted V103
// instance. We recompute all closure, orbit, scoring and search-accounting claims over
// those frozen targets rather than replaying the verdict.
const ACQ_TARGETS = [1,22,23,25,26,28,37,38,41,43,46,52,67,73,74,82,88,97,104,109,121,128,131,134,137,146,152,164,193,194];
const HOLD_TARGETS = [7,11,13,14,19,21,25,26,28,35,37,38,41,42,44,49,50,52,56,67,69,70,73,74,76,81,82,84,88,97,98,100,104,112,131,133,134,137,138,140,145,146,148,152,161,162,164,193,194,196];

export function runExactDemo(){
  const hiddenAcq=1, hiddenHold=8;
  const nonaff=[...Array(16).keys()].filter(x=>!isAffineBinary(x));
  const affine=[...Array(16).keys()].filter(isAffineBinary);
  const base=exactCostTable(3,null);
  const tables=new Map();
  for(const tt of nonaff) tables.set(tt,exactCostTable(3,tt));
  const packageTotal=(tt,targets)=>6+targets.reduce((s,f)=>s+tables.get(tt).cost.get(f),0);
  const acqScores=Object.fromEntries(nonaff.map(tt=>[tt,packageTotal(tt,ACQ_TARGETS)]));
  const bestAcq=Math.min(...Object.values(acqScores));
  const winners=nonaff.filter(tt=>acqScores[tt]===bestAcq);
  const holdScores=Object.fromEntries(nonaff.map(tt=>[tt,packageTotal(tt,HOLD_TARGETS)]));
  const bestHold=Math.min(...Object.values(holdScores));
  const holdWinners=nonaff.filter(tt=>holdScores[tt]===bestHold);
  const selectedHold=Math.min(...winners.map(tt=>holdScores[tt]));
  const cold=HOLD_TARGETS.reduce((sum,f)=>sum+Math.min(...nonaff.map(tt=>6+tables.get(tt).cost.get(f))),0);
  const warm=Math.min(...winners.map(tt=>6+HOLD_TARGETS.reduce((s,f)=>s+tables.get(tt).cost.get(f),0)));
  let coldStates=0;
  for(const f of HOLD_TARGETS) for(const tt of nonaff) coldStates += tables.get(tt).rank.get(f);
  const warmStates=Math.min(...winners.map(tt=>Math.max(...HOLD_TARGETS.map(f=>tables.get(tt).rank.get(f))));
  const sameOrbit=orbit(hiddenAcq).join(',')===orbit(hiddenHold).join(',');
  const result={
    oldClosureSize:base.cost.size,
    affineBinaryOperators:affine,
    hiddenAcq,hiddenHold,
    orbit:orbit(hiddenAcq),sameOrbit,
    acquisitionScores:acqScores,winners,bestAcq,
    heldoutScores:holdScores,holdWinners,bestHold,selectedHold,
    warmGovernedCost:warm,coldGovernedCost:cold,
    coldSemanticStateExpansions:coldStates,warmSemanticStateExpansions:warmStates,
    searchCompression:coldStates/warmStates,
    gates:{
      oldLanguageObstruction:base.cost.size===16 && HOLD_TARGETS.every(f=>!base.cost.has(f)),
      differentLiteralSameCapability:hiddenAcq!==hiddenHold && sameOrbit,
      discoveredClassTransfers:winners.every(tt=>orbit(tt).join(',')===orbit(hiddenAcq).join(',')) && selectedHold<=1.10*bestHold,
      compressionAtLeast4x:coldStates>=4*warmStates,
      warmCheaperThanCold:warm<cold
    }
  };
  result.pass=Object.values(result.gates).every(Boolean);
  return result;
}
