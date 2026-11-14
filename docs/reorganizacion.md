# Propuesta de reorganización de carpetas (sin aplicar)

Se aplicará cuando la fase A esté estable. La referencia de las piezas de suelo
(escenas intercambiadas, duplicados, rampas y nombres propuestos) está en
[tiles/suelos.md](tiles/suelos.md).

## Lo que hay hoy y por qué confunde

- El nivel de prueba es `items/checkpoint/Node2D.tscn`, dentro de la carpeta del checkpoint.
- La escena del checkpoint es `Area2D.tscn`, suelta en la raíz.
- El jugador es `Sonic/KinematicBody2D.tscn` y el anillo `rings/Area2D.tscn`: los nombres
  son tipos de nodo, no lo que representan.
- `badnik_bullet.py` está en la raíz y su escena en `enemies/`.
- `Sprites/enemies/bg-sunset-hill-zone.png` es un fondo, no un enemigo.
- `suelos/N.tscn` y `Sprites/sunset hill/N.png` se nombran por número de recorte.

## Estructura propuesta

Por funcionalidad: escena, script y recursos juntos. Nombres en inglés (decidido).

```text
player/                 sonic.tscn, personaje.py, sonic_physics.py, perf.py, bench.py, legacy/
objects/
  checkpoint/           checkpoint.tscn, checkpoint.py
  springs/              spring_up/down/left/right.tscn (+ una sola clase Spring después)
  dash_panel/
  rings/                ring.tscn, ring.py, dropped_ring.tscn, dropped_ring.py
  loop_path/            loop_path.tscn, loop_path.py
enemies/badnik_flyer/   badnik_flyer.tscn/.py, badnik_bullet.tscn/.py
levels/
  test_level.tscn
  sunset_hill/tiles/    piezas de suelo con nombre por forma
Sprites/                se mantiene por tipo; "sunset hill" pasa a sunset_hill;
                        el fondo pasa a background/
background/, docs/, addons/   sin cambios
```

## Pendiente de decidir

- Qué hacer con las 55 escenas de `suelos/` que el nivel no usa: dejarlas o archivarlas.
- Qué hacer con los 3 duplicados (`31`, `34`, `44`): borrarlos o dejarlos como variantes.

## Riesgos y cómo hacerlo

- Godot 3 identifica todo por ruta `res://`. Hay que mover desde el FileSystem del editor,
  que actualiza las referencias dentro de `.tscn` y `.tres`.
- Godot **no** actualiza los imports de Python (`from Sonic.sonic_physics import ...`) ni los
  strings `"res://..."` dentro de los `.py` (`personaje.py` → `res://items/DroppedRing.tscn`,
  `badnik_flyer.py` → `res://enemies/badnik_bullet.tscn`). Esos se corrigen a mano.
- Las carpetas que se importan desde Python deben tener nombres válidos: minúsculas, sin espacios.
- Commit antes de reorganizar y otro justo después, sin mezclar con cambios de física.
