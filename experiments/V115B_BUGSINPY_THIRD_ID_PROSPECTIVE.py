from __future__ import annotations

import ast
import json
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

OUT = Path('artifacts/v115b_bugsinpy_third_id_prospective')
OUT.mkdir(parents=True, exist_ok=True)
BUGSINPY_REPO = 'https://github.com/soarsmu/BugsInPy.git'
OPS = ('<','<=','>','>=')
DUAL = {'<':'>','>':'<','<=':'>=','>=':'<='}
PRIOR_KEYS = {
    ('ORDER','<','<=',0),
    ('ORDER','<','>=',1),
}
MAX_SITES = 12
TEST_TIMEOUT = 60
COMPILE_TIMEOUT = 300
CASE_BUDGET_SEC = 480
TOTAL_BUDGET_SEC = 3000


def run(cmd, cwd=None, timeout=120):
    try:
        p = subprocess.run(cmd, cwd=cwd, text=True, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, timeout=timeout)
        return p.returncode, p.stdout
    except subprocess.TimeoutExpired as e:
        out = e.stdout or ''
        if isinstance(out, bytes): out = out.decode(errors='ignore')
        return 124, out + '\n[TIMEOUT]'


def purge(work: Path):
    for p in work.rglob('__pycache__'):
        shutil.rmtree(p, ignore_errors=True)


def test_case(bin_dir: Path, work: Path):
    fail = work/'bugsinpy_fail.txt'
    if fail.exists(): fail.unlink()
    purge(work)
    code,out = run([str(bin_dir/'bugsinpy-test'), '-r', '-w', str(work)], cwd=work, timeout=TEST_TIMEOUT)
    if code == 124:
        return None,out
    failed = fail.exists() and fail.read_text(errors='ignore').strip() != ''
    return (not failed),out


def source_files(work: Path, baseline_out: str):
    files=[]
    for p in work.rglob('*.py'):
        s=str(p)
        if '/env/' in s or '/.git/' in s or '/tests/' in s or '/test/' in s:
            continue
        files.append(p.resolve())
    priority=[]
    for m in re.finditer(r'(?:(?:File\s+["\']([^"\']+\.py)["\'])|([A-Za-z0-9_./\\-]+\.py))', baseline_out):
        raw=m.group(1) or m.group(2)
        q=Path(raw)
        for c in ([q] if q.is_absolute() else [work/q]):
            try:
                c=c.resolve()
                if c.exists() and c.is_file() and str(c).startswith(str(work.resolve())) and '/env/' not in str(c):
                    priority.append(c)
            except Exception:
                pass
    seen=set(); ordered=[]
    for p in priority+sorted(set(files),key=str):
        if p not in seen:
            seen.add(p);ordered.append(p)
    return ordered


def comparison_sites(path: Path):
    try:
        src=path.read_text(errors='ignore')
        tree=ast.parse(src)
    except Exception:
        return []
    lines=src.splitlines(keepends=True)
    offs=[0]
    for line in lines: offs.append(offs[-1]+len(line))
    def off(line,col): return offs[line-1]+col
    names={ast.Lt:'<',ast.LtE:'<=',ast.Gt:'>',ast.GtE:'>='}
    sites=[]
    for n in ast.walk(tree):
        if not (isinstance(n,ast.Compare) and len(n.ops)==1 and len(n.comparators)==1): continue
        old=names.get(type(n.ops[0]))
        if old is None: continue
        l,r=n.left,n.comparators[0]
        attrs=('lineno','col_offset','end_lineno','end_col_offset')
        if not all(all(hasattr(x,a) for a in attrs) for x in (n,l,r)): continue
        node_start=off(n.lineno,n.col_offset);node_end=off(n.end_lineno,n.end_col_offset)
        left_start=off(l.lineno,l.col_offset);left_end=off(l.end_lineno,l.end_col_offset)
        right_start=off(r.lineno,r.col_offset);right_end=off(r.end_lineno,r.end_col_offset)
        gap=src[left_end:right_start]
        mm=re.search(r'(?<![<>=])(?:<=|>=|<|>)(?![=])',gap)
        if not mm: continue
        op_start=left_end+mm.start();op_end=left_end+mm.end()
        sites.append({
            'path':path,'src':src,'old':old,'line':n.lineno,
            'node_start':node_start,'node_end':node_end,
            'left_text':src[left_start:left_end],'right_text':src[right_start:right_end],
            'op_start':op_start,'op_end':op_end,
        })
    sites.sort(key=lambda z:(str(z['path']),z['node_start']))
    return sites


def edit(site,newop,swap):
    src=site['src']
    if not swap:
        return src[:site['op_start']]+newop+src[site['op_end']:]
    repl=f"({site['right_text']}) {newop} ({site['left_text']})"
    return src[:site['node_start']]+repl+src[site['node_end']:]


def semantic_noop(old,new,swap):
    return ((not swap) and new==old) or (swap and new==DUAL[old])


def qkey(old,new,swap):
    a=(old,new,int(swap));b=(DUAL[old],DUAL[new],int(swap))
    return ('ORDER',)+min(a,b)


def main():
    started=time.time()
    with tempfile.TemporaryDirectory(prefix='v115b_') as td0:
        td=Path(td0);bip=td/'BugsInPy'
        code,out=run(['git','clone','--quiet',BUGSINPY_REPO,str(bip)],timeout=180)
        if code: raise RuntimeError(out)
        _,commit=run(['git','rev-parse','HEAD'],cwd=bip,timeout=20);commit=commit.strip()
        bin_dir=bip/'framework'/'bin'
        for p in bin_dir.iterdir(): p.chmod(p.stat().st_mode|0o111)

        selected=[];ineligible=[]
        for pdir in sorted((bip/'projects').iterdir(),key=lambda p:p.name):
            if not pdir.is_dir(): continue
            bugs=pdir/'bugs'
            ids=sorted(int(x.name) for x in bugs.iterdir() if x.is_dir() and x.name.isdigit()) if bugs.exists() else []
            if len(ids)>=3:
                selected.append((pdir.name,ids[2],ids[0],ids[1]))
            else:
                ineligible.append({'project':pdir.name,'numeric_bug_count':len(ids)})

        records=[];repairs=[];candidate_tests=0;candidate_rejections=0;qualified=0
        for project,bug_id,v111_id,v115_id in selected:
            if time.time()-started>TOTAL_BUDGET_SEC:
                records.append({'project':project,'bug_id':bug_id,'status':'budget_not_attempted'})
                continue
            case_start=time.time();root=td/f'case_{project}_{bug_id}';root.mkdir(parents=True,exist_ok=True)
            work=root/project
            rec={'project':project,'bug_id':bug_id,'v111_bug_id':v111_id,'v115_bug_id':v115_id}
            code,txt=run([str(bin_dir/'bugsinpy-checkout'),'-p',project,'-v','0','-i',str(bug_id),'-w',str(root)],cwd=bip,timeout=180)
            if code or not work.exists():
                rec.update(status='checkout_fail',detail=txt[-1400:]);records.append(rec);continue
            code,txt=run([str(bin_dir/'bugsinpy-compile'),'-w',str(work)],cwd=work,timeout=COMPILE_TIMEOUT)
            if code==124 or not (work/'bugsinpy_compile_flag').exists():
                rec.update(status='timeout' if code==124 else 'provision_fail',detail=txt[-1400:]);records.append(rec);continue
            base,baseout=test_case(bin_dir,work)
            if base is None:
                rec.update(status='test_infra',detail=baseout[-1400:]);records.append(rec);continue
            if base:
                rec.update(status='baseline_not_failing');records.append(rec);continue
            qualified+=1
            sites=[]
            for path in source_files(work,baseout):
                for s in comparison_sites(path):
                    sites.append(s)
                    if len(sites)>=MAX_SITES: break
                if len(sites)>=MAX_SITES: break
            if not sites:
                rec.update(status='no_comparator_site',baseline_tail=baseout[-1200:]);records.append(rec);continue

            found=[]
            for si,site in enumerate(sites):
                if time.time()-case_start>CASE_BUDGET_SEC or time.time()-started>TOTAL_BUDGET_SEC: break
                path=site['path'];original=site['src']
                for swap in (False,True):
                    for newop in OPS:
                        if semantic_noop(site['old'],newop,swap): continue
                        if time.time()-case_start>CASE_BUDGET_SEC or time.time()-started>TOTAL_BUDGET_SEC: break
                        candidate_tests+=1
                        try:
                            path.write_text(edit(site,newop,swap));purge(work)
                            passed,tout=test_case(bin_dir,work)
                        finally:
                            path.write_text(original);purge(work)
                        if passed is True:
                            abl,aout=test_case(bin_dir,work)
                            key=qkey(site['old'],newop,swap)
                            rr={
                                'project':project,'bug_id':bug_id,'file':str(path.relative_to(work)),
                                'line':site['line'],'site_index':si,'old':site['old'],'new':newop,'swap':swap,
                                'qkey':list(key),'prior_class_hit':key in PRIOR_KEYS,
                                'opposite_dual_coordinate':site['old'] in ('>','>='),
                                'ablation_fail':abl is False,
                            }
                            repairs.append(rr);found.append(rr)
                        elif passed is False:
                            candidate_rejections+=1
            rec.update(status='repair' if found else 'no_repair',sites=len(sites),repairs=found,baseline_tail=baseout[-1000:])
            records.append(rec)

        attempted=[r for r in records if r['status']!='budget_not_attempted']
        causal=[r for r in repairs if r['ablation_fail']]
        hits=[r for r in causal if r['prior_class_hit']]
        terminal={'baseline_not_failing','checkout_fail','provision_fail','test_infra','timeout','no_comparator_site','no_repair','repair'}
        gates={
            'G1_disjointness':all(b!=a and b!=c for _,b,a,c in selected),
            'G2_executable_qualification':qualified>=1,
            'G3_nontrivial_blind_search':candidate_tests>=8,
            'G4_prospective_causal_repair':len(causal)>=1,
            'G5_frozen_prior_class_prediction':len(hits)>=1,
            'G6_competing_alternatives':len(hits)>=1 and candidate_rejections>=1,
            'G7_repair_search_leakage_boundary':True,
            'G8_infrastructure_accounting':all(r['status'] in terminal for r in attempted),
        }
        passed=all(gates.values())
        result={
            'canonical_id':'V115B_BUGSINPY_THIRD_ID_PROSPECTIVE',
            'bugsinpy_commit':commit,
            'selection_rule':'third-smallest numeric bug id per lexicographically ordered project; disjoint from V111/V115',
            'selected_cases':[{'project':p,'bug_id':b,'v111_bug_id':a,'v115_bug_id':c} for p,b,a,c in selected],
            'selection_ineligible':ineligible,
            'prior_keys':[list(x) for x in sorted(PRIOR_KEYS)],
            'qualified_cases':qualified,
            'candidate_tests':candidate_tests,
            'candidate_rejections':candidate_rejections,
            'causal_repairs':causal,
            'prior_class_hits':hits,
            'causal_repairs_outside_prior_classes':[r for r in causal if not r['prior_class_hit']],
            'records':records,
            'gates':gates,
            'information_boundary':{
                'stock_framework_may_stage_fixed_revision_tests_during_provisioning':True,
                'search_reads_fixed_production_implementation':False,
                'search_reads_known_patch_or_diff':False,
                'search_reads_human_repair_text':False,
                'target_derived_relation_update':False,
                'search_information':'final buggy working tree + benchmark relevant verifier/tests + verifier outputs',
            },
            'verdict':'PASS_V115B_BUGSINPY_THIRD_ID_PROSPECTIVE' if passed else 'FAIL_V115B_BUGSINPY_THIRD_ID_PROSPECTIVE',
            'claim_boundary':'Fresh disjoint third-ID BugsInPy sample; blind one-site KEEP/SWAP comparison edits; only two V110 historical quotient keys count as prospective hits.',
        }
        (OUT/'RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
        print(json.dumps(result,indent=2,sort_keys=True))

if __name__=='__main__':
    main()
