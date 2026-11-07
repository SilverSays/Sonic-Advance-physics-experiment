# Pendientes

## Por probar (cambios ya aplicados)
- [-] Aterrizaje sin perder velocidad (_ground_speed sincronizada)
- [x] Pegarse al suelo en bajadas con baches (snap por velocidad)
- [x] Techo corta la subida
- [ ] Panel de boost funciona en el suelo
- [ ] Salida del loop conserva velocidad
- [-] A. Rodar en pendientes gana/pierde velocidad (roll_speed se sincroniza con _ground_speed) — `FIX(roll-pendiente)`
- [-] B. Aterrizar en rampas de 45°–65° cuenta como suelo (floor_max_angle = max_walk_slope_deg) — `FIX(floor-angle)`
- [ ] C1. Resorte hacia arriba funciona estando en el suelo — `FIX(resorte-arriba)`
- [ ] C2. Resorte hacia arriba rodando ya no lanza hacia la derecha — `FIX(resorte-roll)`
- [ ] D. En el aire el input ya no acelera por encima de air_ctrl_cap — `FIX(aire-acelera)`
- [ ] E. Aterrizar/ir más rápido que el objetivo decae suave (overspeed_decel) en vez de frenazo — `FIX(sobrevelocidad)`
- [ ] F. Rodar cuesta arriba frena menos (slope_roll_up_factor) y en pendiente sigue rodando hacia abajo — `FIX(roll-subida)`
- [ ] G. Spindash más potente (1100–1800) y ya no se anula al soltar — `FIX(spindash)`

## Bugs conocidos
- [ ] Pared de frente en suelo caminable no frena
      Hipótesis: `sonic_physics.py`, bloque "Parada seca POR PARED": el `continue` cuando
      is_on_floor() y suelo caminable se salta toda detección de pared.
- [ ] Hitbox de crouch no se reduce (la cápsula no tiene extents)
- [ ] `script = null` en la instancia del jugador en `items/checkpoint/Node2D.tscn`
      Hipótesis: ese override quita personaje.py en la escena principal (suele pasar si el
      editor guardó sin cargar el plugin de Python). Revisar en el inspector del nodo.
      Lo mismo con el PluginScript vacío en ParallaxLayer2.
- [ ] Si `LoopPath.drive()` lanza excepción, el jugador queda sin colisión (capas en 0) y
      atraviesa el suelo: el `except` de `Personaje._physics_process` no restaura las capas.
- [ ] Morir dentro de un loop: el driver tiene prioridad y `_death_tick` nunca corre.
- [ ] LoopPath recorre todo el árbol cada frame buscando al jugador: `player_name_hint` es
      "Personaje" pero el nodo se llama KinematicBody2D y no está en el grupo "Player".

## Deuda técnica
- [ ] `except Exception: pass` por todas partes oculta errores; el import de SonicPhysics
      falla en silencio (Sonic cae sin control y sin mensaje).
- [ ] ~15 parámetros leídos con getattr() no están exportados (max_walk_slope_deg, wall_run_*,
      floor_snap_*, slope_*_boost, air_*): no se pueden ajustar en el inspector.
- [ ] Exports sin uso: accel_air, brake, friction, slope_influence, static_friction_threshold,
      sprint*_min_time; sprint1_timer/sprint2_timer nunca aumentan.
- [ ] Estado no inicializado en _ready: _ground_speed, _was_airborne, surface_up_dir, _no_snap_timer.
- [ ] 4 scripts de resorte casi idénticos → una clase Spring con dirección exportada.
- [ ] SonicPhysics.step() (~440 líneas) → dividir en métodos.
- [ ] Borrar surface_physics.py (sin uso).
- [ ] .gitattributes para que los .import no salgan modificados por LF/CRLF.

## Sin revisar
- [ ] Niveles (suelos/), colisiones de badnik_bullet con el propio badnik
