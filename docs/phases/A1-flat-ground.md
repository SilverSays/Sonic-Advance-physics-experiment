# Phase A1 — Flat ground

**Date:** 2026-11-13 · **Commits:** `bfb5a04` (module written), `1ce3035` (enabled),
`9482096` (results), `b57003d` (resolution test)

## What was done

`Sonic/sonic_physics.py` was rewritten from scratch following the SPG's "Running" section.
The old system moved to `Sonic/legacy/sonic_physics_legacy.py` (no longer imported) and its
animation logic was documented in `docs/legacy-animations.md`.

| Constant | Value (px/frame) | What it does |
|---|---|---|
| `ACC` | 0.046875 | Acceleration while holding a direction |
| `DEC` | 0.5 | Braking while holding against the movement |
| `FRC` | 0.046875 | Friction with no input |
| `TOP` | 6 | Top speed from input |

## Decisions and why

- **Units in px/frame at 60 Hz, no `delta`:** same as the guide, so every constant can be
  compared 1:1 and the tweaks toward Advance can be documented as changes from a known value.
  In Godot 3, `_physics_process` already runs at a fixed step, so `delta` added nothing.
- **Units rule:** the speed (`gs`, `xsp`, `ysp`) lives only in the physics module. The rest of
  the code changes it through `set_ground_speed()` / `set_air_speed()`. The old system had
  several places storing "the speed" and they drifted out of sync.
- **Sonic 2-style top speed:** above `TOP`, input stops accelerating but doesn't cut the speed
  down. That way you don't lose the speed from a spring or a ramp by holding the arrow.
- **Deceleration quirk:** when braking crosses zero, the speed jumps to ±0.5 in the opposite
  direction. That's what the original game does.
- **Walls:** if there's a wall in the direction of movement, the speed goes to 0.
- **`KinematicBody2D` stays:** raycast sensors are phase B. Changing the speed and the
  collision at the same time would make it impossible to tell which one causes a problem.
- `personaje.py` prints the error if importing the physics fails (before, Sonic would fall
  with no control and no message).

## Verified in gameplay

- Slopes don't change the speed: expected, the slope factor is phase A4.
- Stops dead against a wall.
- Animations are correct; `runmax` never shows up (it needs 10 px/frame and the top is 6).
- **Feel:** much slower than the old system (top speed 360 px/s vs ~1000 px/s). Acceleration
  feels right for that top speed. Turning around feels abrupt: left for phase A5, since it's
  the Genesis value.

## Resolution test

At 384×216 you see 1.6 times more of the world horizontally than on a GBA (240×160), so at
the same speed Sonic looks slower. It was changed to 240×160 (960×640 window). Result: it
helps the sense of speed a bit, without being a big difference. **Kept.**

## Performance

Routine: holding right until the wall at the end. Clock: 0.21 µs per pair.

| | A1 | Baseline (old system) |
|---|---|---|
| Total `step()` | 144–222 µs | 292–590 µs |
| "python" | 115–189 µs | 262–553 µs |
| Engine | 23–35 µs | 26–55 µs |

**Not a fair comparison:** A1 does much less (no jump, roll, damage or most animations).
It's a starting point, not proof that the new system is faster.
