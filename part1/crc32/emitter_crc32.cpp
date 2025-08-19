#include <iostream>
#include <string>
#include <algorithm>
#include <stdexcept>
#include <cstdint>
#include <iomanip>

using namespace std;

#define RESET   "\033[0m"
#define BOLD    "\033[1m"
#define GREEN   "\033[32m"
#define RED     "\033[31m"
#define CYAN    "\033[36m"
#define YELLOW  "\033[33m"
#define GRAY    "\033[90m"

// -------- Utilidades de formato --------
static string group_every(const string& s, int n) {
    string out; out.reserve(s.size() + s.size()/n);
    for (size_t i=0;i<s.size();++i){
        if (i && (i% n==0)) out.push_back(' ');
        out.push_back(s[i]);
    }
    return out;
}

// CRC-32
static uint32_t crc32_bits(const string& bits){
    uint32_t crc = 0xFFFFFFFFu;
    const uint32_t poly = 0x04C11DB7u;
    for(char c : bits){
        if(c!='0' && c!='1') throw runtime_error("Solo bits 0/1");
        uint32_t bit = (c=='1') ? 1u : 0u;
        uint32_t top = (crc >> 31) & 1u;
        uint32_t fb  = top ^ bit;        
        crc = (crc << 1);
        if(fb) crc ^= poly;
    }
    crc ^= 0xFFFFFFFFu;
    return crc;
}

static string to_bin32(uint32_t x){
    string s(32,'0');
    for(int i=31;i>=0;--i){
        s[31-i] = ((x>>i)&1u) ? '1':'0'; // MSB primero
    }
    return s;
}

int main(){
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    cout << BOLD << CYAN
         << "=============================\n"
         << "   EMISOR CRC-32 (IEEE802.3)\n"
         << "=============================\n" << RESET;

    cout << GRAY
         << "Parametrizacion: poly=0x04C11DB7, init=0xFFFFFFFF, xorout=0xFFFFFFFF, reflejado=No\n"
         << "Entrada esperada: cadena binaria (solo '0' y '1').\n" << RESET;

    string msg;
    cout << YELLOW << "\nIngrese mensaje binario (solo 0/1): " << RESET << flush;
    if(!(cin >> msg)){
        cerr << RED << "❌ No se pudo leer la entrada.\n" << RESET;
        return 1;
    }
    if(msg.empty() || any_of(msg.begin(), msg.end(), [](char c){return c!='0'&&c!='1';})){
        cerr << RED << "❌ Entrada invalida. Debe contener solo 0 y 1.\n" << RESET;
        return 1;
    }

    // ---- Calculo CRC ----
    uint32_t crc = crc32_bits(msg);
    string crcBits = to_bin32(crc);

    const string frame = msg + crcBits;
    const double overhead_pct = 100.0 * 32.0 / frame.size();

    cout << "\n" << CYAN << "----------------------------------" << RESET << "\n";
    cout << GREEN << "✅ CRC32 generado correctamente" << RESET << "\n";
    cout << BOLD  << "Longitud mensaje: " << RESET << msg.size() << " bits\n";
    cout << BOLD  << "CRC32 (binario):  " << RESET << group_every(crcBits,4) << "\n";
    cout << BOLD  << "CRC32 (hex):      " << RESET
         << "0x" << uppercase << hex << setw(8) << setfill('0') << crc
         << nouppercase << dec << setfill(' ') << "\n";

    cout << BOLD  << "Trama (msg||CRC) [copiar/pegar]: " << RESET << frame << "\n";
    cout << BOLD  << "Overhead CRC:     " << RESET << "32 bits ("
         << fixed << setprecision(1) << overhead_pct << "% de la trama)\n";
    cout << CYAN << "----------------------------------" << RESET << "\n";
    cout << GRAY << "Sugerencia: copie la linea \"Trama \" y péguela en el RECEPTOR.\n" << RESET;
    return 0;
}
