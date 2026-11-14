# Folder reorganization proposal (not applied)

It will be applied once phase A is stable. The reference for the ground pieces (swapped
scenes, duplicates, ramps and proposed names) is in [tiles/ground-pieces.md](tiles/ground-pieces.md).

## What's there today and why it's confusing

- The test level is `items/checkpoint/Node2D.tscn`, inside the checkpoint folder.
- The checkpoint scene is `Area2D.tscn`, loose at the root.
- The player is `Sonic/KinematicBody2D.tscn` and the ring is `rings/Area2D.tscn`: the names
  are node types, not what they represent.
- `badnik_bullet.py` is at the root and its scene is in `enemies/`.
- `Sprites/enemies/bg-sunset-hill-zone.png` is a background, not an enemy.
- `suelos/N.tscn` and `Sprites/sunset hill/N.png` are named by slice number.

## Proposed structure

By feature: scene, script and resources together. Names in English (decided).

```text
player/                 sonic.tscn, personaje.py, sonic_physics.py, perf.py, bench.py, legacy/
objects/
  checkpoint/           checkpoint.tscn, checkpoint.py
  springs/              spring_up/down/left/right.tscn (+ a single Spring class later)
  dash_panel/
  rings/                ring.tscn, ring.py, dropped_ring.tscn, dropped_ring.py
  loop_path/            loop_path.tscn, loop_path.py
enemies/badnik_flyer/   badnik_flyer.tscn/.py, badnik_bullet.tscn/.py
levels/
  test_level.tscn
  sunset_hill/tiles/    ground pieces named by shape
Sprites/                stays organized by type; "sunset hill" becomes sunset_hill;
                        the background moves to background/
background/, docs/, addons/   unchanged
```

## Still to decide

- What to do with the 55 scenes in `suelos/` that the level doesn't use: keep or archive them.
- What to do with the 3 duplicates (`31`, `34`, `44`): delete them or keep them as variants.

## Risks and how to do it

- Godot 3 identifies everything by its `res://` path. Files must be moved from the editor's
  FileSystem dock, which updates the references inside `.tscn` and `.tres` files.
- Godot does **not** update Python imports (`from Sonic.sonic_physics import ...`) or the
  `"res://..."` strings inside `.py` files (`personaje.py` → `res://items/DroppedRing.tscn`,
  `badnik_flyer.py` → `res://enemies/badnik_bullet.tscn`). Those are fixed by hand.
- Folders imported from Python need valid names: lowercase, no spaces.
- One commit before reorganizing and another right after, without mixing in physics changes.
