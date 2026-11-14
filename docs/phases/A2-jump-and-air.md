# Phase A2 — Jump and air

**Date:** 2026-11-13 · **Commits:** `450e69d` (code), `13356f6` (results)

## What was done

Jumping and air movement were added to `Sonic/sonic_physics.py`, following the SPG's
"Jumping", "Midair" and "Air State" sections.

| Constant | Value (px/frame) | What it does |
|---|---|---|
| `JMP` | 6.5 | Jump force, along the ground normal |
| `JMP_RELEASE` | −4 | When the button is released while rising, vertical speed is capped at this |
| `AIR_ACC` | 0.09375 | Air acceleration (twice the ground value) |
| `GRV` | 0.21875 | Gravity |
| Air drag | ~1/32 of `xsp` per frame | Only near the apex (−4 < `ysp` < 0) |

## Decisions and why

- **The guide's order of operations:** in the air, variable jump → input → air drag →
  move → gravity. Applying gravity after moving is what gives the exact jump height.
- **Jump delay:** on the frame of the jump, Sonic doesn't move, as on the Genesis. Sonic Mania
  removed it. It stays as an option (`JUMP_DELAY`) in case it's tweaked in A5.
- **Jump along the normal:** it's added to the speed Sonic already had. On flat ground it's
  simply upward.
- **Air drag:** the guide's Markdown gives `floor(X Speed >> 2) / 256`, which looks badly
  converted. `floor(xsp * 8) / 256` is used instead (equivalent to shifting the subpixels by 5
  bits). It's a hypothesis pending confirmation against the original wiki.
- **Air top speed:** same as on the ground, input doesn't accelerate above 6 but doesn't cut
  the speed either. It's not confirmed whether Sonic 1/2 capped it in the air.
- **16 px/frame fall cap:** provisional; the guide only lists it for Sonic CD.

By the numbers (not measured): a full jump reaches ~100 px in 61 frames; releasing right
away, ~39 px in 38 frames.

## Verified in gameplay

Routine: 5 s running, short jump on a downhill slope, 5 s running, short jump, long jump.

- The jump "feels great": good mobility and air resistance.
- Compared directly with Sonic Advance 1: **almost identical**.
- Short and long jumps are easy to tell apart.
- The jump delay isn't noticeable.

**What this changes in the plan:** the assumption was that Advance's air control was more
forgiving than Genesis', but with the exact Genesis values it already feels like Advance.
The "more air control" tweak planned for A5 may not be needed.

## Performance

| | A1+A2 (routine with jumps) | A1 (running only) |
|---|---|---|
| Total `step()` | 181–269 µs | 144–222 µs |
| "python" | 155–239 µs | 115–189 µs |
| Engine | 20–35 µs | 23–35 µs |

A2 added about 50 µs per frame. What's new and runs every frame is small: two more calls to
`Input` and the air branch. Hypothesis: if those two calls explain a good part of the
difference, each call from Python into Godot would cost tens of µs. The microbenchmark
(`Sonic/bench.py`) was written to check this.
