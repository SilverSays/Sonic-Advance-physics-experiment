# res://Sonic/personaje.py
from godot import exposed, export, KinematicBody2D, Vector2, Input, ResourceLoader

# Módulo externo de físicas (tu sonic_physics.py)
try:
	from Sonic.sonic_physics import SonicPhysics
except Exception:
	SonicPhysics = None

# Medición de rendimiento de step() (ver Sonic/perf.py)
try:
	from Sonic.perf import StepProfiler
except Exception:
	import traceback
	traceback.print_exc()
	StepProfiler = None


@exposed
class Personaje(KinematicBody2D):
	# --- boost/panel ---
	boost_lock_default = export(float, default=0.28)

	# --- medición de rendimiento (Sonic/perf.py) ---
	perf_enabled = export(bool, default=True)
	perf_window = export(int, default=120)   # frames por cada línea impresa

	# ----- velocidades -----
	walk_speed = export(float, default=140.0)
	run_speed = export(float, default=1000.0)
	crouch_speed = export(float, default=60.0)

	# ----- física horizontal -----
	accel_ground = export(float, default=4200.0)
	accel_air = export(float, default=2100.0)
	brake = export(float, default=3000.0)
	friction = export(float, default=1200.0)

	# ----- frenado tipo "auto" -----
	brake_decel = export(float, default=6000.0)
	brake_cooldown = export(float, default=0.6)
	brake_inertia_distance = export(float, default=18.0)

	# ----- deceleración al soltar input -----
	release_decel = export(float, default=700.0)

	# ----- run buildup -----
	run_gain_rate = export(float, default=1.0 / 3.0)
	run_decay_rate = export(float, default=1.0 / 1.0)
	run_loss_on_brake = export(float, default=3.0)

	# ----- fases de sprint -----
	sprint1_threshold = export(float, default=0.05)
	sprint2_threshold = export(float, default=0.25)
	sprint_to_run = export(float, default=0.5)
	run_to_max = export(float, default=0.85)
	sprint1_min_time = export(float, default=0.25)
	sprint2_min_time = export(float, default=0.35)

	# ----- pendiente -----
	slope_influence = export(float, default=1.0)
	static_friction_threshold = export(float, default=80.0)

	# ----- vertical / salto -----
	gravity = export(float, default=900.0)
	jump_speed = export(float, default=420.0)
	max_fall_speed = export(float, default=900.0)

	# ----- anim thresholds -----
	run_threshold = export(float, default=200.0)
	break_min_time = export(float, default=0.12)

	# ----- roll -----
	roll_friction = export(float, default=600.0)
	roll_min_speed = export(float, default=40.0)
	roll_min_speed_to_start = export(float, default=120.0)
	roll_cooldown_time = export(float, default=0.12)
	roll_turn_resistance = export(float, default=900.0)
	roll_exit_preserve_time = export(float, default=0.14)

	# ----- pendientes / roll (antes solo por getattr, ahora visibles en el inspector) -----
	slope_ground_boost = export(float, default=0.95)    # gravedad en pendiente corriendo
	slope_roll_boost = export(float, default=1.15)      # gravedad en pendiente rodando cuesta ABAJO
	slope_roll_up_factor = export(float, default=0.5)   # gravedad en pendiente rodando cuesta ARRIBA
	roll_keep_on_slope = export(float, default=0.2)     # |t.y| mínimo para no desenrollar al pararse (0.2 ≈ 12°)

	# ----- sobrevelocidad / aire -----
	overspeed_decel = export(float, default=250.0)      # decaimiento suave si vas más rápido que el objetivo
	air_ctrl_accel = export(float, default=900.0)
	air_ctrl_cap = export(float, default=140.0)         # el input en el aire no empuja por encima de esto

	# ----- spindash -----
	spindash_max_charge = export(int, default=8)
	# FIX(spindash): antes base 220 + 140/toque => 1 toque = 360 px/s (menos que caminar rápido).
	# Ahora 1 toque ~ velocidad de carrera; 8 toques = 1800.
	spindash_charge_power = export(float, default=100.0)
	spindash_base_power = export(float, default=1000.0)
	spindash_max_launch = export(float, default=1800.0)
	spindash_cancel_vel_threshold = export(float, default=6.0)

	# ===== anillos (estallido visual) =====
	dropped_ring_scene_path = export(str, default="res://items/DroppedRing.tscn")
	dropped_ring_count_cap = export(int, default=32)
	dropped_ring_spread = export(float, default=180.0)
	dropped_ring_speed_min = export(float, default=200.0)
	dropped_ring_speed_max = export(float, default=420.0)
	dropped_ring_up_bias = export(float, default=0.2)

	# ===== vidas / muerte / respawn / cam =====
	lives = export(int, default=2)
	respawn_invuln_time = export(float, default=1.5)
	respawn_marker_path = export(str, default="")
	camera_path = export(str, default="")
	death_min_time = export(float, default=1.0)
	death_launch_up = export(float, default=520.0)

	# ===== golpe / invulnerabilidad =====
	hit_anim_speed = export(float, default=1.0)
	hit_invuln_time = export(float, default=1.2)
	hitstun_time = export(float, default=0.40)
	control_lock_time = export(float, default=0.40)
	hit_knockback_x = export(float, default=320.0)
	hit_knockback_y = export(float, default=280.0)
	hit_blink_freq = export(float, default=12.0)

	# ===== (opcional) bits para “casco de loop” por capas 3/4 =====
	loop_left_layer_bit  = export(int, default=3)   # capa 3  -> valor 4
	loop_right_layer_bit = export(int, default=4)   # capa 4  -> valor 8

	# =========================================================
	#                       READY
	# =========================================================
	def _ready(self):
		# ---- flags base ----
		self.is_dead = False
		self.death_timer = 0.0

		self.is_invulnerable = False
		self.invuln_timer = 0.0
		self.hitstun_timer = 0.0
		self.control_lock_timer = 0.0
		self._blink_accum = 0.0

		self.boost_lock_timer = 0.0

		# anillos actuales
		self.ring_count = 0

		# nodos gráficos/colisión
		self.anim_player = None
		self.sprite = None
		try:
			self.anim_player = self.get_node("AnimationPlayer")
		except Exception:
			pass
		try:
			self.sprite = self.get_node("Sprite")
		except Exception:
			pass

		try:
			self.cshape_node = self.get_node("CollisionShape2D")
		except Exception:
			self.cshape_node = None

		# cámara
		self.cam = None
		try:
			cam_path = str(self.camera_path) if self.camera_path is not None else ""
		except Exception:
			cam_path = ""
		if cam_path:
			try:
				self.cam = self.get_node(cam_path)
			except Exception:
				self.cam = None
		else:
			try:
				self.cam = self.get_node("Camera2D")
			except Exception:
				self.cam = None

		# capas/máscaras originales
		try:
			self._orig_collision_layer = self.collision_layer
			self._orig_collision_mask = self.collision_mask
		except Exception:
			self._orig_collision_layer = 1
			self._orig_collision_mask = 1

		# Raycasts “por si acaso”
		self._ensure_ground_rays()
		try:
			self.get_node("RayFront").collision_mask = self._orig_collision_mask
			self.get_node("RayBack").collision_mask = self._orig_collision_mask
		except Exception:
			pass

		# hitbox original (para crouch)
		self.original_extents = None
		self.crouch_extents = None
		self.cshape_original_pos = None
		if self.cshape_node:
			try:
				pos = self.cshape_node.position
				self.cshape_original_pos = Vector2(pos.x, pos.y)
				shape = self.cshape_node.shape
				if hasattr(shape, "extents"):
					e = shape.extents
					self.original_extents = Vector2(e.x, e.y)
					self.crouch_extents = Vector2(e.x, e.y * 0.5)
			except Exception:
				pass

		# respawn inicial
		self.respawn_pos = self.global_position
		try:
			resp_path = str(self.respawn_marker_path) if self.respawn_marker_path is not None else ""
		except Exception:
			resp_path = ""
		if resp_path:
			try:
				m = self.get_node(resp_path)
				self.respawn_pos = m.global_position
			except Exception:
				pass
		self.original_respawn_pos = Vector2(self.respawn_pos.x, self.respawn_pos.y)

		# estado de movimiento
		self.velocity = Vector2()
		self.crouching = False
		self.run_meter = 0.0
		self.run_block_timer = 0.0
		self.last_input_dir = 0

		self.last_run_meter = self.run_meter
		self.sprint1_timer = 0.0
		self.sprint2_timer = 0.0

		# look
		self.look_mode = None
		self.look_timer = 0.0

		# longitudes de anims (si existen)
		self._anim_len = {}
		for name in ("prelook_up", "look_up", "look_down", "standup", "break", "roll",
					 "spin_charge", "spin_idle", "jump", "death", "hit"):
			try:
				a = self.anim_player.get_animation(name)
				self._anim_len[name] = a.length if a else 0.0
			except Exception:
				self._anim_len[name] = 0.0

		# braking
		self.is_braking = False
		self.brake_timer = 0.0
		self.current_brake_decel = self.brake_decel

		# roll
		self.is_rolling = False
		self.roll_dir = 0
		self.roll_cooldown_timer = 0.0
		self.roll_speed = 0.0
		self.roll_exit_preserve_timer = 0.0

		# spindash
		self.is_spindash_charging = False
		self.spindash_charge = 0
		self.spindash_charge_anim_timer = 0.0
		self.last_down_pressed = False

		# rings soltables
		try:
			self.dropped_ring_scene = ResourceLoader.load(self.dropped_ring_scene_path)
		except Exception:
			self.dropped_ring_scene = None

		# anim finished (opcional)
		try:
			self.anim_player.connect("animation_finished", self, "_on_anim_finished")
		except Exception:
			pass

		# buffers para (des)activar colisiones
		self._area_prev_states = {}
		self._shape_prev_states = {}

		# módulo de físicas separado (opcional)
		self.physics = SonicPhysics(self) if SonicPhysics else None
		self._perf = StepProfiler(self.perf_window, "SonicPhysics.step") if (StepProfiler and self.perf_enabled) else None

		# ====== NUEVO: driver externo (LoopPath / rail, etc.) ======
		self._external_driver = None  # si no es None, delegamos el movimiento a ese driver

	# =========================================================
	#              CREACIÓN AUTOMÁTICA DE RAYCASTS
	# =========================================================
	def _ensure_ground_rays(self):
		try:
			from godot import RayCast2D
		except Exception:
			return
		try:
			rf = self.get_node("RayFront")
		except Exception:
			rf = None
		try:
			rb = self.get_node("RayBack")
		except Exception:
			rb = None
		if rf is None:
			try:
				rf = RayCast2D.new()
				rf.name = "RayFront"
				rf.position = Vector2(6, 0)
				rf.cast_to = Vector2(0, 24)
				rf.enabled = True
				self.add_child(rf)
			except Exception:
				pass
		if rb is None:
			try:
				rb = RayCast2D.new()
				rb.name = "RayBack"
				rb.position = Vector2(-6, 0)
				rb.cast_to = Vector2(0, 24)
				rb.enabled = True
				self.add_child(rb)
			except Exception:
				pass

	# =========================================================
	#                    HELPERS / ESTADO
	# =========================================================
	def _sign(self, x):
		if x > 0: return 1
		if x < 0: return -1
		return 0

	def _is_run_or_maxrun(self):
		abs_vx = abs(self.velocity.x)
		if self.run_meter >= self.sprint_to_run and abs_vx >= self.run_threshold:
			return True
		if self.run_meter >= self.run_to_max or abs_vx >= 0.98 * self.run_speed:
			return True
		return False

	def _walk_children(self, node):
		for c in node.get_children():
			yield c
			for cc in self._walk_children(c):
				yield cc

	def _toggle_all_colliders(self, enable):
		if enable:
			try:
				self.set_deferred("collision_layer", self._orig_collision_layer)
				self.set_deferred("collision_mask", self._orig_collision_mask)
			except Exception:
				pass
			for path, (mon, monable) in list(self._area_prev_states.items()):
				try:
					a = self.get_node(path)
					a.set_deferred("monitoring", mon)
					a.set_deferred("monitorable", monable)
				except Exception:
					pass
			self._area_prev_states.clear()
			for path, disabled in list(self._shape_prev_states.items()):
				try:
					s = self.get_node(path)
					s.set_deferred("disabled", disabled)
				except Exception:
					pass
			self._shape_prev_states.clear()
		else:
			try:
				self.set_deferred("collision_layer", 0)
				self.set_deferred("collision_mask", 0)
			except Exception:
				pass
			self._area_prev_states.clear()
			self._shape_prev_states.clear()
			for n in self._walk_children(self):
				try:
					prev = n.disabled
					self._shape_prev_states[str(n.get_path())] = prev
					n.set_deferred("disabled", True)
				except Exception:
					pass
				try:
					mon = n.monitoring
					monable = n.monitorable
					self._area_prev_states[str(n.get_path())] = (mon, monable)
					n.set_deferred("monitoring", False)
					n.set_deferred("monitorable", False)
				except Exception:
					pass

	# =========================================================
	#            INTEGRACIÓN CON LOOP/RIELES (DRIVER)
	# =========================================================
	def attach_path_driver(self, driver):
		"""Llamado por LoopPath: toma control del movimiento (desactiva colisión propia)."""
		self._external_driver = driver
		try:
			self._prev_layer = self.collision_layer
			self._prev_mask = self.collision_mask
			self.set_deferred("collision_layer", 0)
			self.set_deferred("collision_mask", 0)
		except Exception:
			pass
		# cancelar estados que podrían interferir
		self.is_braking = False
		if getattr(self, "is_spindash_charging", False):
			self.is_spindash_charging = False
			self.spindash_charge = 0
			self.spindash_charge_anim_timer = 0.0

	def detach_path_driver(self, driver, out_velocity=None):
		"""Llamado por LoopPath al salir del path: devuelve control y momentum."""
		if self._external_driver != driver:
			return
		self._external_driver = None
		try:
			self.set_deferred("collision_layer", self._orig_collision_layer)
			self.set_deferred("collision_mask", self._orig_collision_mask)
		except Exception:
			pass
		if out_velocity is not None:
			self.velocity = out_velocity
			# FIX: fuerza a recalcular _ground_speed desde la velocidad de salida en el siguiente paso de física
			self._was_airborne = True

	# (opcional) para la solución de “capas” de loops
	def set_loop_collision(self, left=None, right=None):
		"""Activa/desactiva en la MÁSCARA del player la colisión con capas 3/4 (izq/der)."""
		try:
			mask = int(self.collision_mask)
			def bit(b): return 1 << (int(b) - 1)
			L = bit(getattr(self, "loop_left_layer_bit", 3))
			R = bit(getattr(self, "loop_right_layer_bit", 4))
			if left is not None:
				if left:   mask |= L
				else:      mask &= ~L
			if right is not None:
				if right:  mask |= R
				else:      mask &= ~R
			self.set_deferred("collision_mask", mask)
		except Exception:
			pass

	# =========================================================
	#             INTERFAZ USADA POR OTRAS COSAS
	# =========================================================
	def set_respawn_point(self, new_pos):
		try:
			self.respawn_pos = Vector2(new_pos.x, new_pos.y)
		except Exception:
			pass

	def external_boost(self, dirv, speed, lock_time=None, keep_rolling=None):
		"""Impulso externo (dash panel)."""
		try:
			spd = float(speed)
		except Exception:
			spd = speed

		if lock_time is None:
			lock_time = float(getattr(self, "boost_lock_default", 0.28))
		self.boost_lock_timer = max(self.boost_lock_timer, lock_time)

		# cancelar estados que frenarían
		self.is_braking = False
		if getattr(self, "is_spindash_charging", False):
			self.is_spindash_charging = False
			if hasattr(self, "spindash_charge"):
				self.spindash_charge = 0
			self.spindash_charge_anim_timer = 0.0

		# decidir mantener o no roll
		if keep_rolling is None:
			keep_as_roll = bool(getattr(self, "is_rolling", False))
		else:
			keep_as_roll = bool(keep_rolling)

		if keep_as_roll:
			self.is_rolling = True
			# FIX(resorte-roll): antes velocity.x = ±spd aunque dirv fuera vertical,
			# así que un resorte hacia arriba rodando lanzaba también a la derecha.
			if abs(dirv.x) > 0.01:
				self.roll_dir = 1 if dirv.x > 0 else -1
			self.roll_speed = abs(dirv.x * spd)
			self.velocity.x = dirv.x * abs(spd)
			self.velocity.y = dirv.y * abs(spd)
			self._ground_speed = self.velocity.x
			try:
				if self.anim_player and self.anim_player.current_animation != "roll":
					self.anim_player.play("roll")
			except Exception:
				pass
		else:
			if getattr(self, "is_rolling", False):
				self._stop_roll(preserve=True)
				self.is_rolling = False
			self.velocity = Vector2(dirv.x * spd, dirv.y * spd)
			# FIX: sin esto la física del suelo reconstruía la velocidad con el _ground_speed viejo y anulaba el boost
			self._ground_speed = self.velocity.x

		# FIX(resorte-arriba): si el impulso es mayormente hacia arriba, despegar del suelo.
		# Sin esto, en el siguiente frame is_on_floor() seguía True y la física de suelo
		# reconstruía velocity = tangente * _ground_speed (= 0), anulando el salto; además el snap lo volvía a pegar.
		if dirv.y < -0.7:
			self._no_snap_timer = max(float(getattr(self, "_no_snap_timer", 0.0)), 0.2)
			self._was_airborne = True
			self._spring_lift_timer = 0.1

		if hasattr(self, "run_meter"):
			self.run_meter = max(self.run_meter, 1.0)

		if hasattr(self, "roll_exit_preserve_timer"):
			self.roll_exit_preserve_timer = max(self.roll_exit_preserve_timer, 0.18)

		try:
			if hasattr(self, "sprite") and self.sprite:
				self.sprite.flip_h = True if dirv.x > 0 else False
		except Exception:
			pass
		if hasattr(self, "last_input_dir"):
			self.last_input_dir = 1 if dirv.x >= 0 else -1

	# ----- roll helpers (usados por physics) -----
	def _start_roll(self):
		if self.is_rolling:
			return
		if getattr(self, "roll_cooldown_timer", 0.0) > 0.0:
			return
		if abs(self.velocity.x) < self.roll_min_speed_to_start or not self.is_on_floor() or self.run_meter < self.sprint2_threshold:
			return
		self.is_rolling = True
		self.roll_dir = self._sign(self.velocity.x) if abs(self.velocity.x) > 0.1 else (self.last_input_dir or 1)
		self.roll_speed = abs(self.velocity.x)
		try:
			if self.anim_player:
				self.anim_player.play("roll")
		except Exception:
			pass
		self.run_block_timer = self.brake_cooldown
		self.run_meter = 0.0

	def _stop_roll(self, preserve=False):
		if not self.is_rolling:
			return
		self.is_rolling = False
		try:
			self.roll_cooldown_timer = float(self.roll_cooldown_time)
		except Exception:
			self.roll_cooldown_timer = 0.12
		self.velocity.x = self.roll_dir * self.roll_speed
		if preserve:
			try:
				self.roll_exit_preserve_timer = float(self.roll_exit_preserve_time)
			except Exception:
				self.roll_exit_preserve_timer = 0.14

	def _release_spindash(self):
		if self.spindash_charge <= 0:
			self.is_spindash_charging = False
			self.spindash_charge = 0
			return
		launch = self.spindash_base_power + (self.spindash_charge * self.spindash_charge_power)
		if launch > self.spindash_max_launch:
			launch = self.spindash_max_launch
		dir_to_use = self.last_input_dir if self.last_input_dir != 0 else (1 if (self.sprite and self.sprite.flip_h) else -1)
		self.roll_dir = dir_to_use
		self.roll_speed = abs(launch)
		self.velocity.x = self.roll_dir * self.roll_speed
		# FIX(spindash): sin esto _ground_speed seguía ~0 (parado) y FIX(roll-pendiente) podía
		# sobrescribir roll_speed con ese valor en el mismo frame, matando el lanzamiento.
		self._ground_speed = self.velocity.x
		self.is_spindash_charging = False
		self.spindash_charge = 0
		self.spindash_charge_anim_timer = 0.0
		try:
			if self.anim_player:
				self.anim_player.play("roll")
		except Exception:
			pass
		self.is_rolling = True
		self.run_block_timer = self.brake_cooldown
		self.run_meter = 0.0

	def _start_brake(self, play_anim=True):
		should_play_anim = play_anim and self._is_run_or_maxrun()
		if should_play_anim:
			try:
				if self.anim_player:
					self.anim_player.play("break")
			except Exception:
				pass
		anim_len = self._anim_len.get("break", 0.0)
		self.brake_timer = (anim_len if (should_play_anim and anim_len > 0.001) else self.break_min_time)
		self.is_braking = True
		self.run_block_timer = self.brake_cooldown
		self.run_meter = 0.0
		self.sprint1_timer = 0.0
		self.sprint2_timer = 0.0
		v = abs(self.velocity.x)
		s = max(0.0, float(self.brake_inertia_distance))
		if v > 0 and s > 0:
			a_req = (v * v) / (2.0 * s)
			a_req = max(a_req, 50.0)
			self.current_brake_decel = min(a_req, self.brake_decel)
		else:
			self.current_brake_decel = self.brake_decel

	# -------- rings ----------
	def collect_ring(self, amount=1):
		try:
			self.ring_count += int(amount)
		except Exception:
			self.ring_count += 1
		print("[RINGS] collected ->", self.ring_count)

	def take_damage(self, source_pos=None):
		if self.is_invulnerable or getattr(self, "is_dead", False):
			return
		if self.ring_count > 0:
			lost = self.ring_count
			self.ring_count = 0
			print("[RINGS] player hit! dropped rings:", lost)
			self._drop_rings(lost)
			self._start_hit_reaction(source_pos)
		else:
			print("[PLAYER] hit with no rings -> death")
			self._start_death()

	def _drop_rings(self, count):
		import math, random
		if not self.dropped_ring_scene:
			return
		n = min(int(count), int(self.dropped_ring_count_cap))
		parent = self.get_parent()
		if parent is None:
			return
		center = self.global_position
		half = max(1, n)
		for i in range(n):
			try:
				inst = self.dropped_ring_scene.instance()
				parent.add_child(inst)
				inst.global_position = center
				t = (i + 0.5) / half
				angle_deg = (t - 0.5) * self.dropped_ring_spread
				angle_rad = math.radians(angle_deg)
				dir_vec = Vector2(math.cos(angle_rad), -abs(math.sin(angle_rad)))
				dir_vec.y -= self.dropped_ring_up_bias
				if dir_vec.length() == 0:
					dir_vec = Vector2(0, -1)
				dir_vec = dir_vec / dir_vec.length()
				speed = random.uniform(self.dropped_ring_speed_min, self.dropped_ring_speed_max)
				vel = dir_vec * speed
				try:
					inst.setup(initial_velocity=vel, pickup_delay=0.25)
				except Exception:
					try:
						inst.linear_velocity = vel
					except Exception:
						pass
			except Exception:
				pass

	def _start_hit_reaction(self, source_pos=None):
		self.is_braking = False
		if self.is_rolling:
			self._stop_roll(preserve=False)
		if self.is_spindash_charging:
			self.is_spindash_charging = False
			self.spindash_charge = 0
			self.spindash_charge_anim_timer = 0.0
		self.crouching = False
		hit_from_dir = 0
		try:
			if source_pos is not None:
				hit_from_dir = 1 if (source_pos.x > self.global_position.x) else -1
		except Exception:
			hit_from_dir = 0
		if hit_from_dir == 0:
			if abs(self.velocity.x) > 0.1:
				hit_from_dir = self._sign(self.velocity.x)
			else:
				hit_from_dir = (1 if (self.sprite and self.sprite.flip_h) else -1)
		self.velocity.x = -hit_from_dir * float(self.hit_knockback_x)
		self.velocity.y = -abs(float(self.hit_knockback_y))
		self.is_invulnerable = True
		self.invuln_timer = float(self.hit_invuln_time)
		self.hitstun_timer = float(self.hitstun_time)
		self.control_lock_timer = float(self.control_lock_time)
		self._blink_accum = 0.0
		try:
			if self.anim_player:
				self.anim_player.play("hit", -1, float(self.hit_anim_speed))
		except Exception:
			pass

	# -------- muerte / respawn --------
	def _start_death(self):
		if self.is_dead:
			return
		self.lives -= 1
		print("[PLAYER] death -> lives left:", self.lives)
		self.is_braking = False
		if self.is_rolling:
			self._stop_roll(preserve=False)
		if self.is_spindash_charging:
			self.is_spindash_charging = False
			self.spindash_charge = 0
			self.spindash_charge_anim_timer = 0.0
		self.crouching = False
		self.look_mode = None
		self.look_timer = 0.0
		self.run_meter = 0.0
		self.velocity = Vector2(0, -abs(self.death_launch_up))
		self._toggle_all_colliders(False)
		try:
			if self.cam is not None:
				self.cam.current = False
		except Exception:
			pass
		try:
			if self.anim_player:
				self.anim_player.play("death")
		except Exception:
			pass
		self.death_timer = max(self.death_min_time, self._anim_len.get("death", 0.0))
		self.is_dead = True

	def _death_tick(self, delta):
		self.velocity.y += self.gravity * delta
		if self.velocity.y > self.max_fall_speed:
			self.velocity.y = self.max_fall_speed
		self.move_and_slide(self.velocity, Vector2(0, -1))
		self.death_timer -= delta
		if self.death_timer <= 0.0:
			if self.lives > 0:
				self._respawn()
			else:
				self._game_over()

	def _respawn(self):
		self.global_position = Vector2(self.respawn_pos.x, self.respawn_pos.y)
		self.velocity = Vector2(0, 0)
		self.is_dead = False
		self.death_timer = 0.0
		self._toggle_all_colliders(True)
		try:
			if self.cam is not None:
				self.cam.current = True
		except Exception:
			pass
		self.is_invulnerable = True
		self.invuln_timer = float(self.respawn_invuln_time)
		self._blink_accum = 0.0
		try:
			if self.sprite:
				self.sprite.visible = True
		except Exception:
			pass
		try:
			if self.anim_player:
				self.anim_player.play("idle")
		except Exception:
			pass
		print("[PLAYER] respawned at", self.respawn_pos)

	def _game_over(self):
		print("[PLAYER] GAME OVER (no respawn)")
		try:
			self.respawn_pos = Vector2(self.original_respawn_pos.x, self.original_respawn_pos.y)
		except Exception:
			pass
		try:
			self.set_deferred("collision_layer", 0)
			self.set_deferred("collision_mask", 0)
		except Exception:
			pass

	# =========================================================
	#                 BUCLE FÍSICO PRINCIPAL
	# =========================================================
	def _physics_process(self, delta):
		# Si un driver externo (LoopPath) nos está conduciendo, delega y sal.
		if getattr(self, "_external_driver", None):
			try:
				self._external_driver.drive(delta, self)
			except Exception:
				self._external_driver = None
			return

		# Si usas el módulo externo de físicas:
		if self.physics:
			perf = self._perf
			if perf:
				perf.begin()
				try:
					self.physics.step(delta)
				finally:
					perf.end()
			else:
				self.physics.step(delta)
			return

		# (Fallback muy simple si no hay módulo externo)
		if self.is_dead:
			self._death_tick(delta)
			return
		self.velocity.y += self.gravity * delta
		if self.velocity.y > self.max_fall_speed:
			self.velocity.y = self.max_fall_speed
		self.move_and_slide(self.velocity, Vector2(0, -1))

	# ---------------------------------------------------------
	def _on_anim_finished(self, name):
		pass
