# Fase A2 — Salto y aire

**Fecha:** 2026-11-13 · **Commits:** `450e69d` (código), `13356f6` (resultados)

## Qué se hizo

Se añadió a `Sonic/sonic_physics.py` el salto y el movimiento en el aire, según las
secciones "Jumping", "Midair" y "Air State" de la SPG.

| Constante | Valor (px/frame) | Qué hace |
|---|---|---|
| `JMP` | 6.5 | Fuerza del salto, a lo largo de la normal del suelo |
| `JMP_RELEASE` | −4 | Al soltar el botón subiendo, la velocidad vertical se limita a esto |
| `AIR_ACC` | 0.09375 | Aceleración en el aire (el doble que en el suelo) |
| `GRV` | 0.21875 | Gravedad |
| Air drag | ~1/32 de `xsp` por frame | Solo cerca del ápice (−4 < `ysp` < 0) |

## Decisiones y por qué

- **Orden de operaciones de la guía:** en el aire, salto variable → input → air drag →
  mover → gravedad. La gravedad después de mover es lo que da la altura exacta del salto.
- **Jump delay:** el frame en que salta, Sonic no se mueve, como en Genesis. Sonic Mania
  lo quitó. Queda como opción (`JUMP_DELAY`) por si se ajusta en A5.
- **Salto a lo largo de la normal:** se suma a la velocidad que ya traía. En plano es
  simplemente hacia arriba.
- **Air drag:** el Markdown de la guía da `floor(X Speed >> 2) / 256`, que parece mal
  convertido. Se usa `floor(xsp * 8) / 256` (equivale a desplazar los subpíxeles 5 bits).
  Es una hipótesis pendiente de confirmar con la wiki original.
- **Tope en el aire:** igual que en suelo, el input no acelera por encima de 6 pero no
  recorta. No está confirmado si Sonic 1/2 recortaban en el aire.
- **Tope de caída de 16 px/frame:** provisional; la guía solo lo lista para Sonic CD.

Según las cuentas (sin medir): salto completo de ~100 px en 61 frames; soltando enseguida,
~39 px en 38 frames.

## Verificado jugando

Rutina: 5 s corriendo, salto corto en una pendiente de bajada, 5 s corriendo, salto
corto, salto largo.

- El salto "se siente genial": buena movilidad y resistencia en el aire.
- Comparado directamente con Sonic Advance 1: **casi idéntico**.
- El salto corto y el largo se distinguen bien.
- El jump delay no se nota.

**Lo que esto cambia del plan:** se pensaba que el aire de Advance era más permisivo que el
de Genesis, pero con los valores exactos de Genesis ya se siente como Advance. El ajuste de
"más control en el aire" previsto para A5 quizá no haga falta.

## Rendimiento

| | A1+A2 (rutina con saltos) | A1 (solo correr) |
|---|---|---|
| Total `step()` | 181–269 µs | 144–222 µs |
| "python" | 155–239 µs | 115–189 µs |
| Motor | 20–35 µs | 23–35 µs |

A2 añadió unos 50 µs por frame. Lo nuevo que corre en cada frame es poco: dos llamadas más
a `Input` y la rama del aire. Hipótesis: si esas dos llamadas explican buena parte de la
diferencia, cada llamada de Python a Godot costaría decenas de µs. El microbenchmark
(`Sonic/bench.py`) se escribió para comprobarlo.
