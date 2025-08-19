# ===== Colores ANSI =====
RESET   = "\033[0m"
BOLD    = "\033[1m"
GREEN   = "\033[32m"
RED     = "\033[31m"
CYAN    = "\033[36m"
YELLOW  = "\033[33m"
GRAY    = "\033[90m"

def group_every(s: str, n: int) -> str:
    out = []
    for i, ch in enumerate(s):
        if i and (i % n == 0):
            out.append(' ')
        out.append(ch)
    return ''.join(out)

# CRC-32
def crc32_bits(bits: str) -> int:
    crc = 0xFFFFFFFF
    poly = 0x04C11DB7
    for c in bits:
        if c not in '01':
            raise ValueError("Solo bits 0/1")
        b = 1 if c == '1' else 0
        top = (crc >> 31) & 1
        fb = top ^ b
        crc = ((crc << 1) & 0xFFFFFFFF)
        if fb:
            crc ^= poly
    crc ^= 0xFFFFFFFF
    return crc

def to_bin32(x: int) -> str:
    return "".join('1' if (x >> i) & 1 else '0' for i in range(31, -1, -1))  # MSB primero

def hamming_distance(a: str, b: str) -> int:
    return sum(da != db for da, db in zip(a, b))

def main():
    print(f"{BOLD}{CYAN}=============================")
    print("   RECEPTOR CRC-32 (IEEE802.3)")
    print("=============================" + RESET)
    print(GRAY + "Parametrizacion: poly=0x04C11DB7, init=0xFFFFFFFF, xorout=0xFFFFFFFF, reflejado=No" + RESET)

    frame = input(f"\n{YELLOW}Ingrese trama (mensaje||CRC32, 32 bits al final): {RESET}").strip()

    # Validacion basica
    if (not frame) or any(c not in '01' for c in frame) or len(frame) < 33:
        print(f"{RED}❌ Entrada invalida. Debe ser una cadena binaria con al menos 33 bits (msg + 32 de CRC).{RESET}")
        return

    msg = frame[:-32]
    crc_recv_str = frame[-32:]
    crc_calc = crc32_bits(msg)
    crc_calc_str = to_bin32(crc_calc)

    print(CYAN + "\n----------------------------------" + RESET)
    print(f"{BOLD}Longitud mensaje:{RESET} {len(msg)} bits")
    print(f"{BOLD}CRC recibido    :{RESET} {group_every(crc_recv_str,4)}")
    print(f"{BOLD}CRC calculado   :{RESET} {group_every(crc_calc_str,4)}")

    if crc_calc_str == crc_recv_str:
        print(f"\n{GREEN}✅ Resultado: No se detectaron errores.{RESET}")
        print(f"{BOLD}Mensaje original:{RESET} {group_every(msg,8)}")
        print(GRAY + "Nota: CRC32 detecta todos los errores de 1 bit y todas las rafagas de hasta 32 bits; no corrige errores." + RESET)
    else:
        dist = hamming_distance(crc_calc_str, crc_recv_str)
        print(f"\n{RED}❌ Resultado: Se detectaron errores. La verificacion no coincide.{RESET}")
        print(f"{BOLD}Distancia de Hamming (CRC):{RESET} {dist} bit(s) diferentes")
        print(f"{BOLD}Accion recomendada:{RESET} descartar la trama.")
        print(GRAY + "Recordatorio: CRC32 es un algoritmo de deteccion (no corrige). "
              "Una coincidencia falsa es extremadamente improbable para cambios aleatorios." + RESET)

    print(CYAN + "----------------------------------" + RESET)

if __name__ == "__main__":
    main()
