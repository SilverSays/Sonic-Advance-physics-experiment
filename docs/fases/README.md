# Bitácora por fase

Un archivo por fase de la migración a la Sonic Physics Guide (SPG): qué se hizo,
qué decisiones se tomaron y por qué, cómo se verificó jugando y cuánto cuesta en
rendimiento. Los commits citados están en la rama `feat/fisica-spg`.

| Fase | Archivo | Estado |
|---|---|---|
| 0. Medición base | [00-baseline.md](00-baseline.md) | Hecha |
| A1. Suelo plano | [A1-suelo-plano.md](A1-suelo-plano.md) | Hecha, verificada jugando |
| A2. Salto y aire | [A2-salto-y-aire.md](A2-salto-y-aire.md) | Hecha, verificada jugando |
| Microbenchmark Python vs Godot | (en curso, se documenta al tener resultados) | En curso |
| A3. Roll y spindash | — | Por hacer |

Notas sobre las mediciones:
- Todas se tomaron desde el editor de Godot 3.6.1 (modo debug), con una RTX 3050.
- `[perf]` mide `SonicPhysics.step()` en ventanas de 120 frames. "motor" es solo
  `move_and_slide`; "python" es todo lo demás, **incluidas** las demás llamadas a Godot
  (`Input`, `is_on_floor`, `Vector2`...).
- Una medición solo se compara con otra si la rutina de juego es parecida.
