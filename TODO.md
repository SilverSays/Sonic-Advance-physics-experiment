# Pendientes

Leyenda: `[ ]` por hacer · `[x]` hecho y verificado jugando · `[-]` hecho, sin verificar jugando
o con resultado parcial · `[~]` obsoleto por la migración.

## Fases de la migración a la SPG

### Fase 0 — Medición base
- [x] Medir `SonicPhysics.step()` con el sistema viejo (2026-11-13; resultados en `.ai/SYNC.md`).

### Fase A — Modelo de velocidad SPG (se mantiene KinematicBody2D)
- [ ] A1. Suelo plano: aceleración, desaceleración (con el quirk de 0.5), fricción y tope (versión S2+).
      - [-] Módulo escrito y activado (2026-11-13): `Sonic/sonic_physics.py`. El viejo está en
            `Sonic/legacy/sonic_physics_legacy.py`. Falta que Silv lo revise.
      - [-] Probado jugando (2026-11-13): paredes frenan en seco, animaciones bien, pendientes sin
            cambio de velocidad (esperado). Falta: opinión de Silv sobre la sensación de aceleración y
            frenado, y medición con rutina fija.
      - [x] La regla de pared nueva frena contra paredes (verificado jugando).
- [x] A2. Salto y aire (2026-11-13). Verificado jugando: se siente casi igual a Sonic Advance 1.
      Pendiente: confirmar la fórmula del air drag en la wiki y el tope de caída.
      Ojo: en el Markdown de la SPG, la fórmula del air drag (`floor(X Speed >> 2) / 256`)
      parece mal convertida. Compararla con la wiki.
- [ ] A3. Roll y spindash (fricción y deceleración del roll, spinrev y su decaimiento).
- [ ] A4. Pendientes: slope factor, aterrizaje según ángulo, resbalar o caerse con poca
      velocidad, control lock.
- [x] Resolución interna 240x160 como la GBA (2026-11-13, se queda).
- [ ] A5. Ajustes hacia Sonic Advance, uno por uno y probados por separado:
      aceleración más directa, más control en el aire, flujo menos castigador a alta velocidad,
      frenado al girar menos brusco (DEC), quitar el jump delay (como Mania).
      Por ahora son descripciones cualitativas (de haber jugado). Si hacen falta números,
      medir Advance en un emulador con avance cuadro a cuadro.

- [-] Medir el costo de una sola llamada Python→Godot con un microbenchmark (`Sonic/bench.py`,
      export `bench_on_start`). Escrito 2026-11-13, falta correrlo.
- [ ] Revisar que nada del nivel ni del HUD dependa de la resolución vieja (384x216).

### Fase B — Sensores por raycast
- [ ] Sensores A/B (suelo), C/D (techo), E/F (empuje) según `docs/06-slope-collision.md` de la SPG.
- [ ] Medir el costo de los raycasts desde Python (cada llamada cruza la frontera Python↔Godot).
- [ ] Revisar si hace falta subir de 60 Hz para no atravesar paredes a alta velocidad.
      Hacerlo implica reescalar todas las constantes.

### Reimplementar sobre el sistema nuevo
- [ ] Animaciones completas (ver `docs/animaciones-legacy.md`), con la duración de cuadro
      variable de la guía.
- [ ] Mirar arriba y abajo, agacharse (con hitbox real).
- [ ] Daño, knockback, invulnerabilidad, anillos soltados, muerte y respawn.
- [ ] Regla de unidades: que todos los que escriben `velocity` usen
      `set_ground_speed()` o `set_air_speed()`:
      - [ ] `personaje.py`: `external_boost`, `_start_hit_reaction`, `_start_death`,
            `_respawn`, `_release_spindash`, `_stop_roll`, `detach_path_driver`.
      - [ ] `Sonic/loop_path.py`.
      - [ ] Los 4 resortes y `items/DashPanel/DashPanel.py`: llaman a `external_boost` (px/s)
            y, si no existe, escriben `velocity` del jugador directamente.
      - (`badnik_bullet.py` usa su propia `velocity`, no la del jugador: no aplica.)
- [ ] Exports en px/frame para ajustar las constantes desde el inspector. Los exports
      viejos están en px/s y ya no los usa el módulo nuevo.

## Organización del proyecto (propuesta, sin aplicar)
- [ ] Decidir la estructura nueva. Propuesta en `.ai/SYNC.md`, sección "Propuesta de reorganización".
- [ ] Mover desde el FileSystem del editor de Godot (actualiza las referencias en `.tscn`),
      no desde el explorador de Windows.
- [ ] Después de mover, corregir a mano lo que Godot no actualiza: imports de Python
      (`from Sonic.sonic_physics ...`) y strings `"res://..."` dentro de los `.py`.
- [ ] Renombrar las piezas de suelo por forma (plano, pendiente, etc.) en vez de por número.
      Hoja y tabla con nombres propuestos en `docs/tiles/suelos.md`. Corregir antes las escenas
      que usan el PNG equivocado (14↔15, 284↔286, 152→156, 249→294) y los duplicados (31, 34, 44).
- [ ] Decidir qué hacer con los ~634 PNG de `Sprites/sunset hill/` que ninguna escena usa
      (704 en total, 70 en uso).

## Bugs conocidos
- [ ] `items/DroppedRing.tscn` apunta a `res://rings/__pycache__/ring_idle.tres`, que no existe.
      `__pycache__/` está en `.gitignore`, así que tampoco está en el repo.
      Hipótesis: los anillos soltados al recibir daño no cargan su animación o fallan al instanciarse.
- [ ] El sistema viejo pedía una animación `"crouch"` que no existe en el AnimationPlayer.
- [ ] Pared de frente en suelo caminable no frena (sistema viejo).
      Hipótesis: `sonic_physics.py` viejo, bloque "Parada seca POR PARED": el `continue`
      cuando is_on_floor() y suelo caminable se salta toda detección de pared.
- [ ] Hitbox de crouch no se reduce (la cápsula no tiene extents).
- [ ] `script = null` en la instancia del jugador en `items/checkpoint/Node2D.tscn`.
      Hipótesis: ese override quita personaje.py en la escena principal (suele pasar si el
      editor guardó sin cargar el plugin de Python). Revisar en el inspector del nodo.
      Lo mismo con el PluginScript vacío en ParallaxLayer2.
- [ ] Los loops nunca enganchan: `[LoopPath] reject speed: 0.0` aunque Sonic vaya corriendo
      (sistema viejo y nuevo). Hipótesis: `loop_path.py` `_try_attach` lee `body.velocity`, que es atributo
      de Python y no se ve desde el nodo que obtiene LoopPath; la excepción se traga y `sp = 0.0`.
      Para verificar: imprimir la excepción en ese `except`. Al arreglarlo, leer la velocidad con la API
      de física (`get_speed`, px/frame) según la regla de unidades.
- [ ] Si `LoopPath.drive()` lanza excepción, el jugador queda sin colisión (capas en 0) y
      atraviesa el suelo: el `except` de `Personaje._physics_process` no restaura las capas.
- [ ] Morir dentro de un loop: el driver tiene prioridad y `_death_tick` nunca corre.
- [ ] LoopPath recorre todo el árbol cada frame buscando al jugador: `player_name_hint` es
      "Personaje" pero el nodo se llama KinematicBody2D y no está en el grupo "Player".
- [ ] Mayúsculas inconsistentes: la carpeta es `Sonic/` pero `rings/Area2D.py` dice
      `res://sonic/ring.py` en su comentario. En Windows no importa, pero en un export (PCK)
      las rutas distinguen mayúsculas.

## Deuda técnica
- [ ] `except Exception: pass` por todas partes oculta errores (el módulo nuevo ya no lo usa).
- [ ] Comentarios de cabecera con rutas viejas: `checkpoint.py` dice `res://objects/Checkpoint.py`,
      `DashPanel.py` dice `res://objects/DashPanel.py`, `rings/Area2D.py` dice `res://sonic/ring.py`.
- [ ] Estado no inicializado en _ready: _ground_speed, _was_airborne, surface_up_dir, _no_snap_timer
      (deja de importar cuando se retire el sistema viejo).
- [ ] 4 scripts de resorte casi idénticos → una clase Spring con dirección exportada.
- [ ] Borrar `Sonic/surface_physics.py` (sin uso).
- [ ] `.gitattributes` para que los `.import` no salgan modificados por LF/CRLF.
- [ ] Borrar `.git/stale-index-lock-claude` (lock que quedó de una sesión de Claude).

## Sin revisar
- [ ] Niveles (suelos/), colisiones de badnik_bullet con el propio badnik.
- [ ] `Area2D.tscn` en la raíz es la escena del checkpoint, pero el nivel no la instancia.
      ¿Hay checkpoints en el nivel?

## Archivado: cambios del sistema viejo sin probar (obsoletos por la migración)
- [~] Aterrizaje sin perder velocidad · panel de boost en el suelo · salida del loop conserva
      velocidad · A. roll en pendientes · B. floor-angle · C1/C2 resortes · D. aire-acelera ·
      E. sobrevelocidad · F. roll-subida · G. spindash.
      Siguen en el historial (commit `22e4b49`). Sirven de referencia de síntomas para las fases A2–A4.
- [x] Pegarse al suelo en bajadas con baches (snap por velocidad) — sistema viejo.
- [x] Techo corta la subida — sistema viejo.
