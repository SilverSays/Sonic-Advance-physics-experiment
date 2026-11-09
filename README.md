# Sonic Advance - Physics Experiment

Fangame 2D de Sonic con físicas estilo **Sonic Advance**, hecho en Godot 3 con
**Python** en lugar de GDScript.

Además del juego, es un reto personal: **ver hasta dónde se puede llevar Python
en un juego de plataformas rápido**, y cuánto se puede optimizar, a medida que se
añaden enemigos, objetos interactivos y coleccionables.

> **Estado:** prototipo. Las físicas se están reescribiendo desde cero.
>
> - `main` tiene el sistema de físicas **viejo**, jugable pero con errores conocidos.
> - El trabajo nuevo está en la rama **`feat/fisica-spg`**. Ahí también están el plan
>   detallado (`TODO.md`), la documentación (`docs/`) y las notas de trabajo (`.ai/SYNC.md`).
> - Se fusiona a `main` cada vez que una fase funciona jugando.

## Rumbo del proyecto

Las físicas se están reescribiendo siguiendo la
[Sonic Physics Guide](https://info.sonicretro.org/Sonic_Physics_Guide) (SPG), el
documento de referencia sobre cómo funcionan los Sonic clásicos por dentro. Se usa
como apoyo la versión en Markdown del repo
[trentbrew/sonic-physics-guide](https://github.com/trentbrew/sonic-physics-guide).
Es una conversión automática: si una fórmula se ve rara, se compara con la wiki original.

- **Base:** los valores y el orden de operaciones de los Sonic de Genesis.
- **Destino:** la sensación de Sonic Advance (aceleración más directa, más control
  en el aire, menos castigo en secciones rápidas). Los cambios hacia Advance se hacen
  uno por uno sobre la base de la guía, y se prueba cada uno por separado.

### Por qué

- **El sistema viejo se arreglaba a parches.** Cada bug se corregía con un ajuste
  propio (snap variable, topes, sincronizar la velocidad en varios lugares), y esos
  arreglos chocaban entre sí. La SPG describe un modelo completo, probado durante
  décadas: en vez de inventar la física, se replica una que ya funciona.
- **Números comparables.** Usar las mismas unidades que la guía (píxeles por frame a
  60 Hz) deja comparar cada constante 1:1 con ella, y documentar cada ajuste hacia
  Advance como un cambio sobre un valor conocido.
- **Aprender la guía.** Implementarla paso a paso es la forma de entender por qué
  Sonic se siente como se siente.
- **El reto de rendimiento.** Los sensores por raycast de la guía obligan a hacer
  muchas llamadas a Godot desde Python cada frame. Eso es justo lo que se quiere medir
  y optimizar, y por eso se mide desde el primer día.

## Roadmap

| Fase | Qué incluye | Estado |
|---|---|---|
| **0. Medición base** | Medir cuánto cuesta por frame la física vieja (parte Python y parte motor) | Instalada, falta correrla |
| **A1. Suelo plano** | Aceleración, desaceleración, fricción y velocidad tope de la SPG | Escrita, sin probar |
| **A2. Salto y aire** | Salto variable, control y resistencia en el aire, gravedad | Por hacer |
| **A3. Roll y spindash** | Fricción del roll, carga y lanzamiento del spindash | Por hacer |
| **A4. Pendientes** | La pendiente acelera y frena, aterrizaje según ángulo, resbalar en paredes | Por hacer |
| **A5. Hacia Advance** | Ajustes uno por uno para la sensación de Sonic Advance | Por hacer |
| **B. Sensores** | Cambiar la colisión de Godot por sensores raycast como los de la guía | Por hacer |
| **Reimplementar** | Animaciones completas, daño y muerte, resortes, paneles, loops, mirar arriba y abajo | Por hacer |
| **Juego** | Más enemigos, objetos, coleccionables y niveles, midiendo el rendimiento en cada paso | Futuro |

Durante la fase A se mantiene la colisión de Godot (`KinematicBody2D`) mientras se
reescribe el modelo de velocidad. Así, si algo se siente mal, se sabe que la causa es
la velocidad y no la colisión. Los sensores llegan en la fase B.

Hay también una reorganización de carpetas y nombres pendiente, para cuando la fase A
esté estable.

### Regla de unidades

La velocidad de Sonic (en px/frame) vive **solo** en el módulo de física. Todo lo
demás (resortes, paneles, loops, daño) la cambia a través de él, nunca escribiendo
`velocity` directamente. Es la causa de varios bugs del sistema viejo: había varios
lugares guardando "la velocidad" y se desincronizaban.

## Tecnologías

- **Godot 3.6.1**
- **godot-python** (PythonScript 0.50, Python 3.8), incluido en `addons/pythonscript/`
- Windows. Los `.py` y `.tscn` usan tabuladores.

## Ejecutar el proyecto

1. Instala Godot 3.6.1. Godot 4 no sirve.
2. Clona este repositorio. Para el trabajo nuevo: `git switch feat/fisica-spg`.
3. Abre la carpeta del proyecto desde el editor de Godot.
4. Ejecuta la escena principal con **Play**.

La escena principal es `items/checkpoint/Node2D.tscn` (el nivel de prueba). En la
rama nueva, las líneas `[perf]` de la consola muestran el costo por frame de la física.

## Controles

- **Flecha izquierda / derecha:** moverse.
- **Flecha abajo:** agacharse, rodar o preparar el spindash.
- **Espacio:** saltar o cargar el spindash.

En la rama `feat/fisica-spg`, durante la fase A1, solo funciona el movimiento horizontal.
Lo demás está desactivado a propósito hasta su fase.

## Estructura principal

```text
Sonic/       Jugador: personaje.py, módulo de física, loops.
items/       Checkpoint, resortes, panel de impulso, anillo soltado.
             (items/checkpoint/Node2D.tscn es el nivel de prueba).
rings/       Anillo coleccionable.
enemies/     Enemigo volador y su proyectil.
suelos/      Piezas de suelo (StaticBody2D con un tile de Sunset Hill).
Sprites/     Gráficos.
background/  Fondos de Sunset Hill.
addons/      Runtime de Python para Godot (no tocar).
```
