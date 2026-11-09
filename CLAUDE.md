# Sonic Advance (fangame 2D)

Fangame de Sonic con físicas estilo Sonic Advance. Es también un reto de rendimiento:
ver hasta dónde llega Python en un juego de plataformas rápido.

## Stack
- Godot 3.6.1 + godot-python (PythonScript 0.50, Python 3.8). Scripts en `.py`, no GDScript.
- Windows. Los `.py` y `.tscn` usan tabuladores; los `.py` usan saltos de línea CRLF.
- Repo en GitHub (privado). Silv trabaja en dos computadoras; lo que no está en un commit
  no existe en la otra.

## Cómo trabajar conmigo
- Actúa como auditor: señala problemas y explica la causa antes de proponer cambios.
- No edites archivos sin que yo lo pida.
- Pregúntame antes de dar respuestas largas cuando algo sea ambiguo.
- Sé analítico, no complaciente. Dime cuando me equivoque, aunque parezca convencido.
  Si no sabes algo, dilo.
- No puedes ejecutar el juego. Separa lo leído en el código de lo verificado jugando,
  y marca como *hipótesis* todo lo no verificado.
- Un cambio por síntoma, para poder probar cada uno por separado.
- No des cierres ordenados cuando el problema sigue abierto.
- Responde en español.

## Rumbo: migración a la Sonic Physics Guide (SPG)
- Referencia: https://info.sonicretro.org/Sonic_Physics_Guide. Versión en Markdown:
  https://github.com/trentbrew/sonic-physics-guide. Es una conversión automática y tiene
  al menos una fórmula dudosa: compara con la wiki cuando algo se vea raro.
  `docs/23-implementation-guide.md` de ese repo **no** es de la guía.
- **Base:** valores y orden de operaciones de los juegos de Genesis.
- **Destino:** sensación Sonic Advance. Los ajustes hacia Advance se hacen uno por uno,
  sobre la base de la guía. Las diferencias que describe Silv son cualitativas (de haber jugado).
- **Fases** (detalle en `TODO.md`):
  - 0: baseline de rendimiento.
  - A: modelo de velocidad SPG, manteniendo KinematicBody2D (A1 suelo plano, A2 aire,
    A3 roll y spindash, A4 pendientes, A5 ajustes Advance).
  - B: sensores por raycast.
  - Después: reimplementar lo desactivado.

## Reglas de física
- **Unidades:** px/frame y px/frame² a 60 Hz fijos, como la guía. `step()` no usa `delta`.
  Floats; el `floor()` solo se replica donde la guía lo usa.
- **Regla de unidades:** `gs`, `xsp` y `ysp` viven solo en el módulo de física. Código externo
  usa `physics.set_ground_speed(gs)` o `physics.set_air_speed(xsp, ysp)`, nunca escribe
  `velocity`. `velocity` (px/s) es solo la entrada y salida de `move_and_slide`, y se
  convierte en un único punto (×60 al entrar, ÷60 al salir).
- Tope de velocidad estilo S2+: por encima de `top`, el input no acelera, pero tampoco recorta.
- Gravedad en el aire **después** de mover (define la altura del salto).

## Arquitectura actual
- Jugador: `Sonic/KinematicBody2D.tscn`, KinematicBody2D con `move_and_slide_with_snap`
  (sin sensores todavía).
- `Sonic/personaje.py`: exports (los viejos están en px/s), vida y muerte, anillos,
  `external_boost`, driver de loops, medición de rendimiento.
- `Sonic/sonic_physics.py`: sistema **viejo** (px/s, delta). Se retira tras la baseline.
- `Sonic/sonic_physics_spg.py`: sistema **nuevo**, fase A1. Pasa a llamarse `sonic_physics.py`
  y el viejo se mueve a `Sonic/legacy/`.
- `Sonic/perf.py`: `StepProfiler`. Mide total, Python y motor por cada ventana de N frames.
- `Sonic/loop_path.py`: loops por Path2D (`attach`/`detach_path_driver`). Todavía en px/s.
- `Sonic/surface_physics.py`: sin uso.
- Escena principal (nivel de prueba): `items/checkpoint/Node2D.tscn`.
- Piezas de suelo: `suelos/N.tscn`. Ver `docs/tiles/suelos.md`.

## Rendimiento
- Las líneas `[perf]` en consola dan: costo total de `step()`, parte Python, parte motor
  (solo `move_and_slide`) y % del frame. Se configuran con los exports `perf_enabled`
  y `perf_window` del jugador.
- Los frames dentro de un loop no se miden.
- Las mediciones se anotan en `.ai/SYNC.md`, con fecha y qué se probó.

## Documentos
- `TODO.md`: fases, tareas, bugs y deuda técnica.
- `.ai/SYNC.md`: estado de cada script, dudas abiertas, mediciones y propuesta de
  reorganización. Coordinación entre agentes. Lee sus instrucciones antes de escribir.
- `docs/animaciones-legacy.md`: lógica de animaciones del sistema viejo.
- `docs/tiles/`: hoja de las piezas de suelo y tabla con nombres propuestos.
- Si este archivo contradice a otro documento, manda este.

## Git
- Rama de trabajo: `feat/fisica-spg` (migración a la SPG). `fix/fisica-sonic` queda como
  el último estado del sistema viejo.
- No incluir en los commits los `.import` que aparecen modificados solo por LF/CRLF.
- Reorganización de carpetas: commit antes y commit después, sin mezclarla con cambios de física.
- Mover archivos desde el FileSystem del editor de Godot, no desde el explorador.
  Los imports de Python y los `"res://..."` dentro de los `.py` se corrigen a mano.

## Agentes (futuro, todavía no activo)
Silv planea sumar a Gemini:
- **Gemini:** contexto amplio, inconsistencias entre nodos, planificación de sistemas grandes.
- **Claude:** ejecución quirúrgica: ediciones, refactors, comandos de prueba.

Hasta que Silv lo active, aplican las reglas de "Cómo trabajar conmigo".

## No tocar
- `.import/` y `__pycache__/` (se regeneran). Ojo: `items/DroppedRing.tscn` apunta por
  error a un `.tres` dentro de `rings/__pycache__/`, ver TODO.md.
- `addons/pythonscript` (binarios de la extensión).
