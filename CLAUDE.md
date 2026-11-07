# Sonic Advance (fangame 2D)

## Stack
- Godot 3.6.1 + godot-python (Python 3.8). Scripts en .py, no GDScript.
- Windows. Los .tscn y los .py usan tabuladores.

## Cómo trabajar conmigo
- Actúa como auditor: señala problemas y explica la causa antes de proponer cambios.
- No edites archivos sin que yo lo pida.
- Marca como hipótesis lo que no puedas verificar sin ejecutar el juego.
- Un cambio por síntoma, para poder probar cada uno por separado.

## Arquitectura
- Personaje: KinematicBody2D, movimiento con move_and_slide_with_snap (sin sensores).
- Sonic/personaje.py: parámetros, vida/muerte, anillos, boost externo, driver de loops.
- Sonic/sonic_physics.py: SonicPhysics.step(delta), toda la lógica de movimiento.
- Sonic/loop_path.py: loops por Path2D; toma el control con attach/detach_path_driver.
- En suelo, _ground_speed es la fuente de verdad: velocity = tangente * gs.
- surface_physics.py y RayFront/RayBack no se usan (intento anterior).

## No tocar
- .import/ y __pycache__/ (se regeneran).
- addons/pythonscript (binarios de la extensión).

## Pendientes
Están en TODO.md.
