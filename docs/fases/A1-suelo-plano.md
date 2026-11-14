# Fase A1 — Suelo plano

**Fecha:** 2026-11-13 · **Commits:** `bfb5a04` (módulo escrito), `1ce3035` (activado),
`9482096` (resultados), `b57003d` (prueba de resolución)

## Qué se hizo

Se reescribió `Sonic/sonic_physics.py` desde cero según la sección "Running" de la SPG.
El sistema viejo pasó a `Sonic/legacy/sonic_physics_legacy.py` (ya no se importa) y su
lógica de animaciones quedó documentada en `docs/animaciones-legacy.md`.

| Constante | Valor (px/frame) | Qué hace |
|---|---|---|
| `ACC` | 0.046875 | Aceleración al presionar una dirección |
| `DEC` | 0.5 | Frenado al presionar contra el movimiento |
| `FRC` | 0.046875 | Fricción sin input |
| `TOP` | 6 | Tope de velocidad por input |

## Decisiones y por qué

- **Unidades en px/frame a 60 Hz, sin `delta`:** igual que la guía, para comparar cada
  constante 1:1 y documentar los ajustes hacia Advance como cambios sobre un valor conocido.
  En Godot 3 `_physics_process` ya es de paso fijo, así que `delta` no aportaba nada.
- **Regla de unidades:** la velocidad (`gs`, `xsp`, `ysp`) vive solo en el módulo de física.
  El resto del código la cambia con `set_ground_speed()` / `set_air_speed()`. El sistema
  viejo tenía varios lugares guardando "la velocidad" y se desincronizaban.
- **Tope estilo Sonic 2:** por encima de `TOP` el input deja de acelerar, pero no recorta.
  Así no se pierde velocidad de un resorte o una rampa por mantener la flecha.
- **Quirk de desaceleración:** al cruzar el cero frenando, la velocidad salta a ±0.5 en la
  dirección contraria. Es lo que hace el juego original.
- **Paredes:** si hay una pared en la dirección del movimiento, la velocidad pasa a 0.
- **Se mantiene `KinematicBody2D`:** los sensores por raycast son la fase B. Cambiar la
  velocidad y la colisión a la vez haría imposible saber cuál causa un problema.
- `personaje.py` imprime el error si falla el import de la física (antes Sonic caía sin
  control y sin mensaje).

## Verificado jugando

- Las pendientes no cambian la velocidad: es lo esperado, el slope factor es la fase A4.
- Contra una pared se detiene en seco.
- Animaciones correctas; `runmax` nunca aparece (necesita 10 px/frame y el tope es 6).
- **Sensación:** mucho más lento que el sistema viejo (tope 360 px/s contra ~1000 px/s).
  La aceleración se siente bien y acorde al tope. El frenado al girar se siente brusco:
  se deja para la fase A5, porque es el valor de Genesis.

## Prueba de resolución

Con 384×216 se ve 1.6 veces más mundo a lo ancho que en una GBA (240×160), así que a la
misma velocidad Sonic parece más lento. Se cambió a 240×160 (ventana de 960×640).
Resultado: ayuda un poco con la sensación de velocidad, sin ser una diferencia grande.
**Se queda.**

## Rendimiento

Rutina: solo derecha hasta la pared del final. Reloj: 0.21 µs por par.

| | A1 | Baseline (sistema viejo) |
|---|---|---|
| Total `step()` | 144–222 µs | 292–590 µs |
| "python" | 115–189 µs | 262–553 µs |
| Motor | 23–35 µs | 26–55 µs |

**No es una comparación justa:** A1 hace mucho menos (sin salto, roll, daño ni la mayoría
de animaciones). Sirve como punto de partida, no para decir que el sistema nuevo es más rápido.
