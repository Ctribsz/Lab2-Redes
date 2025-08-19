import argparse, csv, random, math, json, socket, sys, time
import matplotlib.pyplot as plt

RESET="\033[0m"; BOLD="\033[1m"; GREEN="\033[32m"; RED="\033[31m"; CYAN="\033[36m"; YELLOW="\033[33m"; GRAY="\033[90m"

def group_every(s: str, n: int) -> str:
    if n<=0: return s
    out=[]; 
    for i,ch in enumerate(s):
        if i and (i% n==0): out.append(' ')
        out.append(ch)
    return "".join(out)

# ===== Enlace: CRC32 =====
def crc32_bits(bits: str) -> int:
    crc = 0xFFFFFFFF
    poly = 0x04C11DB7
    for c in bits:
        b = 1 if c=='1' else 0
        top = (crc >> 31) & 1
        fb  = top ^ b
        crc = ((crc << 1) & 0xFFFFFFFF)
        if fb: crc ^= poly
    crc ^= 0xFFFFFFFF
    return crc

def bin32(x: int) -> str:
    return "".join('1' if (x>>i)&1 else '0' for i in range(31,-1,-1))

# ===== Enlace: Hamming SEC =====
def is_pow2(x: int) -> bool:
    return x!=0 and (x & (x-1))==0

def r_for_k(k: int) -> int:
    r=0
    while k + r + 1 > (1<<r): r+=1
    return r

def ham_enc_block(data: str) -> str:
    k=len(data); r=r_for_k(k); n=k+r
    code=[0]*(n+1)  # 1-indexed
    j=0
    for i in range(1,n+1):
        if not is_pow2(i):
            code[i]=1 if data[j]=='1' else 0; j+=1
    for i in range(r):
        p=1<<i; par=0
        for kpos in range(1,n+1):
            if kpos & p: par ^= code[kpos]
        code[p]=par
    return "".join('1' if x else '0' for x in code[1:])

def ham_enc_stream(bits: str, k: int):
    pad=(k - (len(bits)%k))%k
    bits = bits + "0"*pad
    r=r_for_k(k); out=[]
    for i in range(0,len(bits),k):
        out.append(ham_enc_block(bits[i:i+k]))
    return "".join(out), pad, r

def ham_syndrome(code: str) -> int:
    n=len(code); r=0
    while (1<<r)<=n: r+=1
    s=0
    for i in range(r):
        p=1<<i; par=0
        for kpos in range(1,n+1):
            if kpos & p: par ^= int(code[kpos-1])
        if par==1: s |= p
    return s

def ham_dec_stream(code: str, k: int, pad: int):
    r=r_for_k(k); n=k+r
    corrected=0; uncorrect=0; data=[]
    for i in range(0,len(code),n):
        cw=list(code[i:i+n])
        s=ham_syndrome("".join(cw))
        if s!=0:
            pos=s
            if 1<=pos<=n:
                cw[pos-1] = '0' if cw[pos-1]=='1' else '1'
                if ham_syndrome("".join(cw))==0:
                    corrected+=1
                else:
                    uncorrect+=1
            else:
                uncorrect+=1
        for j in range(1,n+1):
            if not is_pow2(j): data.append(cw[j-1])
    if pad: data=data[:-pad]
    return "".join(data), corrected, uncorrect

# ===== Ruido =====
def add_noise(bits: str, p: float) -> str:
    L=list(bits)
    for i,ch in enumerate(L):
        if random.random()<p: L[i]='0' if ch=='1' else '1'
    return "".join(L)

def hamming_distance(a: str, b: str) -> int:
    n=min(len(a),len(b))
    return sum(1 for i in range(n) if a[i]!=b[i])

# ===== Datos aleatorios =====
def rand_bits(n: int) -> str:
    import secrets
    return "".join('1' if (secrets.randbits(1)) else '0' for _ in range(n))

# ===== Experimentos offline =====
def run_offline(runs: int, sizes, ps, klist):
    rows=[]
    print(CYAN + BOLD + "\n=== Simulación OFFLINE ===" + RESET)
    for m in sizes:
        for p in ps:
            # CRC32
            ok=0
            for _ in range(runs):
                data = rand_bits(m)
                frame = data + bin32(crc32_bits(data))
                noisy = add_noise(frame, p)
                recv_data = noisy[:-32]
                ok += (bin32(crc32_bits(recv_data)) == noisy[-32:])
            rows.append({
                "algo":"CRC32","k":0,"m_bits":m,"p_error":p,"runs":runs,
                "ok_rate": ok/runs, "corrected_avg":0.0, "uncorrect_avg":0.0
            })
            print(f"CRC32 m={m:4d} p={p:0.4f} → ok={rows[-1]['ok_rate']:.4f}")

            # HAMMING
            for k in klist:
                ok=0; corrected=0; uncorrect=0
                for _ in range(runs):
                    data = rand_bits(m)
                    frame, pad, r = ham_enc_stream(data, k)
                    noisy = add_noise(frame, p)
                    dec, c, u = ham_dec_stream(noisy, k, pad)
                    ok += (u==0 and dec==data)
                    corrected += c; uncorrect += u
                rows.append({
                    "algo":"HAMMING","k":k,"m_bits":m,"p_error":p,"runs":runs,
                    "ok_rate": ok/runs,
                    "corrected_avg": corrected/runs,
                    "uncorrect_avg": uncorrect/runs
                })
                print(f"HAM(k={k:2d}) m={m:4d} p={p:0.4f} → ok={rows[-1]['ok_rate']:.4f}, "
                      f"corr_avg={rows[-1]['corrected_avg']:.3f}, uncor_avg={rows[-1]['uncorrect_avg']:.3f}")
    return rows

def plot_rows(rows, outpng="plots.png"):
    plt.figure()
    groups = {}
    for r in rows:
        key = (r["algo"], r["k"], r["m_bits"])
        groups.setdefault(key, []).append(r)
    # Una curva por (algo,k,m_bits)
    for (algo,k,m), arr in groups.items():
        arr = sorted(arr, key=lambda x: x["p_error"])
        xs=[x["p_error"] for x in arr]
        ys=[x["ok_rate"] for x in arr]
        label = f"{algo}" + (f"(k={k})" if algo=="HAMMING" else "") + f", m={m}"
        plt.plot(xs, ys, marker="o", label=label)
    plt.xlabel("Probabilidad de error por bit")
    plt.ylabel("Tasa de recepción correcta (ok_rate)")
    plt.title("Curvas de desempeño por tamaño (offline)")
    plt.grid(True)
    plt.legend()
    plt.savefig(outpng, dpi=160, bbox_inches="tight")

# ===== Proxy (canal con ruido) =====
def proxy_once(client_sock, addr, dest_host, dest_port, ber):
    try:
        buf=b""
        while True:
            chunk = client_sock.recv(4096)
            if not chunk: break
            buf += chunk
            if b"\n" in buf: break
        line = buf.decode("utf-8", errors="ignore").strip()
        if not line:
            return
        original_bits=None; noisy_bits=None
        try:
            pkt = json.loads(line)
            if isinstance(pkt, dict) and "frame_bits" in pkt:
                original_bits = pkt["frame_bits"]
                noisy_bits = add_noise(original_bits, ber)
                pkt["frame_bits"] = noisy_bits
                pkt["simulator_ber"] = ber
                out = json.dumps(pkt) + "\n"
            else:
                out = line + "\n"
        except Exception:
            # Si no es JSON válido, reenvía tal cual
            out = line + "\n"

        # Conectar a destino y enviar
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as ds:
            ds.connect((dest_host, dest_port))
            ds.sendall(out.encode("utf-8"))

        print(GRAY + f"↘ Recibido de {addr[0]}:{addr[1]}" + RESET)
        if original_bits is not None:
            hd = hamming_distance(original_bits, noisy_bits)
            flips_pct = (hd/len(original_bits))*100.0 if len(original_bits)>0 else 0.0
            print(CYAN + "Canal con ruido (proxy)" + RESET)
            print(f"BER objetivo: {ber:.4f} | flips aplicados: {hd} / {len(original_bits)} ({flips_pct:.2f}%)")
            print("→ reenviado al receptor.")
        else:
            print("Trama no-JSON o sin 'frame_bits' → reenviada sin cambios.")
        print()
    finally:
        client_sock.close()

def run_proxy(listen_host, listen_port, dest_host, dest_port, ber):
    print(BOLD+CYAN+"======================================"+RESET)
    print(BOLD+CYAN+"  SIMULADOR DE CANAL (Proxy con ruido)"+RESET)
    print(BOLD+CYAN+"======================================"+RESET)
    print(GRAY + f"Escuchando en {listen_host}:{listen_port} → destino {dest_host}:{dest_port}, BER={ber}" + RESET)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((listen_host, listen_port))
        s.listen(5)
        while True:
            conn, addr = s.accept()
            proxy_once(conn, addr, dest_host, dest_port, ber)

# ===== CLI =====
def parse_list_of_ints(text: str):
    return [int(x) for x in text.split(",") if x.strip()!=""]

def parse_list_of_floats(text: str):
    return [float(x) for x in text.split(",") if x.strip()!=""]

def main():
    parser = argparse.ArgumentParser(description="Simulador (offline/proxy) para CRC32 y Hamming SEC")
    sub = parser.add_subparsers(dest="mode", required=True)

    # offline
    p_off = sub.add_parser("offline", help="Correr simulaciones offline y graficar resultados")
    p_off.add_argument("--runs", type=int, default=10000, help="iteraciones por punto")
    p_off.add_argument("--sizes", type=str, default="64,256,1024", help="tamaños m en bits, separados por coma")
    p_off.add_argument("--ps", type=str, default="0.0,0.001,0.005,0.01,0.02,0.05", help="probabilidades de error por bit, separadas por coma")
    p_off.add_argument("--klist", type=str, default="11", help="valores k para Hamming (ej. 4,8,11)")
    p_off.add_argument("--outcsv", type=str, default="results.csv")
    p_off.add_argument("--outpng", type=str, default="plots.png")
    p_off.add_argument("--seed", type=int, default=1234)

    # proxy
    p_prox = sub.add_parser("proxy", help="Actuar como canal con ruido entre sender y receiver")
    p_prox.add_argument("--listen", type=str, default="0.0.0.0", help="IP de escucha")
    p_prox.add_argument("--lport", type=int, default=50006, help="Puerto de escucha")
    p_prox.add_argument("--dest", type=str, default="127.0.0.1", help="IP destino (receiver)")
    p_prox.add_argument("--dport", type=int, default=50007, help="Puerto destino (receiver)")
    p_prox.add_argument("--ber", type=float, default=0.01, help="probabilidad de flip por bit")

    args = parser.parse_args()

    if args.mode == "offline":
        random.seed(args.seed)
        sizes = parse_list_of_ints(args.sizes)
        ps    = parse_list_of_floats(args.ps)
        klist = parse_list_of_ints(args.klist)

        print(BOLD+CYAN+"======================================"+RESET)
        print(BOLD+CYAN+"  SIMULACIONES OFFLINE (CRC32/Hamming)"+RESET)
        print(BOLD+CYAN+"======================================"+RESET)
        print(GRAY+f"runs={args.runs}, sizes={sizes}, ps={ps}, klist={klist}, seed={args.seed}"+RESET)

        rows = run_offline(args.runs, sizes, ps, klist)

        if rows:
            with open(args.outcsv,"w",newline="") as f:
                w=csv.DictWriter(f, fieldnames=list(rows[0].keys()))
                w.writeheader(); w.writerows(rows)
            plot_rows(rows, args.outpng)
            print(GREEN+f"\nListo → {args.outcsv} y {args.outpng}"+RESET)
        else:
            print(RED+"No se generaron filas de resultados."+RESET)

    elif args.mode == "proxy":
        if not (0.0 <= args.ber <= 1.0):
            print(RED+"BER invalido. Debe estar en [0,1]."+RESET); sys.exit(1)
        run_proxy(args.listen, args.lport, args.dest, args.dport, args.ber)

if __name__ == "__main__":
    main()
