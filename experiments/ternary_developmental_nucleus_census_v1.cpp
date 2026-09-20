#include <algorithm>
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <map>
#include <numeric>
#include <set>
#include <string>
#include <vector>

using namespace std;

static constexpr int OP_COUNT=19683;
static constexpr int POINTED_COUNT=59049;
static constexpr int P3[9]={1,3,9,27,81,243,729,2187,6561};
static uint8_t DIG[OP_COUNT][9];
static const int PERMS[6][3]={{0,1,2},{0,2,1},{1,0,2},{1,2,0},{2,0,1},{2,1,0}};

struct Dev {
    int d[4]{};
    int recombinant3=0;
    int recur_distinct_sum=0;
    int recur_distinct_max=0;
    int recur_cycle_sum=0;
    int recur_cycle_max=0;
};

static void init_digits(){
    for(int x=0;x<OP_COUNT;x++){
        int y=x;
        for(int i=0;i<9;i++){DIG[x][i]=uint8_t(y%3);y/=3;}
    }
}
static array<uint8_t,9> decode_op(int code){
    array<uint8_t,9> t{};
    int x=code;
    for(int i=0;i<9;i++){t[i]=uint8_t(x%3);x/=3;}
    return t;
}
static int encode_op(const array<uint8_t,9>& t){
    int x=0;for(int i=0;i<9;i++)x+=int(t[i])*P3[i];return x;
}
static inline int ov(const array<uint8_t,9>& op,int a,int b){return op[3*a+b];}
static int canonical_key(int rawkey){
    int g=rawkey/OP_COUNT,code=rawkey%OP_COUNT;
    auto old=decode_op(code);
    int best=POINTED_COUNT+1;
    for(int pi=0;pi<6;pi++){
        auto p=PERMS[pi];
        for(int sw=0;sw<2;sw++){
            array<uint8_t,9> nt{};
            for(int a=0;a<3;a++)for(int b=0;b<3;b++){
                int oa=sw?b:a,ob=sw?a:b;
                nt[3*p[a]+p[b]]=uint8_t(p[ov(old,oa,ob)]);
            }
            best=min(best,p[g]*OP_COUNT+encode_op(nt));
        }
    }
    return best;
}
static int x0code(){
    int z=0;for(int i=0;i<9;i++)z+=(i/3)*P3[i];return z;
}
static int x1code(){
    int z=0;for(int i=0;i<9;i++)z+=(i%3)*P3[i];return z;
}
static int ccode(int g){
    int z=0;for(int i=0;i<9;i++)z+=g*P3[i];return z;
}
static inline int compose(const array<uint8_t,9>& op,int f,int h){
    int z=0;
    const uint8_t* F=DIG[f];const uint8_t* H=DIG[h];
    for(int i=0;i<9;i++)z+=int(op[3*F[i]+H[i]])*P3[i];
    return z;
}
static bool essential_both(int f){
    const uint8_t* F=DIG[f];
    bool e0=false,e1=false;
    for(int y=0;y<3;y++)
        for(int a=0;a<3;a++)for(int b=a+1;b<3;b++)
            if(F[3*a+y]!=F[3*b+y])e0=true;
    for(int x=0;x<3;x++)
        for(int a=0;a<3;a++)for(int b=a+1;b<3;b++)
            if(F[3*x+a]!=F[3*x+b])e1=true;
    return e0&&e1;
}
static pair<int,int> local_cycle(const array<uint8_t,9>& op,int a,int b){
    int first[9];fill(begin(first),end(first),-1);
    int t=0;
    while(true){
        int s=3*a+b;
        if(first[s]>=0)return {first[s],t-first[s]};
        first[s]=t++;
        int c=ov(op,a,b);
        a=b;b=c;
    }
}
static long long gcdll(long long a,long long b){while(b){long long t=a%b;a=b;b=t;}return a;}
static long long lcmll(long long a,long long b){return a/gcdll(a,b)*b;}

static Dev metrics(int key){
    int g=key/OP_COUNT, code=key%OP_COUNT;
    auto op=decode_op(code);
    static vector<uint8_t> seen(OP_COUNT);
    fill(seen.begin(),seen.end(),0);
    vector<int> S;
    auto add=[&](int z){if(!seen[z]){seen[z]=1;S.push_back(z);}};
    int seeds[3]={x0code(),x1code(),ccode(g)};
    for(int z:seeds)add(z);

    Dev d;d.d[0]=(int)S.size();
    for(int r=1;r<=3;r++){
        vector<int> prev=S;
        vector<int> fresh;
        for(int a:prev)for(int b:prev){
            int z=compose(op,a,b);
            if(!seen[z]){seen[z]=1;fresh.push_back(z);}
        }
        S.insert(S.end(),fresh.begin(),fresh.end());
        d.d[r]=(int)S.size();
    }
    for(int f:S)if(essential_both(f))d.recombinant3++;

    pair<int,int> lc[3][3];
    for(int a=0;a<3;a++)for(int b=0;b<3;b++)lc[a][b]=local_cycle(op,a,b);

    for(int i=0;i<3;i++)for(int j=0;j<3;j++){
        int f=seeds[i],h=seeds[j];
        int mu=0; long long lam=1;
        for(int pos=0;pos<9;pos++){
            auto [m,l]=lc[DIG[f][pos]][DIG[h][pos]];
            mu=max(mu,m);lam=lcmll(lam,l);
        }
        int distinct=mu+(int)lam;
        d.recur_distinct_sum+=distinct;
        d.recur_distinct_max=max(d.recur_distinct_max,distinct);
        d.recur_cycle_sum+=(int)lam;
        d.recur_cycle_max=max(d.recur_cycle_max,(int)lam);
    }
    return d;
}

int main(int argc,char**argv){
    if(argc!=4){cerr<<"usage: dev SHARD SHARDS OUT.tsv\n";return 2;}
    int shard=stoi(argv[1]),shards=stoi(argv[2]);string outpath=argv[3];
    init_digits();
    map<int,int> orbit;
    for(int raw=0;raw<POINTED_COUNT;raw++)orbit[canonical_key(raw)]++;
    vector<pair<int,int>> reps;
    long long wsum=0;
    for(auto &kv:orbit)if(kv.first%shards==shard){reps.push_back(kv);wsum+=kv.second;}

    ofstream out(outpath);
    out<<"#META\t"<<shard<<"\t"<<shards<<"\t"<<reps.size()<<"\t"<<wsum<<"\n";
    out<<"key\tweight\td0\td1\td2\td3\trecombinant3\trecur_distinct_sum\trecur_distinct_max\trecur_cycle_sum\trecur_cycle_max\n";
    for(size_t i=0;i<reps.size();i++){
        auto [key,w]=reps[i];Dev d=metrics(key);
        out<<key<<"\t"<<w<<"\t"<<d.d[0]<<"\t"<<d.d[1]<<"\t"<<d.d[2]<<"\t"<<d.d[3]<<"\t"<<d.recombinant3
           <<"\t"<<d.recur_distinct_sum<<"\t"<<d.recur_distinct_max<<"\t"<<d.recur_cycle_sum<<"\t"<<d.recur_cycle_max<<"\n";
    }
    cerr<<"DONE shard="<<shard<<" reps="<<reps.size()<<" weight="<<wsum<<"\n";
    return 0;
}
