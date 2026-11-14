# Animations in the old system (reference for reimplementing them)

The code that picked animations lived in the old physics module, now kept as
`Sonic/legacy/sonic_physics_legacy.py` (section "Animaciones / flip"). It's also in the
history:

    git show 22e4b49:Sonic/sonic_physics.py

The animations themselves **are not lost**: they're in the `AnimationPlayer` of
`Sonic/KinematicBody2D.tscn`. What was lost when the module was replaced is the logic that
decides which one to play. This file summarizes it.

## Animations in the AnimationPlayer (19)

RESET, idle, walk, sprint_start, sprint_mid, run, runmax, break, jump, fall, roll,
spin_charge, spin_idle, look_up, prelook_up, look_down, standup, hit, death

## Priority of the main animation (old system)

Evaluated in this order; the first one that applies wins:

1. `hit` if `hitstun_timer > 0`
2. `roll` if `is_rolling`
3. `break` if `is_braking`
4. `break` if on the ground, the input goes against the sign of `_ground_speed`, and Sonic is
   in run or runmax (`_is_run_or_maxrun()`)
5. Look states (see below): `look_up`, `standup`; nothing changes during `look_down`
6. On the ground:
   - `crouch` if `crouching` — **bug: there's no "crouch" animation in the AnimationPlayer**
   - if `|gs| > 0.1` (px/s), depending on `run_meter` and speed:
     - `runmax` if `run_meter >= run_to_max` or `|gs| >= 0.98 * run_speed`
     - `run` if `|gs| >= run_threshold` and `run_meter >= sprint_to_run`
     - `sprint_mid` / `sprint_start` depending on `sprint2_threshold` / `sprint1_threshold`
       and their timers (note: `sprint1_timer` and `sprint2_timer` never increase, see TODO.md)
     - `walk` otherwise
   - `idle` if `|gs| <= 0.1`
7. In the air: `jump` if `velocity.y < 0`, otherwise `fall`

Animations triggered outside that priority:
- `jump` when jumping
- `spin_charge` while charging the spindash, `spin_idle` while holding it
- `roll` when starting to roll, when releasing the spindash, and in `external_boost` with roll
- `hit` and `death` from `personaje.py`

## Looking up / down (`look_mode` state machine)

Only with `|gs| < 1` on walkable ground.

- Down just pressed → `look_down` (state `look_down_playing` while the animation lasts,
  then `look_down_done`)
- Down released → `standup` (state `standup_wait`) → `None`
- Up held → `prelook_up` (state `wait_prelook_up`) → `look_up` (state `look_up`)
- Up released → `standup` → `None`
- `look_timer` counted down with `delta` and used `_anim_len` (the length of each animation,
  computed in `personaje._ready`)

## Sprite flip

By the sign of `_ground_speed`: `> 0.1` → `sprite.flip_h = True` (faces right),
`< -0.1` → `False`. The base sprite faces left.

## Other visual effects in the old module

- Invulnerability blinking: `sprite.visible` toggles with `_blink_accum * hit_blink_freq`
- Crouch hitbox: changes `cshape_node.shape.extents` (TODO.md: the capsule has no extents,
  so it didn't work)

## When reimplementing

- The old thresholds are in px/s; the new module uses px/frame (divide by 60).
- The guide has its own rules (`docs/21-animations.md` in the SPG repo): idle only when
  gs == 0 exactly, walk at any gs, run at |gs| >= 6, braking when turning at |gs| >= 4, and
  each walk/run frame lasts floor(max(0, 8 - |gs|)) frames.
