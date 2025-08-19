# Laboratorio 2 - Capa Física y Enlace
Universidad del Valle de Guatemala  
Curso: Redes de Computadoras  

## Descripción
Este laboratorio consiste en la implementación de un sistema de comunicación simple en dos fases:  
1. Transmisión directa entre emisor y receptor.  
2. Transmisión con un canal ruidoso simulado, aplicando algoritmos de detección y corrección de errores.

## Estructura del proyecto
```
LABORATORIO2/
├── part1/
│   ├── sender.cpp
│   ├── receiver.cpp
│   └── Makefile
├── part2/
│   ├── sender/
│   │   └── sender.cpp
│   ├── receiver/
│   │   └── receiver.cpp
│   ├── tools/
│   │   └── simulator.py
│   └── Makefile
```

## Algoritmos implementados
- **CRC32**: Detección de errores mediante polinomio de 32 bits.
- **Hamming (7,4)**: Corrección de un solo error por bloque de 4 bits.

## Ejecución rápida
- Parte 1: compilar y ejecutar `sender` y `receiver` directamente.  
- Parte 2: ejecutar el simulador de canal, luego el receptor y por último el emisor.

## Conclusiones
- La transmisión sin canal ruidoso siempre es correcta.  
- Con canal ruidoso, el Hamming permite corregir errores simples, mientras que CRC32 solo detecta.  
- Al aumentar la probabilidad de error, el rendimiento del sistema disminuye.  
