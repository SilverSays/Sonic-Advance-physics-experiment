# Fase 0 — Medición base del sistema viejo

**Fecha:** 2026-11-13 · **Commits:** `bfb5a04` (medición), `1ce3035` (resultados)

## Qué se hizo

- `Sonic/perf.py`: clase `StepProfiler`. Mide cada frame el costo de `SonicPhysics.step()`
  y lo separa en "motor" (la llamada a `move_and_slide`) y "python" (todo lo demás).
  Acumula 120 frames e imprime una sola línea, porque un `print` por frame costaría más
  que lo que se mide.
- Al arrancar calibra cuánto cuesta el propio reloj (`OS.get_ticks_usec()`).
- `personaje.py`: exports `perf_enabled` y `perf_window`, y la medición alrededor de `step()`.

## Por qué antes de reescribir

Al reemplazar el módulo de física, la referencia del sistema viejo se pierde. Sin ella,
"el sistema nuevo es más rápido" no se puede afirmar ni negar.

## Resultado

Rutina libre de unos 30 s (correr, frenar, saltar, anillos). El reloj cuesta 0.29 µs por par.

| | Por ventana de 120 frames | Máximo de un frame |
|---|---|---|
| Total `step()` | 292–590 µs | 1581 µs |
| "python" | 262–553 µs (~90 %) | 1516 µs |
| Motor | 26–55 µs | — |
| % del frame (16.7 ms) | 1.75–3.54 % | ~9.5 % |

## Lectura

- Casi todo el costo es "python", pero esa etiqueta incluye cada llamada a Godot que no
  sea `move_and_slide`. Con esta medición no se puede separar la lógica del costo de cruzar
  de Python a Godot. Para eso se escribió el microbenchmark.
- No se registró qué se hizo en cada ventana; a partir de A1 se usan rutinas fijas.

## Hallazgo lateral

Los loops (`LoopPath`) nunca enganchan: `[LoopPath] reject speed: 0.0` incluso corriendo.
Silv confirmó que nunca funcionaron. Hipótesis (sin verificar): `loop_path.py` lee
`body.velocity`, que no es visible desde el nodo que obtiene, y el `except` convierte el
error en velocidad 0. Queda en `TODO.md` para cuando se reimplementen los loops.
