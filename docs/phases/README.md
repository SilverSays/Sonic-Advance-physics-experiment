# Phase log

One file per phase of the migration to the Sonic Physics Guide (SPG): what was done,
which decisions were made and why, how it was verified in gameplay, and what it costs in
performance. The commits listed are on the `feat/fisica-spg` branch.

| Phase | File | Status |
|---|---|---|
| 0. Baseline measurement | [00-baseline.md](00-baseline.md) | Done |
| A1. Flat ground | [A1-flat-ground.md](A1-flat-ground.md) | Done, verified in gameplay |
| A2. Jump and air | [A2-jump-and-air.md](A2-jump-and-air.md) | Done, verified in gameplay |
| Python vs Godot microbenchmark | (in progress, documented once there are results) | In progress |
| A3. Roll and spindash | — | To do |

Notes on the measurements:
- All taken from the Godot 3.6.1 editor (debug mode), on an RTX 3050.
- `[perf]` measures `SonicPhysics.step()` in windows of 120 frames. "engine" is only
  `move_and_slide`; "python" is everything else, **including** the other calls into Godot
  (`Input`, `is_on_floor`, `Vector2`...).
- A measurement is only compared with another one if the gameplay routine is similar.
