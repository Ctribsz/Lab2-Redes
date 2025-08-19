// hamming/emitter_hamming.cpp
#include <iostream>
#include <string>
#include <vector>
#include <algorithm>
#include <cstdint>
#include <iomanip>

using namespace std;

// ===== Colores ANSI =====
#define RESET   "\033[0m"
#define BOLD    "\033[1m"
#define GREEN   "\033[32m"
#define RED     "\033[31m"
#define CYAN    "\033[36m"
#define YELLOW  "\033[33m"
#define GRAY    "\033[90m"

// -------- Utilidades --------
static bool isBinary(const string& s){
    return !s.empty() && all_of(s.begin(), s.end(), [](char c){ return c=='0'||c=='1'; });
}
static bool isPowerOfTwo(int x){ return x && ((x & (x-1))==0); }
static int calc_r_for_m(int m){
    int r = 0;
    while ((m + r + 1) > (1 << r)) r++; // 2^r >= m + r + 1
    return r;
}
static string group_every(const string& s, int n) {
    string out; out.reserve(s.size() + s.size()/n);
    for (size_t i=0;i<s.size();++i){
        if (i && (i % n == 0)) out.push_back(' ');
        out.push_back(s[i]);
    }
    return out;
}

// -------- Hamming (SEC, paridad par) --------
static string hammingEncode(const string& msgBits){
    const int m = (int)msgBits.size();
    const int r = calc_r_for_m(m);
    const int n = m + r;

    vector<int> code(n+1, 0); // 1-indexed
    // Colocar datos en posiciones != potencias de 2
    for(int i=1, j=0; i<=n; ++i){
        if(!isPowerOfTwo(i)){
            code[i] = (msgBits[j++]=='1');
        }
    }
    // Paridades (even parity)
    for(int i=0; i<r; ++i){
        int p = 1 << i; // posición de paridad
        int parity = 0;
        for(int k=1; k<=n; ++k){
            if(k & p) parity ^= code[k];
        }
        code[p] = parity; // paridad para que el total quede par
    }
    // Construir string
    string out; out.reserve(n);
    for(int i=1; i<=n; ++i) out.push_back(code[i] ? '1' : '0');
    return out;
}

int main(){
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    cout << BOLD << CYAN
         << "=============================\n"
         << "   EMISOR HAMMING (SEC)\n"
         << "=============================\n" << RESET;

    cout << GRAY
         << "Codigo Hamming (SEC: Single-Error-Correcting), paridad par.\n"
         << "Corrige 1 bit y detecta 2 bits de error sin correccion.\n"
         << "Entrada esperada: cadena binaria (solo '0' y '1').\n" << RESET;
         
    string msg;
    cout << YELLOW << "\nIngrese mensaje binario (solo 0/1): " << RESET << flush;
    if(!(cin >> msg)){
        cerr << RED << "❌ No se pudo leer la entrada.\n" << RESET;
        return 1;
    }
    if(!isBinary(msg)){
        cerr << RED << "❌ Entrada invalida. Debe contener solo 0 y 1.\n" << RESET;
        return 1;
    }

    // ---- Calculo Hamming ----
    const int m = (int)msg.size();
    const int r = calc_r_for_m(m);
    const string code = hammingEncode(msg);
    const int n = (int)code.size();
    const double overhead_pct = (100.0 * r) / n;

    cout << "\n" << CYAN << "----------------------------------" << RESET << "\n";
    cout << GREEN << "✅ Trama Hamming generada correctamente" << RESET << "\n";
    cout << BOLD  << "Longitud mensaje (m): " << RESET << m << " bits\n";
    cout << BOLD  << "Bits de paridad (r):  " << RESET << r << " (posiciones ";
    {
        bool first=true;
        for(int i=0;i<r;++i){
            int p = 1<<i;
            if(!first) cout << ", ";
            cout << p;
            first=false;
        }
        cout << ")\n";
    }
    cout << BOLD  << "Longitud total (n):   " << RESET << n << " bits\n";
    cout << BOLD  << "Overhead Hamming:     " << RESET << r << " bits ("
         << fixed << setprecision(1) << overhead_pct << "% de la trama)\n";
    cout << BOLD  << "Trama (copiar/pegar): " << RESET << code << "\n";

    cout << CYAN << "----------------------------------" << RESET << "\n";
    cout << GRAY << "Sugerencia: copie la linea \"Trama \" y péguela en el RECEPTOR.\n" << RESET;
    return 0;
}
