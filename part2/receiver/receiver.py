import argparse
import json
import socket
from typing import Tuple, Optional, List

RESET   = "\033[0m"
BOLD    = "\033[1m"
GREEN   = "\033[32m"
RED     = "\033[31m"
CYAN    = "\033[36m"
YELLOW  = "\033[33m"
GRAY    = "\033[90m"

try:
    import colorama
    colorama.init()
except Exception:
    pass

def group_every(s: str, n: int) -> str:
    return " ".join(s[i:i+n] for i in range(0, len(s), n))

def ascii_from_bits(bits: str) -> str:
    out = []
    for i in range(0, len(bits), 8):
        byte = bits[i:i+8]
        if len(byte) < 8:
            break
        out.append(chr(int(byte, 2)))
    return "".join(out)

def hamming_distance(a: str, b: str) -> int:
    L = min(len(a), len(b))
    return sum(1 for i in range(L) if a[i] != b[i]) + abs(len(a) - len(b))

# ========== CRC32 ==========
def crc32_bits(bits: str) -> int:
    crc = 0xFFFFFFFF
    poly = 0x04C11DB7
    for c in bits:
        if c not in "01":
            raise ValueError("Bits inválidos")
        b = 1 if c == '1' else 0
        top = (crc >> 31) & 1
        fb = top ^ b
        crc = ((crc << 1) & 0xFFFFFFFF)
        if fb:
            crc ^= poly
    crc ^= 0xFFFFFFFF
    return crc

def to_bin32(x: int) -> str:
    return "".join('1' if (x >> i) & 1 else '0' for i in range(31, -1, -1))

# ========== Hamming==========
def is_pow2(x: int) -> bool:
    return x != 0 and (x & (x - 1)) == 0

def r_for_k(k: int) -> int:
    r = 0
    while (k + r + 1) > (1 << r):
        r += 1
    return r

def syndrome(block_bits: str) -> int:
    n = len(block_bits)
    # cuántas posiciones potencia de 2 <= n
    r = 0
    while (1 << r) <= n:
        r += 1
    s = 0
    # calcular paridades (even) incluyendo el bit de paridad
    for i in range(r):
        p = 1 << i
        parity = 0
        for k in range(1, n+1):
            if k & p:
                parity ^= (block_bits[k-1] == '1')
        if parity == 1:
            s |= p
    return s

def extract_data_from_block(block_bits: str) -> str:
    out = []
    for i in range(1, len(block_bits)+1):
        if not is_pow2(i):
            out.append(block_bits[i-1])
    return "".join(out)

def correct_block(block_bits: str) -> Tuple[str, bool, bool, Optional[int]]:
    s = syndrome(block_bits)
    if s == 0:
        return block_bits, False, False, None
    # Intento de corrección de 1 bit
    n = len(block_bits)
    if 1 <= s <= n:
        lst = list(block_bits)
        lst[s-1] = '0' if lst[s-1] == '1' else '1'
        fixed = "".join(lst)
        if syndrome(fixed) == 0:
            return fixed, True, False, s
    # no corregible confiablemente
    return block_bits, False, True, None

def infer_k(frame_len: int, msg_bits_len: int) -> Optional[Tuple[int, int, int, int, int]]:

    candidates = []
    for k in range(3, 65):
        r = r_for_k(k)
        n = k + r
        if frame_len % n != 0:
            continue
        blocks = frame_len // n
        total_data = blocks * k
        if total_data >= msg_bits_len:
            pad = total_data - msg_bits_len
            candidates.append((pad, -k, k, r, n, blocks))
    if not candidates:
        return None
    pad, _negk, k, r, n, blocks = min(candidates)
    return k, r, n, blocks, pad

# ========== Red ==========
def recv_line(conn: socket.socket) -> Optional[str]:

    buf = bytearray()
    while True:
        chunk = conn.recv(4096)
        if not chunk:
            break
        buf.extend(chunk)
        if b"\n" in chunk:
            break
    if not buf:
        return None
    return buf.decode("utf-8", errors="replace").split("\n", 1)[0]

def handle_crc(payload: dict) -> None:
    frame = payload.get("frame_bits", "")
    msg_ascii_len = int(payload.get("msg_ascii_len", 0))
    data_bits_len = msg_ascii_len * 8

    print(CYAN + "\n--------------- CRC32 ---------------" + RESET)
    if len(frame) < data_bits_len + 32:
        print(RED + "❌ Trama demasiado corta para datos + CRC32." + RESET)
        print(GRAY + f"len(frame)={len(frame)}, datos esperados={data_bits_len}, crc=32" + RESET)
        return

    data_bits = frame[:data_bits_len]
    recv_crc_bits = frame[data_bits_len:data_bits_len+32]

    calc_crc = crc32_bits(data_bits)
    calc_crc_bits = to_bin32(calc_crc)

    print(BOLD + "Datos (bits): " + RESET + group_every(data_bits, 8))
    print(BOLD + "CRC recibido : " + RESET + group_every(recv_crc_bits, 4))
    print(BOLD + "CRC calculado: " + RESET + group_every(calc_crc_bits, 4))

    if calc_crc_bits == recv_crc_bits:
        print(GREEN + "✅ Resultado: No se detectaron errores." + RESET)
        msg = ascii_from_bits(data_bits)
        print(BOLD + "Mensaje (ASCII): " + RESET + msg)
        print(GRAY + "Nota: CRC32 detecta todos los errores de 1 bit y todas las ráfagas de hasta 32 bits; no corrige." + RESET)
    else:
        dist = hamming_distance(calc_crc_bits, recv_crc_bits)
        print(RED + "❌ Resultado: Se detectaron errores. Verificación no coincide." + RESET)
        print(BOLD + "Distancia de Hamming (CRC): " + RESET + f"{dist} bit(s)")
        print(YELLOW + "Acción: descartar trama (CRC es de detección, no corrige)." + RESET)

def handle_hamming(payload: dict) -> None:
    frame = payload.get("frame_bits", "")
    msg_ascii_len = int(payload.get("msg_ascii_len", 0))
    msg_bits_len = msg_ascii_len * 8

    print(CYAN + "\n------------- HAMMING -------------" + RESET)

    k = payload.get("k", None)
    if isinstance(k, str) and k.isdigit():
        k = int(k)
    elif isinstance(k, int):
        pass
    else:
        k = None

    if k is None:
        inferred = infer_k(len(frame), msg_bits_len)
        if not inferred:
            print(RED + "❌ No se pudo inferir 'k'. Ajusta el sender para incluir 'k' en el JSON." + RESET)
            print(GRAY + f"len(frame)={len(frame)}, msg_bits_len={msg_bits_len}" + RESET)
            return
        k, r, n, blocks, pad = inferred
        print(GRAY + f"(Inferido) k={k}, r={r}, n={n}, bloques={blocks}, pad≈{pad}" + RESET)
    else:
        r = r_for_k(k)
        n = k + r
        if len(frame) % n != 0:
            print(YELLOW + f"⚠ La longitud de la trama ({len(frame)}) no es múltiplo de n={n}. Intentaré continuar." + RESET)
        blocks = len(frame) // n
        pad = max(0, blocks*k - msg_bits_len)

    corrected_count = 0
    uncorrectable_count = 0
    corrected_positions: List[Tuple[int,int]] = []

    corrected_frame_bits = []
    data_bits_all = []

    for b in range(blocks):
        blk = frame[b*n:(b+1)*n]
        if len(blk) < n:
            # bloque incompleto, ignora
            continue
        fixed, did_fix, uncorrectable, pos = correct_block(blk)
        corrected_frame_bits.append(fixed)
        if did_fix:
            corrected_count += 1
            corrected_positions.append((b, pos if pos is not None else -1))
        if uncorrectable:
            uncorrectable_count += 1
        data_bits_all.append(extract_data_from_block(fixed))

    corrected_frame = "".join(corrected_frame_bits)
    data_bits_full = "".join(data_bits_all)
    data_bits = data_bits_full[:msg_bits_len]

    print(BOLD + f"Bloques procesados: " + RESET + f"{blocks} (n={n}, k={k}, r={r})")
    print(BOLD + "Correcciones SEC: " + RESET + f"{corrected_count}")
    if corrected_positions:
        # muestra hasta los primeros 10
        shown = ", ".join(f"b{bi}@{pi}" for bi,pi in corrected_positions[:10])
        extra = "" if len(corrected_positions)<=10 else f" (+{len(corrected_positions)-10} más)"
        print(GRAY + f"Posiciones corregidas (bloque@bit): {shown}{extra}" + RESET)
    print(BOLD + "No corregibles : " + RESET + f"{uncorrectable_count}")

    if uncorrectable_count == 0:
        print(GREEN + "✅ Resultado: Mensaje recuperado (0 bloques no corregibles)." + RESET)
        print(BOLD + "Datos (bits): " + RESET + group_every(data_bits, 8))
        print(BOLD + "Mensaje (ASCII): " + RESET + ascii_from_bits(data_bits))
        print(GRAY + "Nota: Hamming SEC corrige 1 bit por bloque; 2+ errores en el mismo bloque pueden ser no corregibles." + RESET)
    else:
        print(RED + "❌ Resultado: Se detectaron errores no corregibles; descartar mensaje." + RESET)
        print(BOLD + "Datos (parciales, recortados): " + RESET + group_every(data_bits[:min(len(data_bits), 64)], 8) + (" ..." if len(data_bits)>64 else ""))
        print(GRAY + "Sugerencia: reduce la probabilidad de error o usa bloques con mayor redundancia." + RESET)

def handle_payload(payload: dict) -> None:
    algo = str(payload.get("algo", "")).upper().strip()
    print(CYAN + "--------------------------------------------" + RESET)
    print(BOLD + "Algoritmo: " + RESET + algo)
    if "p_error" in payload:
        print(BOLD + "p_error   : " + RESET + f"{payload.get('p_error')}")
    print(BOLD + "len(frame): " + RESET + f"{len(payload.get('frame_bits',''))} bits")
    print(CYAN + "--------------------------------------------" + RESET)

    if algo == "CRC32":
        handle_crc(payload)
    elif algo == "HAMMING":
        handle_hamming(payload)
    else:
        print(RED + "❌ Algoritmo no reconocido en payload." + RESET)

def serve(host: str, port: int) -> None:
    print(BOLD + CYAN + "=====================================" + RESET)
    print(BOLD + CYAN + " RECEPTOR por CAPAS (CRC32 / HAMMING)" + RESET)
    print(BOLD + CYAN + "=====================================" + RESET)
    print(GRAY + f"Servidor RECEPTOR escuchando en {host}:{port}" + RESET)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, port))
        s.listen(5)
        while True:
            conn, addr = s.accept()
            with conn:
                print(YELLOW + f"\n↘ Conexión de {addr[0]}:{addr[1]}" + RESET)
                line = recv_line(conn)
                if not line:
                    print(RED + "❌ Conexión vacía o cerrada sin datos." + RESET)
                    continue
                # intenta parsear JSON
                try:
                    payload = json.loads(line)
                except Exception as e:
                    print(RED + f"❌ JSON inválido: {e}" + RESET)
                    print(GRAY + f"Contenido recibido (trunc): {line[:200]}..." + RESET)
                    continue
                handle_payload(payload)

def main():
    parser = argparse.ArgumentParser(description="Receiver (server) CRC32/Hamming")
    parser.add_argument("--host", default="0.0.0.0", help="Host de escucha (default 0.0.0.0)")
    parser.add_argument("--port", type=int, default=50007, help="Puerto de escucha (default 50007)")
    args = parser.parse_args()
    serve(args.host, args.port)

if __name__ == "__main__":
    main()
