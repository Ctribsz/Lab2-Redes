# 📡 Laboratorio 2 — Parte 1
### Esquemas de **Detección y Corrección de Errores** (CRC32 & Hamming)

> Implementación minimal y **visual** de emisor/receptor para CRC‑32 (detección) y Hamming SEC (corrección 1‑bit).  
> Incluye instrucciones de **compilación**, **ejecución** y **pruebas**.

---

## 📂 Estructura

```
part1/
├── crc32/
│   ├── emitter_crc32.cpp    # Emisor (C++): genera CRC32 y trama (msg||CRC)
│   └── receiver_crc32.py    # Receptor (Python): verifica CRC32 y reporta resultado
│
└── hamming/
    ├── emitter_hamming.cpp  # Emisor (C++): codifica Hamming (SEC)
    └── receiver_hamming.py  # Receptor (Python): detecta/corrige y extrae mensaje
```

---

## ⚙️ Requisitos

- **C++17** (g++ recomendado)  
- **Python 3.8+**
- Terminal con soporte de **colores ANSI** (WSL/Ubuntu, macOS Terminal, Windows Terminal o PowerShell moderno).

> En Ubuntu/WSL:
```bash
sudo apt update
sudo apt install -y build-essential python3
```

---

## 🚀 CRC‑32 (IEEE 802.3)

### 1) Compilar emisor
```bash
g++ -std=c++17 -O2 -Wall -Wextra -o emitter_crc32 part1/crc32/emitter_crc32.cpp
```

### 2) Ejecutar emisor
```bash
./emitter_crc32
```
- Ingresa una **cadena binaria** (solo `0/1`).
- El programa muestra: **CRC32 en binario y hex**, y la **trama** `mensaje||CRC32` **sin espacios** (lista para copiar).

> Ejemplo:
```
Ingrese mensaje binario (solo 0/1): 101001
✅ CRC32 generado correctamente
CRC32 (hex): 0xD38A4BC1
Trama (msg||CRC): 10100111010011100010100100101111000001
```

### 3) Ejecutar receptor
```bash
python3 part1/crc32/receiver_crc32.py
```
- Pega la **trama completa** que te dio el emisor (sin espacios).
- Verás:
  - **Longitud** del mensaje.
  - **CRC recibido** vs **CRC calculado**.
  - **Resultado** (OK / error detectado).
  - Si hay error, imprime la **distancia de Hamming entre CRCs** y una **recomendación**.

---

## 🛠️ Hamming (SEC — Single Error Correcting)

### 1) Compilar emisor
```bash
g++ -std=c++17 -O2 -Wall -Wextra -o emitter_hamming part1/hamming/emitter_hamming.cpp
```

### 2) Ejecutar emisor
```bash
./emitter_hamming
```
- Ingresa una **cadena binaria** (solo `0/1`).  
- El programa calcula **r**, **n = m + r**, muestra posiciones de paridad y la **trama codificada** para copiar.

### 3) Ejecutar receptor
```bash
python3 part1/hamming/receiver_hamming.py
```
- Pega la **trama** exacta.  
- El receptor:
  - Calcula el **síndrome** y, si procede, **corrige 1 bit** (SEC).
  - Reporta si el bit corregido era **dato** o **paridad**.
  - Si hay **≥2 errores en el mismo bloque**, avisa como **no corregible**.

---

## 🧪 Escenarios de prueba (requeridos)

Usa **los mismos mensajes** para ambos algoritmos.

### A) Sin errores (3 casos, longitudes distintas)
1. Ejecuta emisor → copia **trama** tal cual.
2. Pégala en el receptor → **debe decir “No se detectaron errores”** y mostrar mensaje original.

### B) Un error (3 casos, longitudes distintas)
1. Emisor → copia **trama**.
2. **Cambia 1 bit** a mano en cualquier posición.
3. Receptor:
   - **CRC32** → **detecta** error (no corrige).
   - **Hamming** → **corrige** 1 bit, indica **posición** y muestra mensaje.

### C) Dos o más errores (3 casos, longitudes distintas)
1. Emisor → copia **trama**.
2. **Cambia 2+ bits** a mano.
3. Receptor:
   - **CRC32** → **detecta** error (descartar).
   - **Hamming (SEC)** → normalmente **no corregible** (puede detectar).

### D) ¿Se puede no detectar el error?
- **CRC32**: extremadamente improbable para cambios aleatorios; existen **patrones patológicos** que preservan el CRC, pero son difíciles de conseguir manualmente.
- **Hamming SEC**: **no detecta** algunos patrones de **doble error** como “1 en dato + 1 en paridad” que cancelen el síndrome (dependiendo de posiciones).

> Documenta (capturas) y explica por qué ocurre.

---

## ✅ Consejos

- **No agregues espacios** cuando pegues una trama al receptor (ambos receptores aceptan solo `0/1` continuos).
- Usa mensajes de distintas longitudes para cumplir la rúbrica.
- Para Hamming, recuerda: **corrige 1 bit por bloque** (SEC), **detecta** 2 bits en el mismo bloque (sin corrección).

---

## 💡 Troubleshooting

- Si en Windows los colores no se ven, usa **Windows Terminal** o corre bajo **WSL**.
- Si el emisor no imprime el prompt inmediatamente, agrega `<< flush` (ya incluido en el código provisto).
- Verifica que no queden **saltos de línea extra** al pegar tramas.

---

## 📜 Créditos

Implementación y guía de uso desarrolladas para el **Laboratorio de Redes — Parte 1**.  
Autoría del equipo, con consola **estilizada** para una UX clara.
