# Sonic Advance - Physics Experiment

A 2D Sonic fangame with **Sonic Advance**-style physics, made in Godot 3 with
**Python** instead of GDScript.

Besides the game itself, it's a personal challenge: **seeing how far Python can go
in a fast platformer**, and how much it can be optimized as enemies, interactive
objects and collectibles get added.

> **Status:** prototype. The physics are being rewritten from scratch.
>
> - `main` has the **old** physics system: playable, but with known bugs.
> - The new work lives in the **`feat/fisica-spg`** branch. That's also where the detailed
>   plan (`TODO.md`), the docs (`docs/`) and a log for each phase (`docs/phases/`) are.
> - It gets merged into `main` every time a phase works in actual gameplay.

## Where the project is going

The physics are being rewritten following the
[Sonic Physics Guide](https://info.sonicretro.org/Sonic_Physics_Guide) (SPG), the
reference document on how the classic Sonic games work under the hood. The Markdown
version from [trentbrew/sonic-physics-guide](https://github.com/trentbrew/sonic-physics-guide)
is used as support. It's an automatic conversion, so if a formula looks off, it gets checked against the original wiki.

- **Base:** the values and order of operations of the Genesis Sonic games.
- **Target:** the feel of Sonic Advance (snappier acceleration, more air control,
  less punishment in fast sections). Changes toward Advance are made one at a time
  on top of the guide's base, and each one is tested on its own.

### Why

- **The old system was fixed with patches.** Every bug got its own tweak
  (variable snap, caps, syncing the speed in several places), and those fixes
  clashed with each other. The SPG describes a complete model, proven over
  decades: instead of inventing the physics, I replicate one that already works.
- **Comparable numbers.** Using the same units as the guide (pixels per frame at
  60 Hz) makes it possible to compare every constant 1:1 with it, and to document every
  tweak toward Advance as a change from a known value.
- **Learning the guide.** Implementing it step by step is the way to understand why
  Sonic feels the way he does.
- **The performance challenge.** The guide's raycast sensors require many calls
  into Godot from Python every frame. That's exactly what I want to measure and
  optimize, which is why it's measured from day one.

## Use of AI

This project is developed with the support of an AI (Claude, by Anthropic) as a
**learning companion**. It is not a "vibe-coded" project:

- I decide the direction, the phases and what gets changed.
- The AI explains the Sonic Physics Guide, audits the code, points out problems and
  their causes, and writes parts of the code when I ask it to.
- I review every change and test it in gameplay before calling it done. Anything not
  tested yet is marked as a hypothesis.
- Every phase is documented (what was done, why, and how it was verified) in
  `docs/phases/` on the `feat/fisica-spg` branch.

## Roadmap

| Phase | What it covers | Status |
|---|---|---|
| **0. Baseline measurement** | Measure the per-frame cost of the old physics (Python side and engine side) | Done |
| **A1. Flat ground** | SPG acceleration, deceleration, friction and top speed | Done, verified in gameplay |
| **A2. Jump and air** | Variable jump, air control and drag, gravity | Done, verified in gameplay |
| **A3. Roll and spindash** | Roll friction, spindash charge and release | To do |
| **A4. Slopes** | Slopes speed you up and slow you down, angle-based landing, sliding off walls | To do |
| **A5. Toward Advance** | One-by-one tweaks for the Sonic Advance feel | To do |
| **B. Sensors** | Replace Godot's collision with raycast sensors like the guide's | To do |
| **Reimplement** | Full animations, damage and death, springs, boost panels, loops, looking up and down | To do |
| **Game** | More enemies, objects, collectibles and levels, measuring performance at every step | Future |

During phase A, Godot's collision (`KinematicBody2D`) stays in place while the
speed model is rewritten. That way, if something feels wrong, the cause is the
speed and not the collision. Sensors come in phase B.

There's also a pending reorganization of folders and names, for when phase A is
stable.

### Units rule

Sonic's speed (in px/frame) lives **only** in the physics module. Everything
else (springs, boost panels, loops, damage) changes it through that module, never by writing
`velocity` directly. This caused several bugs in the old system: several places
were storing "the speed" and they drifted out of sync.

## Tech

- **Godot 3.6.1**
- **godot-python** (PythonScript 0.50, Python 3.8), bundled in `addons/pythonscript/`
- Windows. The `.py` and `.tscn` files use tabs.

## Running the project

1. Install Godot 3.6.1. Godot 4 won't work.
2. Clone this repository. For the new work: `git switch feat/fisica-spg`.
3. Open the project folder from the Godot editor.
4. Run the main scene with **Play**.

The main scene is `items/checkpoint/Node2D.tscn` (the test level). On the new
branch, the `[perf]` lines in the console show the per-frame cost of the physics.

## Controls

- **Left / right arrow:** move.
- **Down arrow:** crouch, roll or get ready to spindash.
- **Space:** jump or charge the spindash.

On the `feat/fisica-spg` branch, only running and jumping work for now.
Everything else is disabled on purpose until its phase.

## Main structure

```text
Sonic/       Player: personaje.py, physics module, loops.
items/       Checkpoint, springs, boost panel, dropped ring.
             (items/checkpoint/Node2D.tscn is the test level).
rings/       Collectible ring.
enemies/     Flying enemy and its projectile.
suelos/      Ground pieces (StaticBody2D with a Sunset Hill tile).
Sprites/     Graphics.
background/  Sunset Hill backgrounds.
addons/      Python runtime for Godot (don't touch).
```
