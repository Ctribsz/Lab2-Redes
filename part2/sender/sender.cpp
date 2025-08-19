#include <bits/stdc++.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <unistd.h>
using namespace std;

#define RESET   "\033[0m"
#define BOLD    "\033[1m"
#define GREEN   "\033[32m"
#define RED     "\033[31m"
#define CYAN    "\033[36m"
#define YELLOW  "\033[33m"
#define GRAY    "\033[90m"

// Utilidades presentación
static string ascii_to_bits(const string& s){
    string out; out.reserve(s.size()*8);
    for(unsigned char c: s){
        for(int i=7;i>=0;--i) out.push_back(((c>>i)&1)?'1':'0');
    }
    return out;
}
static string group_every(const string& s, int n){
    string out; out.reserve(s.size()+s.size()/n);
    for(size_t i=0;i<s.size();++i){
        if(i && (i % n == 0)) out.push_back(' ');
        out.push_back(s[i]);
    }
    return out;
}

// ---------- CRC32 ----------
static uint32_t crc32_bits(const string& bits){
    uint32_t crc = 0xFFFFFFFFu, poly = 0x04C11DB7u;
    for(char c: bits){
        if(c!='0'&&c!='1') throw runtime_error("Bits invalidos");
        uint32_t b = (c=='1')?1u:0u;
        uint32_t top = (crc>>31)&1u;
        uint32_t fb = top ^ b;
        crc <<= 1;
        if(fb) crc ^= poly;
    }
    crc ^= 0xFFFFFFFFu;
    return crc;
}
static string to_bin32(uint32_t x){
    string s(32,'0');
    for(int i=31;i>=0;--i) s[31-i] = ((x>>i)&1u)?'1':'0';
    return s;
}

// ---------- Hamming ----------
static bool isPow2(int x){ return x && ((x&(x-1))==0); }
static int r_for_k(int k){ int r=0; while(k + r + 1 > (1<<r)) r++; return r; }

static string hamming_encode_block(const string& data){
    int k = (int)data.size();
    int r = r_for_k(k);
    int n = k + r;
    vector<int> code(n+1,0);
    for(int i=1, j=0; i<=n; ++i) if(!isPow2(i)) code[i] = (data[j++]=='1');
    for(int i=0;i<r;++i){
        int p = 1<<i, parity=0;
        for(int kpos=1;kpos<=n;++kpos) if(kpos & p) parity ^= code[kpos];
        code[p] = parity;
    }
    string out; out.reserve(n);
    for(int i=1;i<=n;++i) out.push_back(code[i]?'1':'0');
    return out;
}

static string hamming_encode_stream(const string& bits, int k, int& pad_bits, int& r_out){
    r_out = r_for_k(k);
    pad_bits = (k - (int(bits.size())%k))%k;
    string padded = bits + string(pad_bits,'0');
    string out;
    for(size_t i=0;i<padded.size(); i+=k){
        string block = padded.substr(i,k);
        out += hamming_encode_block(block);
    }
    return out;
}

// ---------- Ruido ----------
static string apply_noise(const string& bits, double p){
    std::mt19937_64 rng( std::random_device{}() );
    std::bernoulli_distribution flip(p);
    string out(bits);
    for(char& c: out){ if(flip(rng)) c = (c=='1'?'0':'1'); }
    return out;
}

// ---------- Sockets ----------
static bool send_line(const string& host, int port, const string& line){
    int sock = socket(AF_INET, SOCK_STREAM, 0);
    if(sock<0){ perror("socket"); return false; }
    sockaddr_in addr{}; addr.sin_family = AF_INET; addr.sin_port = htons(port);
    if(inet_pton(AF_INET, host.c_str(), &addr.sin_addr)<=0){ cerr<<"IP invalida\n"; close(sock); return false; }
    if(connect(sock,(sockaddr*)&addr,sizeof(addr))<0){ perror("connect"); close(sock); return false; }
    ssize_t n = send(sock, line.data(), line.size(), 0);
    bool ok = (n==(ssize_t)line.size());
    close(sock);
    return ok;
}

// ---------- main ----------
int main(){

    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    cout << unitbuf;

    cout<<BOLD<<CYAN
        <<"=====================================\n"
        <<" EMISOR por CAPAS (CRC32 / HAMMING)\n"
        <<"=====================================\n"<<RESET;

    cout<<YELLOW<<"Mensaje a enviar (texto ASCII): "<<RESET<<flush;
    string msg; getline(cin, msg);
    if(msg.empty()){ cerr<<RED<<"❌ Mensaje vacio.\n"<<RESET; return 1; }

    cout<<YELLOW<<"Algoritmo [1=CRC32, 2=HAMMING]: "<<RESET<<flush;
    int alg=0; cin>>alg;
    if(alg!=1 && alg!=2){ cerr<<RED<<"❌ Opcion invalida.\n"<<RESET; return 1; }

    int k=0;
    if(alg==2){
        cout<<YELLOW<<"Hamming k (ej. 4/8/11): "<<RESET<<flush;
        cin>>k; if(k<=0 || k>64){ cerr<<RED<<"❌ k invalido.\n"<<RESET; return 1; }
    }

    double p=0.0;
    cout<<YELLOW<<"Probabilidad de error por bit (ej. 0.00, 0.01, 0.05): "<<RESET<<flush;
    cin>>p; if(p<0 || p>1){ cerr<<RED<<"❌ p invalido.\n"<<RESET; return 1; }

    string host="127.0.0.1"; int port=50007;
    cout<<YELLOW<<"IP receptor [enter=127.0.0.1]: "<<RESET<<flush;
    cin.ignore(numeric_limits<streamsize>::max(), '\n');
    string tmp; getline(cin,tmp); if(!tmp.empty()) host=tmp;
    cout<<YELLOW<<"Puerto receptor [enter=50007]: "<<RESET<<flush;
    getline(cin,tmp); if(!tmp.empty()) port=stoi(tmp);

    string bits = ascii_to_bits(msg);

    // --- ENLACE ---
    string frame_bits;
    string crcBits; uint32_t crc_val=0;
    int r=0,n=0,pad=0;

    if(alg==1){
        crc_val = crc32_bits(bits);
        crcBits = to_bin32(crc_val);
        frame_bits = bits + crcBits;
    }else{
        frame_bits = hamming_encode_stream(bits, k, pad, r);
        n = k + r;
    }

    // --- RUIDO ---
    string noisy = apply_noise(frame_bits, p);

    cout<<CYAN<<"\n-------------- RESUMEN EMISOR --------------\n"<<RESET;
    cout<<BOLD<<"Texto original: "<<RESET<<msg<<"\n";
    cout<<BOLD<<"ASCII->Bits:   "<<RESET<<group_every(bits,8)<<"\n";

    if(alg==1){
        cout<<BOLD<<"CRC32 (bin):  "<<RESET<<group_every(crcBits,4)<<"\n";
        cout<<BOLD<<"CRC32 (hex):  "<<RESET<<"0x"<<uppercase<<hex<<setw(8)<<setfill('0')<<crc_val
            <<dec<<nouppercase<<setfill(' ')<<"\n";
    }else{
        cout<<BOLD<<"Hamming k="<<RESET<<k<<", r="<<r<<", n="<<n<<", pad="<<pad<<"\n";
        cout<<BOLD<<"Bloques: "<<RESET<<group_every(frame_bits,n)<<"\n";
    }

    cout<<BOLD<<"Trama sin ruido: "<<RESET<<group_every(frame_bits,8)<<"\n";
    cout<<BOLD<<"Trama con ruido: "<<RESET<<group_every(noisy,8)<<"\n";
    cout<<BOLD<<"Destino socket:  "<<RESET<<host<<":"<<port<<"\n";
    cout<<CYAN<<"--------------------------------------------\n"<<RESET;

    ostringstream oss;
    oss<<"{\"msg_ascii_len\":"<<msg.size()
       <<",\"algo\":\""<<(alg==1?"CRC32":"HAMMING")<<"\""
       <<",\"frame_bits\":\""<<noisy<<"\"}\n";
    string line=oss.str();

    bool ok = send_line(host, port, line);
    if(ok) cout<<GREEN<<"✅ Trama enviada por socket.\n"<<RESET;
    else   cout<<RED<<"❌ Error enviando por socket.\n"<<RESET;
    return ok?0:1;
}
