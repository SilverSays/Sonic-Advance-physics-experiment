# Phase 0 — Baseline of the old system

**Date:** 2026-11-13 · **Commits:** `bfb5a04` (measurement), `1ce3035` (results)

## What was done

- `Sonic/perf.py`: the `StepProfiler` class. Every frame it measures the cost of
  `SonicPhysics.step()` and splits it into "engine" (the `move_and_slide` call) and "python"
  (everything else). It accumulates 120 frames and prints a single line, because a `print`
  every frame would cost more than what's being measured.
- On startup it calibrates how much the clock itself costs (`OS.get_ticks_usec()`).
- `personaje.py`: `perf_enabled` and `perf_window` exports, and the measurement around `step()`.

## Why before rewriting

Once the physics module is replaced, the old system's reference is gone. Without it,
"the new system is faster" can be neither claimed nor refuted.

## Result

Free routine of about 30 s (running, braking, jumping, rings). The clock costs 0.29 µs per pair.

| | Per 120-frame window | Worst single frame |
|---|---|---|
| Total `step()` | 292–590 µs | 1581 µs |
| "python" | 262–553 µs (~90 %) | 1516 µs |
| Engine | 26–55 µs | — |
| % of the frame (16.7 ms) | 1.75–3.54 % | ~9.5 % |

## Reading

- Almost all the cost is "python", but that label includes every call into Godot other than
  `move_and_slide`. This measurement can't separate the logic from the cost of crossing from
  Python into Godot. The microbenchmark was written for that.
- What was done in each window wasn't recorded; from A1 on, fixed routines are used.

## Side finding

Loops (`LoopPath`) never attach: `[LoopPath] reject speed: 0.0` even while running.
Silv confirmed they never worked. Hypothesis (unverified): `loop_path.py` reads
`body.velocity`, which isn't visible from the node it gets, and the `except` turns the error
into a speed of 0. It's in `TODO.md` for when loops are reimplemented.
