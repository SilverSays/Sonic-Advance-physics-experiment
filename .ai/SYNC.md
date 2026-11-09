# .ai/SYNC.md — Estado compartido entre agentes

## Qué es este archivo (léelo antes de escribir)

Es el punto de coordinación entre los agentes de IA que trabajan en este repo
(sesiones de Claude, y más adelante Gemini). No reemplaza a otros documentos:

- `CLAUDE.md` tiene las reglas de trabajo y la arquitectura. **Manda sobre este archivo.**
- `TODO.md` tiene las tareas y los bugs. Una tarea va allá, no aquí.
- Este archivo guarda lo que un agente necesita saber al llegar: en qué estado está
  cada script, qué dudas hay abiertas, qué se midió y qué está a medio hacer.

### Qué se puede escribir aquí
- Cambios en el estado de un script (tabla de abajo).
- Dudas abiertas para Silv o para otro agente, con contexto suficiente para entenderlas sin la conversación.
- Mediciones (`[perf]`) con fecha y qué se estaba probando.
- Trabajo a medio hacer: qué quedó, en qué archivo, qué falta.
- Inconsistencias entre nodos, escenas o scripts que hayas detectado.

### Qué NO va aquí
- Tareas o bugs nuevos: van en `TODO.md`.
- Reglas de trabajo: van en `CLAUDE.md`, y solo si Silv lo pide.
- Código largo. Basta con apuntar a archivo y línea.
- Conversaciones copiadas.

### Cómo escribir
1. Separa siempre **lo leído en el código** de **lo verificado jugando**. Lo no
   verificado se marca como *hipótesis*. Ningún agente puede ejecutar el juego;
   solo Silv lo verifica.
2. Firma y fecha cada entrada del registro: `AAAA-MM-DD · agente · resumen`.
3. No borres entradas de otro agente. Si algo dejó de ser cierto, márcalo
   `(resuelto AAAA-MM-DD: ...)` o `(obsoleto: ...)`.
4. Actualiza la tabla de estado cuando cambies un script, en el mismo momento.
5. Mantén el archivo corto: cuando el registro pase de unas 30 entradas, resume
   las viejas en un párrafo.

### Roles (futuro, todavía no activo)
Silv planea sumar a Gemini a este flujo:
- **Gemini:** contexto amplio. Detectar inconsistencias entre nodos y escenas y
  planificar sistemas grandes.
- **Claude:** ejecución quirúrgica. Ediciones puntuales, refactors de funciones
  y comandos de prueba.

Hasta que Silv lo active, cada agente trabaja según `CLAUDE.md`.

---

## Estado de los scripts de Python

Estado al 2026-11-08. "Verificado" significa probado jugando por Silv.

| Script | Estado | Notas |
|---|---|---|
| `Sonic/personaje.py` | En uso | Parámetros (exports viejos en px/s), vida y muerte, anillos, boost, driver de loops. Desde 2026-11-08 mide `step()` con `perf.py` (exports `perf_enabled`, `perf_window`). Varios métodos escriben `velocity` directamente (ver regla de unidades en README). |
| `Sonic/sonic_physics.py` | En uso, **a retirar** | Sistema viejo (px/s, delta). Tiene un cronómetro alrededor de `move_and_slide` para la baseline. Tras la baseline se mueve a `Sonic/legacy/sonic_physics_legacy.py`. |
| `Sonic/sonic_physics_spg.py` | Escrito, **sin revisar, sin probar** | Fase A1 de la SPG (suelo plano, px/frame). Reemplazará a `sonic_physics.py`. API: `set_ground_speed`, `set_air_speed`, `get_speed`. |
| `Sonic/perf.py` | Escrito, sin probar | `StepProfiler`: total, Python y motor por ventana de N frames. Calibra el costo de `OS.get_ticks_usec()` al iniciar. |
| `Sonic/loop_path.py` | En uso | Loops por Path2D. Escribe `body.velocity` en px/s: incompatible con el módulo nuevo hasta migrarlo. |
| `Sonic/surface_physics.py` | Sin uso | Intento anterior. Borrar. |
| `items/springs/*/*.py` (4) | En uso, ignorados por el módulo nuevo | Casi idénticos. Llaman a `external_boost` (px/s); si no existe, escriben `velocity` del jugador. |
| `items/DashPanel/DashPanel.py` | En uso, ignorado por el módulo nuevo | Llama a `external_boost` (px/s). |
| `items/checkpoint/checkpoint.py` | ¿En uso? | Su escena (`Area2D.tscn` en la raíz) no la instancia el nivel. |
| `items/dropped_ring.py` | En uso | Su escena apunta a un `.tres` que no existe (ver TODO.md). |
| `rings/Area2D.py` | En uso | Anillo coleccionable. |
| `enemies/badnik_flyer.py`, `badnik_bullet.py` | En uso | Sin revisar a fondo. La bala usa su propia `velocity` (no la del jugador). `badnik_bullet.py` está en la raíz y su escena en `enemies/`. |

## Mediciones `[perf]`

Formato: fecha · módulo · qué se hizo en la prueba · línea(s) `[perf]`.

- (vacío: falta la baseline del sistema viejo, Fase 0)

## Dudas abiertas

1. **godot-python y los `.py` sueltos:** ¿el editor intenta cargar los `.py` que no usa
   ninguna escena (`surface_physics.py`, el futuro `legacy/`)? Si lo hace, ¿da errores en
   consola? Lo tiene que ver Silv en el editor.
2. **¿Se importan `OS` y `Engine` desde `godot`?** `perf.py` usa `from godot import OS`
   y el módulo nuevo `from godot import Engine`. Por el patrón de `ResourceLoader`
   (que ya se importa así en `personaje.py`) debería funcionar, pero es *hipótesis*.
3. **Air drag en la SPG en Markdown:** `docs/11-forces-subtopics/air-state.md` del repo
   trentbrew dice `X Speed -= (floor(X Speed >> 2) / 256)`. Por memoria, el original equivale
   a aproximadamente `xsp/32` por frame. Verificar en la wiki antes de la fase A2.
4. **Tope de caída:** el módulo nuevo usa 16 px/frame como provisional. La SPG solo lo lista
   para Sonic CD. Confirmar qué hacen S1, S2, S3K y Advance.
5. **Orden del air drag:** `docs/12-main-game-loop.md` pone el drag *antes* de mover, y
   `air-state.md` dice que se aplica *después* de la gravedad. Resolver en la fase A2.

## Propuesta de reorganización (sin aplicar, pendiente de que Silv decida)

Lo que hay hoy y por qué confunde:
- El nivel de prueba es `items/checkpoint/Node2D.tscn`, dentro de la carpeta del checkpoint.
- La escena del checkpoint es `Area2D.tscn`, suelta en la raíz.
- El jugador es `Sonic/KinematicBody2D.tscn` y el anillo `rings/Area2D.tscn`: los nombres son tipos de nodo, no lo que representan.
- `badnik_bullet.py` está en la raíz y su escena en `enemies/`.
- `Sprites/enemies/bg-sunset-hill-zone.png` es un fondo, no un enemigo.
- `suelos/N.tscn` y `Sprites/sunset hill/N.png` se nombran por número de recorte.

Estructura propuesta (por funcionalidad: escena + script + recursos juntos):

```text
player/                 sonic.tscn, personaje.py, sonic_physics.py, perf.py, legacy/
objects/
  checkpoint/           checkpoint.tscn, checkpoint.py
  springs/              spring_up/down/left/right.tscn (+ una sola clase Spring después)
  dash_panel/
  rings/                ring.tscn, ring.py, dropped_ring.tscn, dropped_ring.py
  loop_path/            loop_path.tscn, loop_path.py
enemies/badnik_flyer/   badnik_flyer.tscn/.py, badnik_bullet.tscn/.py
levels/
  test_level.tscn
  sunset_hill/tiles/    piezas de suelo con nombre por forma, en inglés (decidido);
                        ver docs/tiles/suelos.md (intercambiadas, duplicados, rampas)
Sprites/                se mantiene por tipo; "sunset hill" pasa a sunset_hill;
                        el fondo pasa a background/
background/, docs/, .ai/, addons/   sin cambios
```

Lo que conviene dejar como está: la división de `Sprites/` por objeto, `background/`,
`docs/` y `addons/`.

Riesgos y cómo hacerlo:
- Godot 3 identifica todo por ruta `res://`. Hay que mover desde el FileSystem del
  editor, que actualiza las referencias dentro de `.tscn` y `.tres`.
- Godot **no** actualiza los imports de Python (`from Sonic.sonic_physics import ...`) ni
  los strings `"res://..."` en `.py` (`personaje.py` → `res://items/DroppedRing.tscn`,
  `badnik_flyer.py` → `res://enemies/badnik_bullet.tscn`). Esos se corrigen a mano.
- Los nombres de carpeta con imports de Python deben ser identificadores válidos:
  minúsculas, sin espacios.
- Hacer un commit antes de reorganizar y otro justo después, sin mezclar con cambios de física.
- Renombrar tiles por forma requiere ver cada imagen. Se puede generar una hoja de
  contacto con los 70 tiles en uso para clasificarlos.

## Registro

- 2026-11-08 · Claude · Nuevo rumbo: migración a la SPG en px/frame (fase A con KinematicBody2D,
  fase B con raycasts). Se añadió `perf.py` y la medición en `personaje.py` y el
  `sonic_physics.py` viejo. Se escribió `sonic_physics_spg.py` (A1, sin revisar). Se creó
  `docs/animaciones-legacy.md`. Se actualizaron README y TODO.
  Encontrado: `DroppedRing.tscn` apunta a un `.tres` inexistente en `__pycache__`; la
  animación `crouch` no existe. Se dejó `.git/stale-index-lock-claude` (borrar).
- 2026-11-08 · Claude · `CLAUDE.md` reescrito con el rumbo nuevo. Se creó `docs/tiles/` (hoja de
  las 70 piezas de suelo con su colisión, tabla con ángulos y nombres propuestos). Hallazgos: 4 escenas
  usan el PNG equivocado y 3 son duplicados; solo 15 de las 70 se usan en el nivel.
