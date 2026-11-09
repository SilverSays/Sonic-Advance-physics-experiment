# Animaciones del sistema viejo (referencia para reimplementar)

El código que elegía las animaciones vivía en `Sonic/sonic_physics.py` (versión del commit `22e4b49`,
sección "Animaciones / flip", líneas ~440–579). Para verlo completo:

    git show 22e4b49:Sonic/sonic_physics.py

Las animaciones en sí **no se pierden**: están en el `AnimationPlayer` de `Sonic/KinematicBody2D.tscn`.
Lo que se pierde al reemplazar el módulo es la lógica que decide cuál reproducir. Este archivo la resume.

## Animaciones en el AnimationPlayer (19)

RESET, idle, walk, sprint_start, sprint_mid, run, runmax, break, jump, fall, roll,
spin_charge, spin_idle, look_up, prelook_up, look_down, standup, hit, death

## Prioridad de la animación principal (sistema viejo)

Se evaluaba en este orden; gana la primera que aplique:

1. `hit` si `hitstun_timer > 0`
2. `roll` si `is_rolling`
3. `break` si `is_braking`
4. `break` si está en suelo, el input va contra el signo de `_ground_speed` y está en run o runmax (`_is_run_or_maxrun()`)
5. Estados de mirar (ver abajo): `look_up`, `standup`; durante `look_down` no se cambia nada
6. En suelo:
   - `crouch` si `crouching` — **bug: no existe una animación "crouch" en el AnimationPlayer**
   - si `|gs| > 0.1` (px/s), según `run_meter` y velocidad:
     - `runmax` si `run_meter >= run_to_max` o `|gs| >= 0.98 * run_speed`
     - `run` si `|gs| >= run_threshold` y `run_meter >= sprint_to_run`
     - `sprint_mid` / `sprint_start` según `sprint2_threshold` / `sprint1_threshold` y sus timers
       (ojo: `sprint1_timer` y `sprint2_timer` nunca aumentan, ver TODO.md)
     - `walk` en otro caso
   - `idle` si `|gs| <= 0.1`
7. En el aire: `jump` si `velocity.y < 0`, si no `fall`

Animaciones disparadas fuera de esa prioridad:
- `jump` al saltar
- `spin_charge` al cargar spindash, `spin_idle` mientras se mantiene
- `roll` al empezar a rodar, al soltar el spindash y en `external_boost` con roll
- `hit` y `death` desde `personaje.py`

## Mirar arriba / abajo (máquina de estados `look_mode`)

Solo con `|gs| < 1` en suelo caminable.

- Abajo recién presionado → `look_down` (estado `look_down_playing` durante lo que dura la animación, luego `look_down_done`)
- Soltar abajo → `standup` (estado `standup_wait`) → `None`
- Arriba mantenido → `prelook_up` (estado `wait_prelook_up`) → `look_up` (estado `look_up`)
- Soltar arriba → `standup` → `None`
- `look_timer` se descontaba con `delta` y usaba `_anim_len` (largo de cada animación, calculado en `personaje._ready`)

## Flip del sprite

Por signo de `_ground_speed`: `> 0.1` → `sprite.flip_h = True` (mira a la derecha), `< -0.1` → `False`.
El sprite base mira a la izquierda.

## Otros efectos visuales en el módulo viejo

- Parpadeo de invulnerabilidad: `sprite.visible` alterna con `_blink_accum * hit_blink_freq`
- Hitbox de agacharse: cambia `cshape_node.shape.extents` (TODO.md: la cápsula no tiene extents, no funcionaba)

## Al reimplementar

- Los umbrales viejos están en px/s; el módulo nuevo usa px/frame (dividir entre 60).
- La guía tiene reglas propias (docs/21-animations.md del repo de la SPG): idle solo con gs == 0 exacto,
  walk con cualquier gs, run con |gs| >= 6, braking al girar con |gs| >= 4, y duración de cada cuadro
  de walk/run = floor(max(0, 8 - |gs|)) frames.
