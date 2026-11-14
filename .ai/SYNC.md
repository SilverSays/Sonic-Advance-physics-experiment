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

## Recordatorios para Silv

Cualquier agente: recuérdale esto a Silv cuando se empiece la reorganización de carpetas
(o antes, si la conversación llega a ese tema).

- Decidir qué hacer con las **55 escenas de `suelos/` que el nivel no usa**: dejarlas para
  niveles futuros o archivarlas.
- Decidir qué hacer con los **3 duplicados** (`31`, `34`, `44`): borrarlos o dejarlos como variantes.
  Detalle en `docs/tiles/suelos.md`.

---

## Estado de los scripts de Python

Estado al 2026-11-13. "Verificado" significa probado jugando por Silv.

| Script | Estado | Notas |
|---|---|---|
| `Sonic/personaje.py` | En uso | Parámetros (exports viejos en px/s), vida y muerte, anillos, boost, driver de loops. Mide `step()` con `perf.py` (exports `perf_enabled`, `perf_window`). Desde 2026-11-13 imprime el error si falla el import de la física (antes fallaba en silencio). Varios métodos escriben `velocity` directamente (ver regla de unidades en README). |
| `Sonic/sonic_physics.py` | **Activo desde 2026-11-13, sin probar jugando** | Fase A1 de la SPG (suelo plano, px/frame). Antes se llamaba `sonic_physics_spg.py`. API: `set_ground_speed`, `set_air_speed`, `get_speed`. |
| `Sonic/legacy/sonic_physics_legacy.py` | Retirado, no se importa | Sistema viejo (px/s, delta). Referencia para animaciones, look up/down, etc. |
| `Sonic/perf.py` | En uso, **verificado** (2026-11-13) | `StepProfiler`: total, Python y motor por ventana de N frames. `from godot import OS` funciona. |
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

- **2026-11-13 · sistema viejo (baseline, Fase 0)** · Godot 3.6.1 desde el editor (debug), RTX 3050.
  Prueba libre de unos 30 s (correr, frenar, saltar, anillos); no se registró qué se hizo en cada ventana.
  Reloj: 0.29 us por par de `get_ticks_usec()`. Ventanas de 120 frames, sin contar la primera (arranque):
  total 292–590 us (máx 1581) · python 262–553 us · motor 26–55 us · 1.75–3.54 % del frame.
  Primera ventana: total 376 us, máx 1897 us.
  Lectura: ~90 % del costo es "python", pero esa etiqueta incluye cada llamada a Godot que no sea
  `move_and_slide` (is_on_floor, Input, anim_player, Vector2...). Todavía no se separa lógica pura de costo de frontera.
  Para comparar con el módulo nuevo: repetir una rutina fija (10 s quieto, 10 s corriendo en plano, 10 s frenando y girando).
- **2026-11-13 · módulo nuevo, fase A1** · mismas condiciones (editor, debug). Reloj: 0.21 us por par.
  7 ventanas: total 144–222 us (máx 617) · python 115–189 us · motor 23–35 us · 0.86–1.33 % del frame.
  Lectura: entre 2 y 3 veces menos que la baseline, pero **no es una comparación justa**: A1 hace mucho
  menos (sin salto, roll, look, daño ni la mayoría de animaciones). Sirve como punto de partida de A1, no como
  "el sistema nuevo es más rápido". El "python" sigue siendo ~85 % del total para unas 100 líneas de
  lógica. *Hipótesis:* lo domina el costo de llamar a Godot (Input, is_on_floor, get_floor_normal,
  is_on_wall, Vector2, anim_player, sprite). Falta medir cuánto cuesta una sola llamada Python→Godot.

## Dudas abiertas

1. ~~godot-python y los `.py` sueltos~~ (resuelto 2026-11-13: el editor imprime `Cannot load ... because
   it doesn't expose any class to Godot` al cambiar de pestaña de escena. Le pasaba también al
   `sonic_physics.py` viejo, que funcionaba, así que se considera ruido inofensivo.)
2. **¿Se importa `Engine` desde `godot`?** `OS` sí (verificado 2026-11-13). `Engine` lo usa el
   módulo nuevo; si falla, ahora `personaje.py` imprime el traceback.
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
- 2026-11-13 · Claude · Baseline del sistema viejo registrada (Mediciones). Fase A1 activada:
  `sonic_physics.py` viejo → `Sonic/legacy/sonic_physics_legacy.py`; `sonic_physics_spg.py` → `sonic_physics.py`.
  `personaje.py` ahora imprime el error si falla el import de la física. Pendiente: que Silv pruebe A1 jugando.
  Visto en el log: `[LoopPath] reject speed: 0.0 < 220.0` (5 veces); falta saber si Sonic iba rápido.
- 2026-11-13 · Claude · Silv probó A1 jugando: no gana ni pierde velocidad en pendientes (esperado, aún sin
  slope factor), se para en seco contra paredes, las animaciones se ven bien y `runmax` nunca aparece.
  `[LoopPath] reject speed: 0.0` salía también con el sistema viejo **corriendo**. *Hipótesis (leída en el
  código, sin verificar):* `loop_path.py` lee `body.velocity`, que es un atributo de Python y no una propiedad
  de Godot; el nodo que encuentra LoopPath no lo expone, así que `body.velocity` lanza una excepción, el
  `except` la traga y pone `sp = 0.0`. Explicaría por qué los loops nunca enganchan. Se repite muchas veces
  porque `_process` sondea cada frame dentro de `poll_radius`. Ver TODO.md.
