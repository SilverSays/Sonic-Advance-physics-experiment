# Sonic Advance - Physics Experiment

Experimento temprano para recrear y probar el movimiento de Sonic en 2D,
inspirado en **Sonic Advance**. El objetivo actual es investigar la sensación
de movimiento, la aceleración y la interacción con superficies, no presentar
todavía un juego terminado.

> **Estado:** prototipo en desarrollo. La física y las escenas cambian con
> frecuencia y pueden contener errores.

## Qué incluye actualmente

- Movimiento horizontal con aceleración, frenado, fricción y velocidad máxima.
- Salto, caída y control en el aire.
- Movimiento sobre pendientes y transiciones a superficies inclinadas.
- Rodar y cargar/lanzar un spindash.
- Anillos que se dispersan al recibir daño.
- Checkpoints y respawn con invulnerabilidad temporal.
- Resortes, paneles de impulso, loops y un enemigo volador con proyectiles.
- Varias escenas de suelo para probar diferentes formas y pendientes.

## Tecnologías

- **Godot 3.x**
- **Python mediante el módulo Godot Python incluido en el proyecto**
- Escenas `.tscn` y scripts Python

El proyecto conserva el runtime de Python dentro de
`addons/pythonscript/`, por lo que la configuración depende de esta versión
de Godot y de ese módulo.

## Ejecutar el proyecto

1. Instala una versión compatible de Godot 3.x.
2. Clona este repositorio.
3. Abre la carpeta del proyecto desde el editor de Godot.
4. Ejecuta la escena principal con **Play**.

La escena principal configurada actualmente es
`items/checkpoint/Node2D.tscn`. Si el proyecto no inicia, revisa que Godot
pueda cargar el módulo de Python incluido y que estés usando Godot 3.x, no
Godot 4.

## Controles

Los controles pueden cambiar mientras se desarrolla el prototipo. La
configuración actual usa:

- **Flecha izquierda / derecha:** moverse.
- **Flecha abajo:** agacharse, rodar o preparar el spindash.
- **Espacio:** saltar; también carga el spindash cuando corresponde.

## Estructura principal

```text
Sonic/       Física y comportamiento del personaje.
items/       Checkpoints, resortes, paneles y anillos.
enemies/     Enemigos y proyectiles.
suelos/      Escenas de superficies para pruebas.
Sprites/     Recursos visuales.
addons/      Runtime de Python para Godot.
```

## Próximos pasos

- Ajustar la física para que sea consistente en más tipos de superficie.
- Mejorar las escenas de prueba y la presentación del nivel.
- Completar enemigos, cámara, interfaz y flujo de juego.
- Documentar una versión estable de los controles y requisitos.

Este repositorio es un espacio de experimentación. Las contribuciones,
reportes de errores y sugerencias son bienvenidos.
