#include <algorithm>
#include <array>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <set>
#include <sstream>
#include <string>
#include <unordered_map>
#include <vector>

using namespace std;

static constexpr int Q = 3;
static constexpr int OP_COUNT = 19683; // 3^9
static constexpr int POINTED_COUNT = 59049;
static constexpr int POW3_9[9] = {1,3,9,27,81,243,729,2187,6561};
static uint8_t DIG2[OP_COUNT][9];
static uint8_t DIG1[27][3];

static const int AUDIT_KEYS[256] = {
43717,57661,5852,9039,7322,45270,21591,24528,9626,28342,18648,47359,6204,11940,55200,58342,
14433,6873,23828,20761,23041,14606,26459,29913,15916,34762,55020,24383,1181,55715,48851,23532,
10337,54567,21098,54009,26285,47938,16056,56339,48940,38594,49381,2109,31061,50010,45212,10043,
26049,34034,4188,58184,56375,11421,29651,26691,2459,45420,17796,56287,36833,34478,14586,7941,
20753,23224,7209,49192,16438,36228,32633,3263,34519,10801,29131,49768,51896,31718,55533,8848,
2236,43702,29922,42107,36908,374,4452,31627,5145,14839,48043,30320,46320,22632,29568,55235,
55222,44347,5807,55377,22245,25964,57721,8343,48997,48508,502,35326,41174,12410,51575,11809,
43116,42402,9516,57435,16612,56236,17793,15398,25338,22534,39336,8912,41748,29894,21215,49205,
53404,42611,54197,19942,39090,1615,8167,9896,3433,37159,7237,51006,29459,55546,31838,31872,
52683,42633,26682,13681,34849,57081,10823,11188,9798,29653,47643,48623,645,15475,51830,12979,
35992,24346,28781,43731,25566,41384,45410,1954,18435,11031,45960,53456,29530,49502,58172,38265,
3523,58685,45387,35187,12335,9430,33612,29595,53637,143,13380,36846,10191,33496,53582,536,
22118,17903,38105,24157,28412,31644,42172,8059,39078,27205,38289,24082,40479,38339,52273,23071,
31217,48923,13361,46788,51541,22329,54292,47592,22995,9686,13107,39146,16841,31942,21169,50946,
15723,27163,18684,48242,4955,8820,55915,16019,44946,51616,56247,13524,29014,29848,11753,28482,
51721,21598,15662,40346,33622,30960,17776,31042,22978,41927,45190,35350,15704,31948,24431,48454
};

struct Closure {
    int count = 0;
    bool all_constants = false;
    uint64_t hash = 0;
};

struct Metrics {
    int unary_count=0;
    int binary_count=0;
    int no_ground_count=0;
    int fresh_delta=0;
    int ref_delta=0;
    bool no_ground_all_constants=false;
    bool generative=false;
    uint64_t unary_hash=0, binary_hash=0, no_ground_hash=0;
};

struct Features {
    bool commutative=false, idempotent=false, associative=false, conservative=false;
    bool cancellative=false, any_one_identity=false, two_identity=false;
    bool any_one_absorber=false, two_absorber=false;
    bool ground_one_identity=false, ground_two_identity=false;
    bool ground_one_absorber=false, ground_two_absorber=false;
    bool diag_ground_fixed=false;
    int asymmetry_score=0, image_size=0, diag_image_size=0;
    int isotone_orders=0, residual_orders=0, ground_top_residual_orders=0;
};

static void init_digits() {
    for (int x=0;x<OP_COUNT;x++) {
        int y=x;
        for (int i=0;i<9;i++){ DIG2[x][i]=uint8_t(y%3); y/=3; }
    }
    for (int x=0;x<27;x++) {
        int y=x;
        for (int i=0;i<3;i++){ DIG1[x][i]=uint8_t(y%3); y/=3; }
    }
}

static array<uint8_t,9> decode_op(int code) {
    array<uint8_t,9> t{};
    int x=code;
    for(int i=0;i<9;i++){t[i]=uint8_t(x%3);x/=3;}
    return t;
}
static int encode_op(const array<uint8_t,9>& t) {
    int x=0;
    for(int i=0;i<9;i++) x += int(t[i])*POW3_9[i];
    return x;
}
static int opval(const array<uint8_t,9>& op,int a,int b){ return op[3*a+b]; }

static const int PERMS[6][3]={{0,1,2},{0,2,1},{1,0,2},{1,2,0},{2,0,1},{2,1,0}};

static int canonical_key(int rawkey) {
    int g=rawkey/OP_COUNT, code=rawkey%OP_COUNT;
    auto old=decode_op(code);
    int best=POINTED_COUNT+1;
    for(int pi=0;pi<6;pi++){
        const int* p=PERMS[pi];
        for(int sw=0;sw<2;sw++){
            array<uint8_t,9> nt{};
            for(int a=0;a<3;a++) for(int b=0;b<3;b++){
                int oa=sw?b:a, ob=sw?a:b;
                nt[3*p[a]+p[b]]=uint8_t(p[opval(old,oa,ob)]);
            }
            int ng=p[g], nc=encode_op(nt);
            best=min(best,ng*OP_COUNT+nc);
        }
    }
    return best;
}

static uint64_t fnv_hash(vector<int> elems) {
    sort(elems.begin(), elems.end());
    uint64_t h=1469598103934665603ULL;
    for(int x:elems){
        uint32_t u=(uint32_t)x;
        for(int k=0;k<4;k++){
            h ^= uint8_t((u>>(8*k))&255);
            h *= 1099511628211ULL;
        }
    }
    return h;
}

static int proj1_code(){ return 0 + 1*3 + 2*9; }
static int const1_code(int g){ return g*(1+3+9); }
static int proj2_x0(){
    int code=0;
    for(int idx=0;idx<9;idx++) code += (idx/3)*POW3_9[idx];
    return code;
}
static int proj2_x1(){
    int code=0;
    for(int idx=0;idx<9;idx++) code += (idx%3)*POW3_9[idx];
    return code;
}
static int const2_code(int g){
    int s=0;
    for(int i=0;i<9;i++) s+=g*POW3_9[i];
    return s;
}

static inline int compose1(const array<uint8_t,9>& op,int f,int g){
    int z=0;
    z += op[3*DIG1[f][0]+DIG1[g][0]];
    z += int(op[3*DIG1[f][1]+DIG1[g][1]])*3;
    z += int(op[3*DIG1[f][2]+DIG1[g][2]])*9;
    return z;
}
static inline int compose2(const array<uint8_t,9>& op,int f,int g){
    int z=0;
    const uint8_t* F=DIG2[f]; const uint8_t* G=DIG2[g];
    for(int i=0;i<9;i++) z += int(op[3*F[i]+G[i]])*POW3_9[i];
    return z;
}

static Closure closure1(const array<uint8_t,9>& op,int ground){
    bool seen[27]={false};
    vector<int> e; e.reserve(27);
    auto add=[&](int x){ if(!seen[x]){seen[x]=true;e.push_back(x);} };
    add(proj1_code()); if(ground>=0) add(const1_code(ground));
    bool comm=true;
    for(int a=0;a<3;a++)for(int b=0;b<3;b++) if(opval(op,a,b)!=opval(op,b,a)) comm=false;
    for(size_t qi=0; qi<e.size() && e.size()<27; ++qi){
        int f=e[qi]; size_t lim=e.size();
        for(size_t j=0;j<lim && e.size()<27;j++){
            int g=e[j]; add(compose1(op,f,g));
            if(!comm) add(compose1(op,g,f));
        }
    }
    bool allc=true;
    for(int c=0;c<3;c++) allc &= seen[const1_code(c)];
    return {(int)e.size(),allc,fnv_hash(e)};
}

static Closure closure2(const array<uint8_t,9>& op,int ground){
    static vector<uint8_t> seen(OP_COUNT);
    fill(seen.begin(),seen.end(),0);
    vector<int> e; e.reserve(OP_COUNT);
    auto add=[&](int x){ if(!seen[x]){seen[x]=1;e.push_back(x);} };
    add(proj2_x0()); add(proj2_x1()); if(ground>=0) add(const2_code(ground));
    bool comm=true;
    for(int a=0;a<3;a++)for(int b=0;b<3;b++) if(opval(op,a,b)!=opval(op,b,a)) comm=false;
    for(size_t qi=0; qi<e.size() && e.size()<OP_COUNT; ++qi){
        int f=e[qi]; size_t lim=e.size();
        for(size_t j=0;j<lim && e.size()<OP_COUNT;j++){
            int g=e[j]; add(compose2(op,f,g));
            if(!comm && e.size()<OP_COUNT) add(compose2(op,g,f));
        }
    }
    bool allc=true;
    for(int c=0;c<3;c++) allc &= bool(seen[const2_code(c)]);
    return {(int)e.size(),allc,fnv_hash(e)};
}

static Metrics metrics_for(int rawkey){
    int g=rawkey/OP_COUNT, code=rawkey%OP_COUNT;
    auto op=decode_op(code);
    Closure u=closure1(op,g), b=closure2(op,g), n=closure2(op,-1);
    Metrics m;
    m.unary_count=u.count; m.binary_count=b.count; m.no_ground_count=n.count;
    m.fresh_delta=b.count-u.count; m.ref_delta=b.count-n.count;
    m.no_ground_all_constants=n.all_constants;
    m.generative=(b.count>3 && m.fresh_delta>0 && (m.ref_delta>0 || n.all_constants));
    m.unary_hash=u.hash;m.binary_hash=b.hash;m.no_ground_hash=n.hash;
    return m;
}

static bool leq_rank(const int rank[3],int a,int b){ return rank[a]<=rank[b]; }

static Features features_for(int rawkey){
    int g=rawkey/OP_COUNT, code=rawkey%OP_COUNT;
    auto op=decode_op(code);
    Features f;
    set<int> image,diag;
    f.commutative=true;f.idempotent=true;f.associative=true;f.conservative=true;
    for(int a=0;a<3;a++)for(int b=0;b<3;b++){
        int v=opval(op,a,b); image.insert(v);
        if(a==b)diag.insert(v);
        if(opval(op,a,b)!=opval(op,b,a) && a<b) f.asymmetry_score++;
        if(opval(op,a,b)!=opval(op,b,a)) f.commutative=false;
        if(a==b && v!=a) f.idempotent=false;
        if(v!=a && v!=b) f.conservative=false;
    }
    for(int a=0;a<3;a++)for(int b=0;b<3;b++)for(int c=0;c<3;c++)
        if(opval(op,opval(op,a,b),c)!=opval(op,a,opval(op,b,c))) f.associative=false;
    bool leftcan=true,rightcan=true;
    for(int a=0;a<3;a++){
        set<int>L,R;
        for(int b=0;b<3;b++){L.insert(opval(op,a,b));R.insert(opval(op,b,a));}
        leftcan &= (L.size()==3);rightcan &= (R.size()==3);
    }
    f.cancellative=leftcan&&rightcan;
    bool anyLId=false,anyRId=false,anyLAbs=false,anyRAbs=false;
    for(int e=0;e<3;e++){
        bool lid=true,rid=true,labs=true,rabs=true;
        for(int a=0;a<3;a++){
            lid &= opval(op,e,a)==a; rid &= opval(op,a,e)==a;
            labs &= opval(op,e,a)==e; rabs &= opval(op,a,e)==e;
        }
        anyLId|=lid;anyRId|=rid;anyLAbs|=labs;anyRAbs|=rabs;
        if(lid&&rid)f.two_identity=true;
        if(labs&&rabs)f.two_absorber=true;
        if(e==g){
            f.ground_one_identity=lid||rid;f.ground_two_identity=lid&&rid;
            f.ground_one_absorber=labs||rabs;f.ground_two_absorber=labs&&rabs;
        }
    }
    f.any_one_identity=anyLId||anyRId;f.any_one_absorber=anyLAbs||anyRAbs;
    f.diag_ground_fixed=opval(op,g,g)==g;
    f.image_size=(int)image.size();f.diag_image_size=(int)diag.size();

    int res1=0,res2=0;
    for(int pi=0;pi<6;pi++){
        int rank[3]; for(int i=0;i<3;i++)rank[PERMS[pi][i]]=i;
        bool iso1=true,iso2=true,anti1=true,anti2=true;
        for(int a=0;a<3;a++)for(int ap=0;ap<3;ap++) if(leq_rank(rank,a,ap)){
            for(int b=0;b<3;b++){
                iso1 &= leq_rank(rank,opval(op,a,b),opval(op,ap,b));
                anti1 &= leq_rank(rank,opval(op,ap,b),opval(op,a,b));
            }
        }
        for(int b=0;b<3;b++)for(int bp=0;bp<3;bp++) if(leq_rank(rank,b,bp)){
            for(int a=0;a<3;a++){
                iso2 &= leq_rank(rank,opval(op,a,b),opval(op,a,bp));
                anti2 &= leq_rank(rank,opval(op,a,bp),opval(op,a,b));
            }
        }
        if(iso1&&iso2)f.isotone_orders++;
        bool r1=anti1&&iso2, r2=iso1&&anti2;
        if(r1)res1++; if(r2)res2++;
        if(rank[g]==2 && (r1||r2))f.ground_top_residual_orders++;
    }
    f.residual_orders=max(res1,res2);
    return f;
}

static string hex64(uint64_t x){
    stringstream ss; ss<<hex<<setw(16)<<setfill('0')<<x; return ss.str();
}

int main(int argc,char**argv){
    if(argc!=4){ cerr<<"usage: census SHARD SHARDS OUT.tsv\n"; return 2; }
    int shard=stoi(argv[1]), shards=stoi(argv[2]); string outpath=argv[3];
    init_digits();

    map<int,int> orbit;
    for(int raw=0;raw<POINTED_COUNT;raw++) orbit[canonical_key(raw)]++;

    vector<int> reps;
    long long weight_sum=0;
    for(auto &kv:orbit) if((kv.first%shards)==shard){reps.push_back(kv.first);weight_sum+=kv.second;}

    unordered_map<int,Metrics> metric_cache;
    ofstream out(outpath);
    out<<"#META\t"<<shard<<"\t"<<shards<<"\t"<<reps.size()<<"\t"<<weight_sum<<"\n";
    out<<"key\tweight\tground\topcode\tunary\tbinary\tno_ground\tfresh_delta\tref_delta\tno_ground_all_constants\tgenerative"
       <<"\tcommutative\tidempotent\tassociative\tconservative\tcancellative\tany_one_identity\ttwo_identity"
       <<"\tany_one_absorber\ttwo_absorber\tground_one_identity\tground_two_identity\tground_one_absorber\tground_two_absorber"
       <<"\tdiag_ground_fixed\tasymmetry_score\timage_size\tdiag_image_size\tisotone_orders\tresidual_orders\tground_top_residual_orders"
       <<"\tunary_hash\tbinary_hash\tno_ground_hash\n";

    for(size_t ri=0;ri<reps.size();ri++){
        int key=reps[ri]; Metrics m=metrics_for(key); Features f=features_for(key); metric_cache[key]=m;
        int g=key/OP_COUNT, code=key%OP_COUNT, w=orbit[key];
        out<<key<<"\t"<<w<<"\t"<<g<<"\t"<<code<<"\t"<<m.unary_count<<"\t"<<m.binary_count<<"\t"<<m.no_ground_count
           <<"\t"<<m.fresh_delta<<"\t"<<m.ref_delta<<"\t"<<m.no_ground_all_constants<<"\t"<<m.generative
           <<"\t"<<f.commutative<<"\t"<<f.idempotent<<"\t"<<f.associative<<"\t"<<f.conservative<<"\t"<<f.cancellative
           <<"\t"<<f.any_one_identity<<"\t"<<f.two_identity<<"\t"<<f.any_one_absorber<<"\t"<<f.two_absorber
           <<"\t"<<f.ground_one_identity<<"\t"<<f.ground_two_identity<<"\t"<<f.ground_one_absorber<<"\t"<<f.ground_two_absorber
           <<"\t"<<f.diag_ground_fixed<<"\t"<<f.asymmetry_score<<"\t"<<f.image_size<<"\t"<<f.diag_image_size
           <<"\t"<<f.isotone_orders<<"\t"<<f.residual_orders<<"\t"<<f.ground_top_residual_orders
           <<"\t"<<hex64(m.unary_hash)<<"\t"<<hex64(m.binary_hash)<<"\t"<<hex64(m.no_ground_hash)<<"\n";
        if((ri+1)%25==0) cerr<<"shard "<<shard<<": "<<(ri+1)<<"/"<<reps.size()<<"\n";
    }
    out.close();

    int audit_total=0,audit_pass=0;
    for(int raw:AUDIT_KEYS){
        int ck=canonical_key(raw);
        if((ck%shards)!=shard) continue;
        audit_total++;
        Metrics rawm=metrics_for(raw);
        auto it=metric_cache.find(ck);
        if(it==metric_cache.end()){ cerr<<"missing canonical rep "<<ck<<"\n"; continue; }
        Metrics cm=it->second;
        bool ok=rawm.unary_count==cm.unary_count && rawm.binary_count==cm.binary_count &&
                rawm.no_ground_count==cm.no_ground_count && rawm.fresh_delta==cm.fresh_delta &&
                rawm.ref_delta==cm.ref_delta;
        if(ok)audit_pass++; else cerr<<"AUDIT FAIL raw "<<raw<<" canon "<<ck<<"\n";
    }
    ofstream meta(outpath+".audit");
    meta<<audit_total<<"\t"<<audit_pass<<"\n";
    cerr<<"DONE shard="<<shard<<" reps="<<reps.size()<<" weight="<<weight_sum<<" audits="<<audit_pass<<"/"<<audit_total<<"\n";
    return audit_total==audit_pass?0:3;
}
