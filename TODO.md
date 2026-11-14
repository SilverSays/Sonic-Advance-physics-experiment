# To do

Legend: `[ ]` to do · `[x]` done and verified in gameplay · `[-]` done but not verified in
gameplay, or partial result · `[~]` obsolete because of the migration.

## SPG migration phases

### Phase 0 — Baseline measurement
- [x] Measure `SonicPhysics.step()` with the old system (2026-11-13; results in `docs/phases/00-baseline.md`).

### Phase A — SPG speed model (KinematicBody2D stays)
- [x] A1. Flat ground: acceleration, deceleration (with the 0.5 quirk), friction and top speed (S2+ version).
      Verified in gameplay (2026-11-13): stops dead against walls, animations OK, slopes don't change
      speed (expected until A4). Feels much slower than the old system; acceleration feels right
      for its top speed; turning around feels abrupt (left for A5). See `docs/phases/A1-flat-ground.md`.
- [x] A2. Jump and air (2026-11-13). Verified in gameplay: feels almost the same as Sonic Advance 1.
      Pending: confirm the air drag formula and the fall speed cap against the wiki.
      Note: in the SPG Markdown, the air drag formula (`floor(X Speed >> 2) / 256`) looks
      badly converted. Compare it with the wiki.
- [ ] A3. Roll and spindash (roll friction and deceleration, spinrev and its decay).
- [ ] A4. Slopes: slope factor, angle-based landing, slipping or falling at low speed, control lock.
- [x] 240x160 internal resolution like the GBA (2026-11-13, kept).
- [ ] A5. Tweaks toward Sonic Advance, one at a time and tested separately:
      snappier acceleration, smoother flow at high speed, less abrupt turning (DEC),
      removing the jump delay (like Mania). More air control may not be needed (A2 already
      feels like Advance). These are qualitative descriptions (from playing). If numbers are
      needed, measure Advance in an emulator with frame advance.

- [-] Measure the cost of a single Python→Godot call with a microbenchmark (`Sonic/bench.py`,
      `bench_on_start` export). Written 2026-11-13, not run yet.
- [ ] Check that nothing in the level or HUD depends on the old resolution (384x216).

### Phase B — Raycast sensors
- [ ] A/B (floor), C/D (ceiling), E/F (push) sensors per `docs/06-slope-collision.md` in the SPG.
- [ ] Measure the cost of raycasts from Python (every call crosses the Python↔Godot boundary).
- [ ] Check whether going above 60 Hz is needed to avoid tunneling through walls at high speed.
      Doing so means rescaling every constant.

### Reimplement on the new system
- [ ] Full animations (see `docs/legacy-animations.md`), with the guide's variable frame duration.
- [ ] Looking up and down, crouching (with a real hitbox).
- [ ] Damage, knockback, invulnerability, dropped rings, death and respawn.
- [ ] Units rule: everything that writes `velocity` must use `set_ground_speed()` or `set_air_speed()`:
      - [ ] `personaje.py`: `external_boost`, `_start_hit_reaction`, `_start_death`,
            `_respawn`, `_release_spindash`, `_stop_roll`, `detach_path_driver`.
      - [ ] `Sonic/loop_path.py`.
      - [ ] The 4 springs and `items/DashPanel/DashPanel.py`: they call `external_boost` (px/s)
            and, if it doesn't exist, write the player's `velocity` directly.
      - (`badnik_bullet.py` uses its own `velocity`, not the player's: doesn't apply.)
- [ ] Exports in px/frame to tune the constants from the inspector. The old exports are
      in px/s and the new module no longer uses them.

## Project organization (proposal, not applied)
- [ ] Decide the new structure. Proposal in `docs/reorganization.md`.
- [ ] Move files from Godot's FileSystem dock (it updates references in `.tscn` files),
      not from Windows Explorer.
- [ ] After moving, fix by hand what Godot doesn't update: Python imports
      (`from Sonic.sonic_physics ...`) and `"res://..."` strings inside `.py` files.
- [ ] Rename ground pieces by shape (flat, slope, etc.) instead of by number.
      Sheet and table with proposed names in `docs/tiles/ground-pieces.md`. First fix the scenes
      that use the wrong PNG (14↔15, 284↔286, 152→156, 249→294) and the duplicates (31, 34, 44).
- [ ] Decide what to do with the ~634 PNGs in `Sprites/sunset hill/` that no scene uses
      (704 in total, 70 in use).

## Known bugs
- [ ] `items/DroppedRing.tscn` points to `res://rings/__pycache__/ring_idle.tres`, which doesn't exist.
      `__pycache__/` is in `.gitignore`, so it's not in the repo either. Confirmed by Silv:
      dropped rings don't work properly.
- [ ] The old system asked for a `"crouch"` animation that doesn't exist in the AnimationPlayer.
- [ ] Running into a wall on walkable ground doesn't stop Sonic (old system).
      Hypothesis: old `sonic_physics.py`, "Parada seca POR PARED" block: the `continue` when
      is_on_floor() and the ground is walkable skips all wall detection.
- [ ] Crouch hitbox doesn't shrink (the capsule has no extents).
- [ ] `script = null` on the player instance in `items/checkpoint/Node2D.tscn`.
      Hypothesis: that override removes personaje.py in the main scene (usually happens when the
      editor saved without loading the Python plugin). Check the node in the inspector.
      Same with the empty PluginScript on ParallaxLayer2.
- [ ] Loops never attach: `[LoopPath] reject speed: 0.0` even while Sonic is running
      (old and new systems). Confirmed by Silv: loops never worked. Hypothesis for the cause:
      `loop_path.py` `_try_attach` reads `body.velocity`, which is a Python attribute not visible
      from the node LoopPath gets; the exception is swallowed and `sp = 0.0`.
      To verify: print the exception in that `except`. When fixing it, read the speed through the
      physics API (`get_speed`, px/frame) per the units rule.
- [ ] If `LoopPath.drive()` raises, the player is left with no collision (layers at 0) and falls
      through the floor: the `except` in `Personaje._physics_process` doesn't restore the layers.
- [ ] Dying inside a loop: the driver takes priority and `_death_tick` never runs.
- [ ] LoopPath walks the whole tree every frame looking for the player: `player_name_hint` is
      "Personaje" but the node is called KinematicBody2D and isn't in the "Player" group.
- [ ] Inconsistent capitalization: the folder is `Sonic/` but `rings/Area2D.py` says
      `res://sonic/ring.py` in its comment. Doesn't matter on Windows, but paths are
      case-sensitive in an export (PCK).

## Technical debt
- [ ] `except Exception: pass` everywhere hides errors (the new module no longer uses it).
- [ ] Header comments with old paths: `checkpoint.py` says `res://objects/Checkpoint.py`,
      `DashPanel.py` says `res://objects/DashPanel.py`, `rings/Area2D.py` says `res://sonic/ring.py`.
- [ ] Uninitialized state in _ready: _ground_speed, _was_airborne, surface_up_dir, _no_snap_timer
      (stops mattering once the old system is retired).
- [ ] 4 nearly identical spring scripts → one Spring class with an exported direction.
- [ ] Delete `Sonic/surface_physics.py` (unused).
- [ ] `.gitattributes` so `.import` files don't show as modified because of LF/CRLF
      (`main` already has a `.gitattributes`, but only for `addons/`).
- [ ] Code comments and console messages are still in Spanish.

## Not reviewed yet
- [ ] Levels (`suelos/`), badnik_bullet collisions with its own badnik.
- [ ] Checkpoints: the logic exists (`Area2D.tscn` at the root is the checkpoint scene), but
      the level doesn't use it. Confirmed by Silv.

## Archived: untested changes to the old system (obsolete because of the migration)
- [~] Landing without losing speed · boost panel on the ground · loop exit keeps speed ·
      A. rolling on slopes · B. floor-angle · C1/C2 springs · D. air acceleration ·
      E. overspeed · F. rolling uphill · G. spindash.
      Still in the history (commit `22e4b49`). Useful as symptom references for phases A3–A4.
- [x] Sticking to the ground on bumpy downhills (speed-based snap) — old system.
- [x] Ceiling cuts the upward movement — old system.
