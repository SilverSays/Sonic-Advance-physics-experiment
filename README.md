# Sonic Advance - Physics Experiment

Fangame 2D de Sonic con físicas estilo **Sonic Advance**, hecho en Godot 3 con
**Python** en lugar de GDScript.

Además del juego, es un reto personal: **ver hasta dónde se puede llevar Python
en un juego de plataformas rápido**, y cuánto se puede optimizar, a medida que se
añaden enemigos, objetos interactivos y coleccionables.

> **Estado:** prototipo en plena migración de físicas. Durante la fase actual
> muchas mecánicas están desactivadas a propósito (ver "Rumbo actual").

## Rumbo actual

Las físicas se están reescribiendo desde cero siguiendo la
[Sonic Physics Guide](https://info.sonicretro.org/Sonic_Physics_Guide) (SPG).
Se usa como apoyo la versión en Markdown del repo
[trentbrew/sonic-physics-guide](https://github.com/trentbrew/sonic-physics-guide).
Es una conversión automática: si una fórmula se ve rara, hay que compararla
con la wiki original.

- **Base:** los valores y el orden de operaciones de los Sonic de Genesis (SPG).
- **Destino:** la sensación de Sonic Advance (aceleración más directa, más control
  en el aire, menos castigo en secciones rápidas). Los cambios hacia Advance se
  hacen poco a poco sobre la base de la guía, probando cada uno.
- **Unidades:** píxeles por frame a 60 Hz fijos, igual que la guía (sin `delta`).
- **Colisión:**
  - **Fase A:** se mantiene el `KinematicBody2D` + `move_and_slide_with_snap`
    mientras se reescribe el modelo de velocidad.
  - **Fase B:** migración a sensores por raycast como los de la guía.
- **Rendimiento:** cada frame se mide el costo de `step()`, separando Python y
  motor (`Sonic/perf.py`).

El plan por fases y las tareas están en [TODO.md](TODO.md).

### Regla de unidades

La velocidad de Sonic (`gs`, `xsp`, `ysp`, en px/frame) vive **solo** en el módulo
de física. El código externo (resortes, boosts, loops, daño) la cambia con
`set_ground_speed()` o `set_air_speed()`, nunca escribiendo `velocity` directamente.
`velocity` (px/s) es solo la entrada y salida de `move_and_slide`.

## Qué funciona ahora

Con el módulo nuevo (fase A, suelo plano):

- Aceleración, desaceleración, fricción y velocidad tope según la SPG.
- Animaciones mínimas: idle, walk, run, runmax, break y fall.

Desactivado hasta reimplementarlo con el sistema nuevo:

- Salto, roll y spindash.
- Física de pendientes.
- Daño y muerte (la muerte usa todavía el código viejo).
- Mirar arriba y abajo, y agacharse.
- Resortes, paneles de impulso y loops: siguen en la escena, pero escriben
  `velocity` directamente y el módulo nuevo los ignora.

La lógica de animaciones del sistema viejo está documentada en
[docs/animaciones-legacy.md](docs/animaciones-legacy.md).

## Tecnologías

- **Godot 3.6.1**
- **godot-python** (PythonScript 0.50, Python 3.8), incluido en `addons/pythonscript/`
- Windows. Los `.py` y `.tscn` usan tabuladores.

## Ejecutar el proyecto

1. Instala Godot 3.6.1. Godot 4 no sirve.
2. Clona este repositorio.
3. Abre la carpeta del proyecto desde el editor de Godot.
4. Ejecuta la escena principal con **Play**.

La escena principal configurada es `items/checkpoint/Node2D.tscn`, que es el
nivel de prueba. Pendiente: reorganizar y darle un nombre que se entienda.

Las líneas `[perf]` de la consola muestran el costo por frame de la física.
Se configuran con los exports `perf_enabled` y `perf_window` del jugador.

## Controles

- **Flecha izquierda / derecha:** moverse.
- **Flecha abajo / Espacio:** salto, roll y spindash. Desactivados en la fase actual.

## Estructura principal

```text
Sonic/       Jugador: personaje.py, módulo de física, perf.py, loops.
items/       Checkpoint, resortes, panel de impulso, anillo soltado.
             (items/checkpoint/Node2D.tscn es el nivel de prueba).
rings/       Anillo coleccionable.
enemies/     Enemigo volador y su proyectil.
suelos/      Piezas de suelo (StaticBody2D con un tile de Sunset Hill).
Sprites/     Gráficos.
background/  Fondos de Sunset Hill.
docs/        Documentación del proyecto.
.ai/         Coordinación entre agentes de IA (SYNC.md).
addons/      Runtime de Python para Godot (no tocar).
```

Hay una propuesta de reorganización pendiente; ver TODO.md.

## Documentos para trabajar en el proyecto

- `CLAUDE.md`: reglas de trabajo y arquitectura. Es la fuente de verdad.
- `TODO.md`: fases, tareas, bugs conocidos y deuda técnica.
- `.ai/SYNC.md`: estado de los scripts y dudas abiertas, para coordinar agentes.
