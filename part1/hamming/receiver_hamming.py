# ===== Colores ANSI =====
RESET   = "\033[0m"
BOLD    = "\033[1m"
GREEN   = "\033[32m"
RED     = "\033[31m"
CYAN    = "\033[36m"
YELLOW  = "\033[33m"
GRAY    = "\033[90m"

def is_power_of_two(x: int) -> bool:
    return x != 0 and (x & (x - 1)) == 0

def group_every(s: str, n: int) -> str:
    out = []
    for i, ch in enumerate(s):
        if i and (i % n == 0):
            out.append(' ')
        out.append(ch)
    return "".join(out)

def calc_r_for_n(n: int) -> int:
    r = 0
    while (1 << r) <= n:
        r += 1
    return r

def syndrome(bits: str) -> int:
    n = len(bits)
    r = calc_r_for_n(n)
    s = 0
    for i in range(r):
        p = 1 << i
        parity = 0
        for k in range(1, n + 1):
            if k & p:
                parity ^= int(bits[k - 1])
        if parity == 1:
            s |= p
    return s

def extract_message(bits: str) -> str:
    # quitar posiciones potencia de 2
    return "".join(bits[i-1] for i in range(1, len(bits)+1) if not is_power_of_two(i))

def main():
    print(f"{BOLD}{CYAN}=============================")
    print("   RECEPTOR HAMMING (SEC)")
    print("=============================" + RESET)

    print(GRAY + "Codigo Hamming (SEC: corrige 1 bit, detecta 2 sin correccion). Paridad par." + RESET)

    frame = input(f"{YELLOW}\nIngrese trama Hamming (emisor->receptor, sin espacios): {RESET}").strip()
    if (not frame) or any(c not in "01" for c in frame):
        print(f"{RED}❌ Entrada invalida. Use solo '0' y '1'.{RESET}")
        return

    n = len(frame)
    r = calc_r_for_n(n)
    m = n - r

    print(CYAN + "\n----------------------------------" + RESET)
    print(f"{BOLD}Longitud total (n):{RESET} {n} bits   "
          f"{BOLD}Paridades (r):{RESET} {r}   "
          f"{BOLD}Mensaje (m):{RESET} {m} bits")
    print(f"{BOLD}Trama (agrupada 8b):{RESET} {group_every(frame,8)}")

    s = syndrome(frame)
    s_bin = format(s, f"0{r}b")  # r bits

    if s == 0:
        print(f"\n{GREEN}✅ Resultado: No se detectaron errores.{RESET}")
        print(f"{BOLD}Mensaje original:{RESET} {group_every(extract_message(frame),8)}")
        print(GRAY + "Nota: Hamming (SEC) corrige 1 bit, detecta >=2 (sin correccion)." + RESET)
        print(CYAN + "----------------------------------" + RESET)
        return

    # Intentar correccion 1-bit
    print(f"\n{RED}❌ Verificacion fallida.{RESET}")
    print(f"{BOLD}Sindrome (bin):{RESET} {s_bin}  {BOLD}Posicion indicada:{RESET} {s} (1-indexada)")
    if 1 <= s <= n:
        flipped = list(frame)
        flipped[s-1] = '0' if flipped[s-1] == '1' else '1'
        s2 = syndrome("".join(flipped))
        if s2 == 0:
            kind = "paridad" if is_power_of_two(s) else "dato"
            print(f"{GREEN}✅ Correccion aplicada:{RESET} se invirtio el bit en la posicion {s} ({kind}).")
            print(f"{BOLD}Trama corregida:{RESET} {group_every(''.join(flipped),8)}")
            print(f"{BOLD}Mensaje corregido:{RESET} {group_every(extract_message(''.join(flipped)),8)}")
            print(GRAY + "Distancia de Hamming respecto a la trama recibida: 1 bit." + RESET)
            print(CYAN + "----------------------------------" + RESET)
            return
        
    print(f"{RED}⚠️  Se detectaron 2 o mas errores (no corregible como 1-bit).{RESET}")
    print("Accion recomendada: descartar la trama y solicitar retransmision.")
    print(GRAY + "Tip: si necesitas deteccion garantizada de dobles errores + correccion de simples, usa Hamming extendido (SECDED)." + RESET)
    print(CYAN + "----------------------------------" + RESET)

if __name__ == "__main__":
    main()
