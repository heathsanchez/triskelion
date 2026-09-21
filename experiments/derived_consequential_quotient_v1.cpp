#include <algorithm>
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <map>
#include <numeric>
#include <string>
#include <vector>
using namespace std;

static constexpr int Q=3;
static constexpr int OP_COUNT=19683;
static constexpr int POINTED_COUNT=59049;
static constexpr int P3[9]={1,3,9,27,81,243,729,2187,6561};
static uint8_t DIG2[OP_COUNT][9];
static uint8_t DIG1[27][3];
static const int PERMS[6][3]={{0,1,2},{0,2,1},{1,0,2},{1,2,0},{2,0,1},{2,1,0}};

struct ClosureSet { vector<uint8_t> seen; vector<int> elems; bool all_constants=false; };
struct Rounds { array<string,4> sig; array<int,4> count{}; int recombinant3=0; };
struct Rec { int distinct_sum=0, distinct_max=0, cycle_sum=0, cycle_max=0; };

static void init_digits(){
    for(int x=0;x<OP_COUNT;x++){ int y=x; for(int i=0;i<9;i++){DIG2[x][i]=uint8_t(y%3); y/=3;} }
    for(int x=0;x<27;x++){ int y=x; for(int i=0;i<3;i++){DIG1[x][i]=uint8_t(y%3); y/=3;} }
}
static array<uint8_t,9> decode_op(int code){ array<uint8_t,9> t{}; for(int i=0;i<9;i++){t[i]=uint8_t(code%3);code/=3;} return t; }
static int encode_op(const array<uint8_t,9>& t){ int z=0; for(int i=0;i<9;i++) z+=int(t[i])*P3[i]; return z; }
static inline int ov(const array<uint8_t,9>& op,int a,int b){return op[3*a+b];}

static int canonical_key(int rawkey){
    int g=rawkey/OP_COUNT, code=rawkey%OP_COUNT; auto old=decode_op(code); int best=POINTED_COUNT+1;
    for(int pi=0;pi<6;pi++){ const int* p=PERMS[pi]; for(int sw=0;sw<2;sw++){
        array<uint8_t,9> nt{};
        for(int a=0;a<3;a++) for(int b=0;b<3;b++){ int oa=sw?b:a, ob=sw?a:b; nt[3*p[a]+p[b]]=uint8_t(p[ov(old,oa,ob)]); }
        best=min(best,p[g]*OP_COUNT+encode_op(nt));
    }}
    return best;
}

static int proj1_code(){return 0+1*3+2*9;}
static int const1_code(int g){return g*(1+3+9);}
static int proj2_x0(){int z=0; for(int i=0;i<9;i++) z+=(i/3)*P3[i]; return z;}
static int proj2_x1(){int z=0; for(int i=0;i<9;i++) z+=(i%3)*P3[i]; return z;}
static int const2_code(int g){int z=0;for(int i=0;i<9;i++)z+=g*P3[i];return z;}

static inline int compose1(const array<uint8_t,9>& op,int f,int h){
    int z=0; z += op[3*DIG1[f][0]+DIG1[h][0]]; z += int(op[3*DIG1[f][1]+DIG1[h][1]])*3; z += int(op[3*DIG1[f][2]+DIG1[h][2]])*9; return z;
}
static inline int compose2(const array<uint8_t,9>& op,int f,int h){
    int z=0; const uint8_t* F=DIG2[f]; const uint8_t* H=DIG2[h];
    for(int i=0;i<9;i++) z += int(op[3*F[i]+H[i]])*P3[i];
    return z;
}
static string encode_seen(const vector<uint8_t>& seen){
    static const char* H="0123456789abcdef"; string s; s.reserve((seen.size()+3)/4);
    for(size_t i=0;i<seen.size();i+=4){ int v=0; for(int k=0;k<4;k++) if(i+k<seen.size() && seen[i+k]) v|=(1<<k); s.push_back(H[v]); }
    return s;
}
static ClosureSet fixed2(const array<uint8_t,9>& op,int ground){
    ClosureSet c; c.seen.assign(OP_COUNT,0); c.elems.reserve(OP_COUNT);
    auto add=[&](int z){ if(!c.seen[z]){c.seen[z]=1;c.elems.push_back(z);} };
    add(proj2_x0()); add(proj2_x1()); if(ground>=0) add(const2_code(ground));
    bool comm=true; for(int a=0;a<3;a++)for(int b=0;b<3;b++)if(ov(op,a,b)!=ov(op,b,a))comm=false;
    for(size_t qi=0; qi<c.elems.size() && c.elems.size()<OP_COUNT; ++qi){
        int f=c.elems[qi]; size_t lim=c.elems.size();
        for(size_t j=0;j<lim && c.elems.size()<OP_COUNT;j++){ int h=c.elems[j]; add(compose2(op,f,h)); if(!comm && c.elems.size()<OP_COUNT) add(compose2(op,h,f)); }
    }
    c.all_constants=true; for(int a=0;a<3;a++) c.all_constants &= bool(c.seen[const2_code(a)]);
    return c;
}
static int fixed1_count(const array<uint8_t,9>& op,int ground){
    vector<uint8_t> seen(27,0); vector<int> elems; elems.reserve(27);
    auto add=[&](int z){if(!seen[z]){seen[z]=1; elems.push_back(z);}};
    add(proj1_code()); if(ground>=0)add(const1_code(ground));
    bool comm=true; for(int a=0;a<3;a++)for(int b=0;b<3;b++)if(ov(op,a,b)!=ov(op,b,a))comm=false;
    for(size_t qi=0; qi<elems.size() && elems.size()<27; ++qi){
        int f=elems[qi]; size_t lim=elems.size();
        for(size_t j=0;j<lim && elems.size()<27;j++){ int h=elems[j]; add(compose1(op,f,h)); if(!comm && elems.size()<27)add(compose1(op,h,f)); }
    }
    return int(elems.size());
}
static bool essential_both(int f){
    const uint8_t* F=DIG2[f]; bool e0=false,e1=false;
    for(int y=0;y<3;y++)for(int a=0;a<3;a++)for(int b=a+1;b<3;b++)if(F[3*a+y]!=F[3*b+y])e0=true;
    for(int x=0;x<3;x++)for(int a=0;a<3;a++)for(int b=a+1;b<3;b++)if(F[3*x+a]!=F[3*x+b])e1=true;
    return e0&&e1;
}
static Rounds rounds3(const array<uint8_t,9>& op,int g){
    vector<uint8_t> seen(OP_COUNT,0); vector<int> elems; elems.reserve(OP_COUNT);
    auto add=[&](int z){if(!seen[z]){seen[z]=1;elems.push_back(z);}};
    add(proj2_x0()); add(proj2_x1()); add(const2_code(g));
    Rounds r; r.count[0]=int(elems.size()); r.sig[0]=encode_seen(seen);
    for(int round=1;round<=3;round++){ vector<int> prev=elems; for(int a:prev) for(int b:prev) add(compose2(op,a,b)); r.count[round]=int(elems.size()); r.sig[round]=encode_seen(seen); }
    for(int f:elems) if(essential_both(f)) r.recombinant3++;
    return r;
}
static pair<int,int> local_cycle(const array<uint8_t,9>& op,int a,int b){
    int first[9]; fill(begin(first),end(first),-1); int t=0;
    while(true){ int s=3*a+b; if(first[s]>=0)return {first[s],t-first[s]}; first[s]=t++; int c=ov(op,a,b); a=b; b=c; }
}
static long long gcdll(long long a,long long b){while(b){long long t=a%b;a=b;b=t;}return a;}
static long long lcmll(long long a,long long b){return a/gcdll(a,b)*b;}
static Rec recurrence(const array<uint8_t,9>& op,int g){
    int seeds[3]={proj2_x0(),proj2_x1(),const2_code(g)}; pair<int,int> lc[3][3];
    for(int a=0;a<3;a++)for(int b=0;b<3;b++)lc[a][b]=local_cycle(op,a,b);
    Rec r;
    for(int i=0;i<3;i++)for(int j=0;j<3;j++){
        int f=seeds[i], h=seeds[j], mu=0; long long lam=1;
        for(int pos=0;pos<9;pos++){ auto [m,l]=lc[DIG2[f][pos]][DIG2[h][pos]]; mu=max(mu,m); lam=lcmll(lam,l); }
        int distinct=mu+int(lam); r.distinct_sum+=distinct; r.distinct_max=max(r.distinct_max,distinct); r.cycle_sum+=int(lam); r.cycle_max=max(r.cycle_max,int(lam));
    }
    return r;
}

int main(int argc,char**argv){
    if(argc!=4){cerr<<"usage: derived_quotient SHARD SHARDS OUT.tsv\n";return 2;}
    int shard=stoi(argv[1]), shards=stoi(argv[2]); string outpath=argv[3]; init_digits();
    map<int,int> orbit; for(int raw=0;raw<POINTED_COUNT;raw++)orbit[canonical_key(raw)]++;
    vector<pair<int,int>> reps; long long wsum=0; for(auto &kv:orbit) if(kv.first%shards==shard){reps.push_back(kv);wsum+=kv.second;}
    ofstream out(outpath);
    out<<"#META\t"<<shard<<"\t"<<shards<<"\t"<<reps.size()<<"\t"<<wsum<<"\n";
    out<<"key\tweight\tground\topcode\tunary\tbinary\tno_ground\tno_ground_all_constants\td0\td1\td2\td3\trecombinant3\trecur_distinct_sum\trecur_distinct_max\trecur_cycle_sum\trecur_cycle_max\th0_sig\th1_sig\th2_sig\th3_sig\tfixed_sig\tno_ground_sig\n";
    for(size_t i=0;i<reps.size();i++){
        auto [key,w]=reps[i]; int g=key/OP_COUNT,code=key%OP_COUNT; auto op=decode_op(code);
        int unary=fixed1_count(op,g); auto fg=fixed2(op,g); auto fn=fixed2(op,-1); auto rd=rounds3(op,g); auto rc=recurrence(op,g);
        out<<key<<"\t"<<w<<"\t"<<g<<"\t"<<code<<"\t"<<unary<<"\t"<<fg.elems.size()<<"\t"<<fn.elems.size()<<"\t"<<int(fn.all_constants)
           <<"\t"<<rd.count[0]<<"\t"<<rd.count[1]<<"\t"<<rd.count[2]<<"\t"<<rd.count[3]<<"\t"<<rd.recombinant3<<"\t"<<rc.distinct_sum<<"\t"<<rc.distinct_max<<"\t"<<rc.cycle_sum<<"\t"<<rc.cycle_max
           <<"\t"<<rd.sig[0]<<"\t"<<rd.sig[1]<<"\t"<<rd.sig[2]<<"\t"<<rd.sig[3]<<"\t"<<encode_seen(fg.seen)<<"\t"<<encode_seen(fn.seen)<<"\n";
        if((i+1)%25==0) cerr<<"shard "<<shard<<": "<<(i+1)<<"/"<<reps.size()<<"\n";
    }
    cerr<<"DONE shard="<<shard<<" reps="<<reps.size()<<" weight="<<wsum<<"\n";
}
