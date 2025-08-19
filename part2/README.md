# Parte 2 — Arquitectura por capas con sockets (CRC32 / Hamming)  

Esta parte implementa una mini‑pila de **Aplicación → Presentación → Enlace → Transmisión**, con:
- **Emisor (sender)** en C++17 (interactivo, con interfaz en consola).
- **Receptor (receiver)** en Python 3 (servidor TCP que valida/decodifica).
- **Simulador** de canal con ruido y **motor de simulaciones offline** en Python.

> **Nota:** `server.py` ya **no se usa**. El servidor es `receiver.py`.

---

## 📁 Estructura de carpetas

```
part2/
├─ sender/
│  ├─ sender.cpp     # Emisor C++17 (interactivo)
│  └─ sender         # (binario generado tras compilar)
├─ receiver/
│  └─ receiver.py    # Receptor/servidor TCP (CRC32/Hamming)
└─ tools/
   └─ simulator.py   # Simulaciones offline y proxy (canal con ruido)
```

---

## 🧰 Requisitos

- **Windows + WSL2** (emisor desde WSL y receptor en Windows) o ambos en Windows.
- **g++** con C++17 (ej. en WSL: `sudo apt install g++`).
- **Python 3.10+** en Windows (o donde ejecutes el receptor y el simulador).
- Para gráficas (modo *offline*): `matplotlib` + `numpy`  
  *Combinación estable recomendada*:
  ```bash
  pip install "numpy==1.26.4" "matplotlib==3.8.4"
  ```

---

## ⚙️ Compilar el **sender** (C++)

Desde la raíz del proyecto (o dentro de `part2/sender`):

```bash
g++ -std=c++17 -O2 -Wall -Wextra -o part2/sender/sender part2/sender/sender.cpp
# o
cd part2/sender
g++ -std=c++17 -O2 -Wall -Wextra -o sender sender.cpp
```

El binario queda como `part2/sender/sender` (WSL/Linux) o `sender.exe` si compilas en Windows.

---

## ▶️ Ejecutar el **receiver** (servidor TCP)

En **Windows PowerShell** (o una consola con Python):

```powershell
python part2/receiver/receiver.py --host 0.0.0.0 --port 50007
```

Verás algo como:

```
=====================================
 RECEPTOR por CAPAS (CRC32 / HAMMING)
=====================================
Servidor RECEPTOR escuchando en 0.0.0.0:50007
```

> El receptor **siempre debe estar ejecutándose** antes de enviar.

---

## 📤 Ejecutar el **sender** (cliente interactivo)

En **WSL**:

```bash
./part2/sender/sender
```

Sigue los **prompts**:

1) **Mensaje a enviar (texto ASCII)** — escribe tu texto (ej. `Hola UVG`).  
2) **Algoritmo** — `1=CRC32`, `2=HAMMING`.  
   - Si eliges Hamming, se pedirá **k** (bits de datos por bloque). Ejemplos útiles: `4`, `8`, `11`.  
3) **Probabilidad de error por bit** — ruido local que se aplica en el emisor (ej. `0.00`, `0.01`).  
4) **IP receptor / Puerto** — IP y puerto del servidor `receiver.py`.

La consola mostrará un **resumen** (bits ASCII, CRC/Hamming, tramas con/sin ruido) y enviará un **JSON** por socket que el receptor interpreta.

### 📡 ¿Qué IP debo usar?
- Si el **receiver** corre en **Windows** y el **sender** en **WSL**, usa la IP de Windows vista desde `ipconfig`.  
  Ejemplos reales que suelen funcionar:
  - IP del adaptador LAN/Wi‑Fi (ej. `10.x.x.x`).
  - IP de **vEthernet (WSL)** (ej. `172.28.80.1`).  
- **No uses `0.0.0.0`** como destino.  
- `127.0.0.1` **puede no funcionar** entre WSL2 y Windows por NAT; por eso es más seguro usar la IP de `ipconfig`.

Para ver tu IP en Windows:
```powershell
ipconfig
```
Busca **“Dirección IPv4”** en el adaptador activo (o en *vEthernet (WSL)*).

---

## 🌪️ Simulador de canal con ruido (proxy)

Permite interponer un “canal” entre el emisor y el receptor para inyectar errores con una **BER** (bit error rate) controlada.

### 1) Inicia el receptor (puerto real)
```powershell
python part2/receiver/receiver.py --host 0.0.0.0 --port 50007
```

### 2) Inicia el proxy (escucha en 50006 y reenvía a 50007 con BER=0.02)
```powershell
python part2/tools/simulator.py proxy --listen 0.0.0.0 --lport 50006 --dest 127.0.0.1 --dport 50007 --ber 0.02
```

Verás:
```
======================================
  SIMULADOR DE CANAL (Proxy con ruido)
======================================
Escuchando en 0.0.0.0:50006 → destino 127.0.0.1:50007, BER=0.02
```

### 3) En el sender, usa el **puerto del proxy (50006)** y la IP del host Windows
```
IP receptor: <IPv4 de Windows via ipconfig>
Puerto receptor: 50006
```

El proxy imprimirá cuántos bits invirtió y reenviará al receptor.

---

## 📊 Simulaciones **offline** (sin sockets)

Genera estadísticas y **gráficas** de desempeño variando tamaño, BER, y `k` de Hamming.

```powershell
python part2/tools/simulator.py offline `
  --runs 10000 `
  --sizes "64,256,1024" `
  --ps "0.0,0.001,0.005,0.01,0.02,0.05" `
  --klist "4,8,11" `
  --outcsv results.csv `
  --outpng plots.png
```

- Salida: `results.csv` (tabla) y `plots.png` (curvas ok_rate vs p_error).  
- Requiere `matplotlib` y `numpy` (ver **Requisitos**).

---

## 🧪 Qué hace cada capa

- **Aplicación**: pide el mensaje y muestra el resultado final (o error).  
- **Presentación**: codifica/decodifica ASCII ↔ bits (8b por carácter).  
- **Enlace**:  
  - **CRC32**: agrega 32 bits de verificación; *detecta* pero no corrige.  
  - **Hamming SEC (k,r,n)**: divide en bloques; *corrige 1 bit por bloque* y *detecta 2+*.  
- **Transmisión**: envía/recibe por sockets TCP.  
- **Ruido**: opcional, mediante el **proxy** (o el parámetro `p` del sender).

---

## 🧯 Troubleshooting

- **`Connection refused`**: receptor no está corriendo, IP/puerto equivocados o firewall.  
- **No llega al receptor**: prueba con la IP real de Windows (`ipconfig`).  
- **Colores raros**: usa una terminal que soporte ANSI (Windows Terminal / PowerShell).  
- **Puertos ocupados**: cambia `--port` del receptor o `--lport/--dport` del proxy.  
- **Gráficas fallan**: verifica versiones: `numpy==1.26.4`, `matplotlib==3.8.4`.

---

## 🧠 Consejos para el informe

- Compara **tasa de recepción correcta** (ok_rate) entre CRC32 y Hamming según BER.  
- Muestra impacto de **k** (redundancia) en Hamming.  
- Discute cuándo conviene *detección* (CRC) vs *corrección* (Hamming).

---

## 📌 Resumen rápido de ejecución

1. **Receiver** en Windows:
   ```powershell
   python part2/receiver/receiver.py --host 0.0.0.0 --port 50007
   ```
2. (Opcional) **Proxy** con BER:
   ```powershell
   python part2/tools/simulator.py proxy --listen 0.0.0.0 --lport 50006 --dest 127.0.0.1 --dport 50007 --ber 0.02
   ```
3. **Sender** en WSL:
   ```bash
   ./part2/sender/sender
   # IP = IPv4 de Windows (ipconfig)
   # Puerto = 50007 (directo) o 50006 (pasando por el proxy)
   ```
