# res://Sonic/sonic_physics.py
from godot import Vector2, Input
import math
import traceback

class SonicPhysics:
	def __init__(self, character):
		self.c = character

	# ---------------------- Helpers de pendiente ----------------------
	def _slope_vectors(self):
		c = self.c
		UP = Vector2(0, -1)

		# límites para piso normal
		max_deg = float(getattr(c, "max_walk_slope_deg", 65.0))
		cos_limit = math.cos(math.radians(max_deg))

		# parámetros de wall-run
		wr_enabled   = bool(getattr(c, "wall_run_enabled", True))
		wr_min_speed = float(getattr(c, "wall_run_min_speed", 260.0))
		wr_max_deg   = float(getattr(c, "wall_run_max_angle_deg", 90.0))
		wr_step_max  = float(getattr(c, "wall_run_angle_step_max_deg", 35.0))

		walkable = False
		n = UP

		try:
			if c.is_on_floor():
				n = c.get_floor_normal()
				if n.length() > 1e-6:
					n = n.normalized()
					# piso normal
					walkable = (n.dot(UP) >= cos_limit)

					# --- extensión: wall-run por transición suave desde curva ---
					if (not walkable) and wr_enabled:
						# velocidad tangencial actual
						try:
							prev_n = getattr(c, "surface_up_dir", UP)
							dotp = max(-1.0, min(1.0, prev_n.dot(n)))
							angle_step = math.degrees(math.acos(dotp))
						except Exception:
							angle_step = 180.0

						gs = getattr(c, "_ground_speed", self._gs_from_velocity(c.velocity, Vector2(1, 0)))
						enough_speed = abs(gs) >= wr_min_speed
						within_step  = angle_step <= wr_step_max
						within_max   = (n.dot(UP) >= math.cos(math.radians(wr_max_deg)))

						# Solo si vienes pegado a una superficie (transición suave + velocidad)
						if enough_speed and within_step and within_max:
							walkable = True
				else:
					n = UP
			else:
				n = getattr(c, "surface_up_dir", UP)
				if n.length() <= 1e-6:
					n = UP
		except Exception:
			n = getattr(c, "surface_up_dir", UP)
			if n.length() <= 1e-6:
				n = UP

		if walkable:
			t = Vector2(-n.y, n.x)  # tangente hacia la derecha en el plano de la superficie
		else:
			n = UP
			t = Vector2(1, 0)

		c._walkable_floor_flag = walkable
		return n, t

	def _gs_from_velocity(self, vel, t):
		return vel.x * t.x + vel.y * t.y

	def _snap_length(self, delta):
		"""Alcance del snap al suelo. Crece con la velocidad (estilo Sonic clásico):
		a 1000 px/s se mueve ~17 px por frame, así que 6 px fijos pierden el suelo en cualquier bache."""
		c = self.c
		base = float(getattr(c, "floor_snap_len", 6.0))
		top = float(getattr(c, "floor_snap_max", 20.0))
		gs = abs(float(getattr(c, "_ground_speed", 0.0)))
		return max(base, min(gs * delta + 4.0, top))

	def _apply_adv3_slope_on_ground(self, delta: float):
		c = self.c
		if not c.is_on_floor() or not getattr(c, "_walkable_floor_flag", True):
			return
		n, t = self._slope_vectors()

		sgb = float(getattr(c, "slope_ground_boost", 0.95))
		srb = float(getattr(c, "slope_roll_boost",   1.15))
		sf  = (srb if getattr(c, "is_rolling", False) else sgb)

		gs = getattr(c, "_ground_speed", None)
		if gs is None:
			gs = self._gs_from_velocity(c.velocity, t)

		# FIX(roll-subida): rodando cuesta ARRIBA la pendiente frena menos que lo que acelera cuesta abajo
		# (como en los Sonic clásicos). Antes el mismo factor 1.15 + roll_friction frenaban de golpe.
		if getattr(c, "is_rolling", False) and (t.y * gs) < 0.0:
			sf = float(getattr(c, "slope_roll_up_factor", 0.5))

		# gravedad proyectada a lo largo de la pendiente
		gs += c.gravity * t.y * sf * delta

		# reconstruir velocidad mundial SOLO en piso
		c.velocity = t * gs
		c.surface_up_dir = n
		c._ground_speed = gs

	# --------------------------- STEP ---------------------------
	def step(self, delta: float):
		c = self.c

		# muerte / respawn
		if getattr(c, "is_dead", False):
			c._death_tick(delta)
			return

		# ---------- timers ----------
		if c.invuln_timer > 0.0:
			c.invuln_timer -= delta
			if c.invuln_timer <= 0.0:
				c.invuln_timer = 0.0
				c.is_invulnerable = False
				c._blink_accum = 0.0
				try: c.sprite.visible = True
				except Exception: pass

		c.boost_lock_timer   = max(0.0, c.boost_lock_timer   - delta)
		c._spring_lift_timer = max(0.0, getattr(c, "_spring_lift_timer", 0.0) - delta)
		c.hitstun_timer      = max(0.0, c.hitstun_timer      - delta)
		c.control_lock_timer = max(0.0, c.control_lock_timer - delta)

		if c.is_invulnerable:
			c._blink_accum += delta
			try:
				c.sprite.visible = ((int(c._blink_accum * c.hit_blink_freq) & 1) == 0)
			except Exception: pass

		c.run_block_timer          = max(0.0, c.run_block_timer - delta)
		c.roll_cooldown_timer      = max(0.0, c.roll_cooldown_timer - delta)
		c.roll_exit_preserve_timer = max(0.0, c.roll_exit_preserve_timer - delta)
		c.spindash_charge_anim_timer = max(0.0, c.spindash_charge_anim_timer - delta)

		# ---------------- INPUT ----------------
		input_dir = 0
		if c.control_lock_timer <= 0.0 and c.hitstun_timer <= 0.0:
			if Input.is_action_pressed("ui_right"): input_dir += 1
			if Input.is_action_pressed("ui_left"):  input_dir -= 1

		n, t = self._slope_vectors()

		# --- FIX: mantener _ground_speed sincronizada con la velocidad real ---
		# Antes _ground_speed quedaba "congelada" en el aire / tras golpe / tras loop,
		# y al aterrizar se reconstruía la velocidad con el valor viejo (velocity = t * gs).
		on_ground_now = (c.is_on_floor()
						 and getattr(c, "_walkable_floor_flag", True)
						 and c.hitstun_timer <= 0.0)
		if on_ground_now:
			if getattr(c, "_was_airborne", False):
				# aterrizaje: proyecta la velocidad real sobre la tangente del suelo
				# (en bajada conserva la componente vertical de la caída; en plano = velocity.x)
				c._ground_speed = c.velocity.x * t.x + c.velocity.y * t.y
				c._was_airborne = False
				if c.is_rolling and abs(c._ground_speed) > 0.1:
					c.roll_speed = abs(c._ground_speed)
					c.roll_dir = c._sign(c._ground_speed)
		else:
			c._ground_speed = c.velocity.x
			c._was_airborne = True
			if c.is_rolling:
				# en bola, en el aire se conserva el momentum (sin fricción de roll)
				c.roll_speed = abs(c.velocity.x)
				if abs(c.velocity.x) > 0.1:
					c.roll_dir = c._sign(c.velocity.x)

		gs_now = getattr(c, "_ground_speed", self._gs_from_velocity(c.velocity, t))

		if c.boost_lock_timer > 0.0:
			if input_dir != 0 and c._sign(gs_now) != 0 and input_dir != c._sign(gs_now):
				input_dir = 0

		# freno inverso en piso caminable
		inverse_pressed = (input_dir != 0 and c._sign(gs_now) != 0 and c._sign(gs_now) != input_dir)
		if inverse_pressed and c.is_on_floor() and getattr(c, "_walkable_floor_flag", True) and not c.is_braking and not c.is_rolling:
			if c._is_run_or_maxrun():
				c._start_brake(play_anim=True)

		# target speed
		target_speed = (c.crouching and c.crouch_speed) or (c.walk_speed + (c.run_speed - c.walk_speed) * c.run_meter)

		# ---------------- Spindash ----------------
		idle_enough  = abs(gs_now) < 1.0 and c.is_on_floor() and getattr(c, "_walkable_floor_flag", True)
		down_pressed = (c.control_lock_timer <= 0.0) and Input.is_action_pressed("ui_down")
		jump_consumed_for_spindash = False

		if down_pressed and idle_enough and not c.is_rolling and c.hitstun_timer <= 0.0:
			if Input.is_action_just_pressed("jump") or Input.is_action_just_pressed("ui_accept"):
				jump_consumed_for_spindash = True
				c.is_spindash_charging = True
				c.spindash_charge = min(c.spindash_charge + 1, c.spindash_max_charge)
				try: c.anim_player.play("spin_charge")
				except Exception: pass
				c.spindash_charge_anim_timer = c._anim_len.get("spin_charge", 0.0)
			if c.is_spindash_charging and c.spindash_charge > 0 and c.spindash_charge_anim_timer <= 0.0:
				try:
					if c.anim_player.current_animation != "spin_idle":
						c.anim_player.play("spin_idle")
				except Exception: pass
		else:
			if c.is_spindash_charging and not down_pressed:
				c._release_spindash()
			elif c.is_spindash_charging:
				moved = Input.is_action_pressed("ui_left") or Input.is_action_pressed("ui_right")
				vel_too_high = abs(gs_now) > float(c.spindash_cancel_vel_threshold)
				if moved or vel_too_high or not c.is_on_floor():
					c.is_spindash_charging = False
					c.spindash_charge = 0
					c.spindash_charge_anim_timer = 0.0

		if c.is_spindash_charging or (down_pressed and idle_enough and c.look_mode in ("look_down_playing","look_down_done")):
			input_dir = 0

		# ------------- Control de ground speed (solo piso caminable) -------------
		gs = getattr(c, "_ground_speed", self._gs_from_velocity(c.velocity, t))
		desired_gs = input_dir * target_speed

		if c.boost_lock_timer > 0.0 and input_dir != 0 and c._sign(gs) == input_dir:
			if abs(gs) > abs(desired_gs):
				desired_gs = gs
		if c.boost_lock_timer > 0.0:
			inverse_pressed = False

		# ROLL
		if Input.is_action_just_pressed("ui_down") and not idle_enough and c.is_on_floor() and getattr(c, "_walkable_floor_flag", True):
			if not c.is_rolling and c.roll_cooldown_timer <= 0.0 and c.run_meter >= c.sprint2_threshold:
				c._start_roll()

		# FIX: la fricción/giro de roll solo aplica con el suelo bajo los pies (antes también en el aire)
		if c.is_rolling and on_ground_now:
			# FIX(roll-pendiente): _ground_speed ya trae la gravedad de pendiente del frame anterior
			# (_apply_adv3_slope_on_ground). Antes roll_speed lo pisaba y se perdía esa ganancia/pérdida.
			if abs(gs) > 0.1:
				c.roll_speed = abs(gs)
				c.roll_dir = c._sign(gs)
			if input_dir != 0 and input_dir != c.roll_dir:
				turn_dec = c.roll_turn_resistance * delta
				if c.roll_speed <= turn_dec:
					c.roll_speed = 0.0
					c.roll_dir = input_dir
				else:
					c.roll_speed -= turn_dec
			gs = c.roll_dir * c.roll_speed

			try:
				g_tan = c.gravity * t.y
				helps = (g_tan * c.roll_dir) > 0
			except Exception:
				helps = False

			if c.roll_speed != 0 and not helps:
				dec = c.roll_friction * delta
				if c.roll_speed <= dec:
					c.roll_speed = 0.0
					gs = 0.0
				else:
					c.roll_speed -= dec
					gs = c.roll_dir * c.roll_speed

			# FIX(roll-subida): en pendiente no desenrollar al llegar a ~0; la gravedad le da la vuelta
			# y sigue rodando cuesta abajo. Solo se desenrolla en suelo casi plano.
			on_slope = abs(t.y) > float(getattr(c, "roll_keep_on_slope", 0.2))
			if c.roll_speed < c.roll_min_speed and not on_slope:
				c._stop_roll()

		# NORMAL (en piso caminable)
		elif c.is_on_floor() and getattr(c, "_walkable_floor_flag", True):
			if c.is_braking:
				c.brake_timer -= delta
				dec = c.current_brake_decel * delta
				if abs(gs) <= dec: gs = 0.0
				else:             gs -= c._sign(gs) * dec
				if c.brake_timer <= 0 and abs(gs) <= 1.0:
					c.is_braking = False
					c.brake_timer = 0.0
					c.current_brake_decel = c.brake_decel
			else:
				if input_dir != 0:
					if c.run_block_timer <= 0 and not c.crouching:
						if c._sign(gs) == input_dir or abs(gs) < 1.0:
							c.run_meter += c.run_gain_rate * delta
						else:
							c.run_meter -= c.run_loss_on_brake * delta
						c.run_meter = max(0.0, min(1.0, c.run_meter))

					accel = c.accel_ground
					if c._sign(gs) != c._sign(desired_gs) and abs(gs) > 0.1:
						max_step = c.brake_decel * delta if c._is_run_or_maxrun() else accel * delta
					else:
						max_step = accel * delta

					# FIX(sobrevelocidad): si vas en la dirección del input pero MÁS rápido que el objetivo
					# (aterrizaje, bajada, spindash, boost), antes se recortaba a accel_ground (4200 px/s²) => frenazo seco.
					# Ahora solo decae suavemente con overspeed_decel.
					if c._sign(gs) == input_dir and abs(gs) > abs(desired_gs):
						dec = float(getattr(c, "overspeed_decel", 250.0)) * delta
						gs -= c._sign(gs) * min(dec, abs(gs) - abs(desired_gs))
					else:
						diff = desired_gs - gs
						if abs(diff) <= max_step: gs = desired_gs
						else:                     gs += c._sign(diff) * max_step
				else:
					# NO frenar si acabas de salir de roll con preserve=True
					if getattr(c, "roll_exit_preserve_timer", 0.0) <= 0.0:
						dec = c.release_decel * delta
						if abs(gs) <= dec: gs = 0.0
						else:              gs -= c._sign(gs) * dec
					c.run_meter -= c.run_decay_rate * delta

		# Persistimos gs
		c.run_meter = max(0.0, min(1.0, c.run_meter))
		c._ground_speed = gs

		# ---------------- Gravedad / SALTO + CONTROL Y RESISTENCIA EN AIRE ----------------
		try:    c._no_snap_timer
		except: c._no_snap_timer = 0.0
		if c._no_snap_timer > 0.0:
			c._no_snap_timer = max(0.0, c._no_snap_timer - delta)

		pressed_jump = Input.is_action_just_pressed("jump") or Input.is_action_just_pressed("ui_accept")
		will_jump = (c.control_lock_timer <= 0.0 and c.hitstun_timer <= 0.0
					 and c.is_on_floor() and getattr(c, "_walkable_floor_flag", True) and not c.crouching
					 and pressed_jump and not jump_consumed_for_spindash)

		# En piso caminable y NO saltas: aplicar rampa
		# FIX(resorte-arriba): con _spring_lift_timer activo (resorte vertical) no reconstruir la velocidad desde el suelo
		if (c.is_on_floor() and getattr(c, "_walkable_floor_flag", True) and not will_jump
				and c.hitstun_timer <= 0.0 and getattr(c, "_spring_lift_timer", 0.0) <= 0.0):
			self._apply_adv3_slope_on_ground(delta)

		# EN EL AIRE: momentum + (a) resistencia contra; (b) control mínimo para arrancar desde 0
		if (not c.is_on_floor()) or (not getattr(c, "_walkable_floor_flag", True)) or c.hitstun_timer > 0.0:
			air_resist = float(getattr(c, "air_resist_against", 700.0))
			air_acc    = float(getattr(c, "air_ctrl_accel", 900.0))
			air_thr    = float(getattr(c, "air_ctrl_threshold", 60.0))
			air_cap    = float(getattr(c, "air_ctrl_cap", 140.0))
			# nuevo: cap duro en el aire para “no ir tan rápido” tras saltar
			# FIX: el tope era 0.8*run_speed (800) y recortaba el momentum de rampas/spindash (1600) al instante.
			# Ahora el techo por defecto es la velocidad máxima real del juego; baja c.air_max_speed si lo quieres más corto.
			air_max_spd = float(getattr(c, "air_max_speed", float(getattr(c, "spindash_max_launch", 1600.0))))

			if input_dir != 0 and c.velocity.x != 0 and input_dir == -c._sign(c.velocity.x) and abs(c.velocity.x) > air_thr:
				# (a) resistencia solo si vas rápido y el input es contrario
				resist = air_resist * delta
				if abs(c.velocity.x) <= resist:
					c.velocity.x = 0.0
				else:
					c.velocity.x -= c._sign(c.velocity.x) * resist
			elif input_dir != 0:
				# (b) control mínimo para empezar a moverte desde casi cero (cap suave)
				# FIX(aire-acelera): antes el cap solo se aplicaba en una ventana estrecha justo encima de air_cap;
				# si ya ibas más rápido, cada frame sumaba air_acc hasta air_max_speed (1600).
				# Ahora el input en el aire nunca empuja por encima de air_cap (pero no recorta el momentum que traías).
				vx = c.velocity.x
				if c._sign(vx) != input_dir or abs(vx) < air_cap:
					vx += input_dir * air_acc * delta
					if c._sign(vx) == input_dir and abs(vx) > air_cap:
						vx = input_dir * air_cap
					c.velocity.x = vx

			# Cap de velocidad aérea (también corta exceso que traías del suelo/spindash)
			if abs(c.velocity.x) > air_max_spd:
				c.velocity.x = math.copysign(air_max_spd, c.velocity.x)

			# Gravedad vertical normal
			c.velocity.y += c.gravity * delta
			if c.velocity.y > c.max_fall_speed:
				c.velocity.y = c.max_fall_speed

		# Salto: conserva momentum; si venías de spindash/roll, desbola sin forzar a tope
		if will_jump:
			if getattr(c, "is_rolling", False):
				# Salir de bola con preservación temporal del momentum
				c._stop_roll(preserve=True)
				c.is_rolling = False
				# Mantener estado de "correr", pero SIN forzar run_meter a 1.0
				try:
					c.run_meter = max(float(c.run_meter), float(getattr(c, "sprint_to_run", 0.5)))
				except Exception:
					c.run_meter = max(c.run_meter, 0.5)

			# impulso vertical puro; NO tocamos la X
			c.velocity += (n * c.jump_speed)

			# evita re-snap inmediato y corta anim
			c._no_snap_timer = 0.22
			try:
				if c.anim_player:
					c.anim_player.play("jump")
			except Exception:
				pass

		# -------------- Mover (con o sin snap) --------------
		UP = Vector2(0, -1)
		use_snap = (c._no_snap_timer <= 0.0 and c.hitstun_timer <= 0.0 and getattr(c, "_walkable_floor_flag", True))
		up_dir_to_use = n if use_snap else UP
		# FIX(floor-angle): antes no se pasaba floor_max_angle y Godot usaba 45° por defecto,
		# así que al aterrizar (up = global) en rampas de 45°-65° is_on_floor() daba False.
		floor_angle = math.radians(float(getattr(c, "max_walk_slope_deg", 65.0)))

		perf = getattr(c, "_perf", None)
		if perf: perf.engine_begin()
		try:
			if use_snap:
				c.move_and_slide_with_snap(c.velocity, -up_dir_to_use * self._snap_length(delta), up_dir_to_use,
										   False, 4, floor_angle)
			else:
				c.move_and_slide(c.velocity, up_dir_to_use, False, 4, floor_angle)
		except Exception:
			traceback.print_exc()
			c.move_and_slide(c.velocity, up_dir_to_use)
		if perf: perf.engine_end()

		# -------- Parada seca POR PARED (no por rampa ni wall-run válido) --------
		try:
			for i in range(c.get_slide_count()):
				col = c.get_slide_collision(i)
				if not col: continue
				nrm = col.normal
				# FIX: golpe de techo (normal apuntando hacia abajo) -> corta la subida
				if nrm.y > 0.7 and c.velocity.y < 0.0:
					c.velocity.y = 0.0
					continue
				is_wall =abs(nrm.dot(UP)) < 0.25 and abs(nrm.x) > 0.2
				# si estamos en "piso" (incluye wall-run válido), no aplicar frenado por pared
				if c.is_on_floor() and getattr(c, "_walkable_floor_flag", False):
					continue
				if not is_wall: continue
				if c.velocity.dot(nrm) < 0:
					c.velocity.x = 0.0
					if abs(c.velocity.y) < 20.0: c.velocity.y = 0.0
					c._ground_speed = 0.0
					if c.is_rolling: c._stop_roll(preserve=False)
					c.run_meter = 0.0
					break
		except Exception:
			pass

		# up_dir post-move (solo si piso caminable)
		try:
			if c.is_on_floor():
				n_after = c.get_floor_normal()
				if n_after.length() > 1e-6 and n_after.normalized().dot(UP) >= math.cos(math.radians(float(getattr(c,"wall_run_enabled", True) and getattr(c,"wall_run_max_angle_deg",90.0) or getattr(c,"max_walk_slope_deg",65.0)))):
					c.surface_up_dir = n_after.normalized()
				else:
					c.surface_up_dir = UP
		except Exception:
			pass

		# ---------------- Animaciones / flip ----------------
		idle_enough = abs(getattr(c, "_ground_speed", 0.0)) < 1.0 and c.is_on_floor() and getattr(c, "_walkable_floor_flag", True)
		if Input.is_action_just_pressed("ui_down") and idle_enough and not c.is_spindash_charging and c.hitstun_timer <= 0.0:
			ld_len = c._anim_len.get("look_down", 0.0)
			try:
				c.anim_player.play("look_down")
				if ld_len > 0.001: c.look_mode = "look_down_playing"; c.look_timer = ld_len
				else: c.look_mode = "look_down_done"; c.look_timer = 0.0
			except Exception:
				c.look_mode = None; c.look_timer = 0.0

		if c.look_mode in ("look_down_playing","look_down_done") and not Input.is_action_pressed("ui_down"):
			st_len = c._anim_len.get("standup", 0.0)
			try:
				c.anim_player.play("standup")
				if st_len > 0.001: c.look_mode = "standup_wait"; c.look_timer = st_len
				else: c.look_mode = None; c.look_timer = 0.0
			except Exception:
				c.look_mode = None; c.look_timer = 0.0

		if (not c.is_rolling) and (not c.is_spindash_charging) and Input.is_action_pressed("ui_down") and not idle_enough and c.is_on_floor() and getattr(c, "_walkable_floor_flag", True) and c.original_extents:
			if not c.crouching:
				c.crouching = True
				try:
					c.cshape_node.shape.extents = Vector2(c.crouch_extents.x, c.crouch_extents.y)
					dy = c.original_extents.y - c.crouch_extents.y
					c.cshape_node.position = Vector2(c.cshape_original_pos.x, c.cshape_original_pos.y + dy)
				except Exception: pass
		else:
			if c.crouching and not (Input.is_action_pressed("ui_down") and not idle_enough):
				c.crouching = False
				try:
					if c.original_extents:
						c.cshape_node.shape.extents = Vector2(c.original_extents.x, c.original_extents.y)
						c.cshape_node.position = Vector2(c.cshape_original_pos.x, c.cshape_original_pos.y)
				except Exception: pass

		if Input.is_action_pressed("ui_up") and idle_enough:
			if c.look_mode is None:
				pre_len = c._anim_len.get("prelook_up", 0.0)
				try:
					if pre_len > 0.001:
						c.anim_player.play("prelook_up"); c.look_mode = "wait_prelook_up"; c.look_timer = pre_len
					else:
						c.anim_player.play("look_up"); c.look_mode = "look_up"; c.look_timer = 0.0
				except Exception:
					c.look_mode = None; c.look_timer = 0.0
		else:
			if c.look_mode in ("wait_prelook_up","look_up"):
				st_len = c._anim_len.get("standup", 0.0)
				try:
					c.anim_player.play("standup")
					if st_len > 0.001: c.look_mode = "standup_wait"; c.look_timer = st_len
					else: c.look_mode = None; c.look_timer = 0.0
				except Exception:
					c.look_mode = None; c.look_timer = 0.0

		if c.look_timer > 0:
			c.look_timer = max(0.0, c.look_timer - delta)
			if c.look_timer <= 0:
				if c.look_mode == "wait_prelook_up":
					try: c.anim_player.play("look_up")
					except Exception: pass
					c.look_mode = "look_up"
				elif c.look_mode == "look_down_playing":
					if Input.is_action_pressed("ui_down"): c.look_mode = "look_down_done"
					else:
						st_len = c._anim_len.get("standup", 0.0)
						try:
							c.anim_player.play("standup")
							if st_len > 0.001: c.look_mode = "standup_wait"; c.look_timer = st_len
							else: c.look_mode = None
						except Exception:
							c.look_mode = None
				elif c.look_mode == "standup_wait":
					c.look_mode = None

		# Anim principal
		desired_anim = None
		if c.hitstun_timer > 0.0: desired_anim = "hit"
		elif c.is_rolling:        desired_anim = "roll"
		elif c.is_braking:        desired_anim = "break"
		else:
			inv_now = (input_dir != 0 and c._sign(getattr(c, "_ground_speed", 0.0)) != 0
					   and c._sign(getattr(c, "_ground_speed", 0.0)) != input_dir)
			if c.is_on_floor() and getattr(c, "_walkable_floor_flag", True) and inv_now and c._is_run_or_maxrun():
				desired_anim = "break"
			else:
				if c.look_mode in ("wait_prelook_up","look_up"): desired_anim = "look_up"
				elif c.look_mode in ("look_down_playing","look_down_done"): desired_anim = None
				elif c.look_mode == "standup_wait": desired_anim = "standup"
				else:
					if c.is_on_floor() and getattr(c, "_walkable_floor_flag", True):
						if c.crouching: desired_anim = "crouch"
						else:
							abs_gs = abs(getattr(c, "_ground_speed", 0.0))
							if abs_gs > 0.1:
								if c.run_meter >= c.run_to_max or abs_gs >= 0.98 * c.run_speed: desired_anim = "runmax"
								elif abs_gs >= c.run_threshold and c.run_meter >= c.sprint_to_run: desired_anim = "run"
								elif (c.run_meter >= c.sprint2_threshold and (c.sprint2_timer > 0 or c.run_meter < c.sprint_to_run)): desired_anim = "sprint_mid"
								elif (c.run_meter >= c.sprint1_threshold and (c.sprint1_timer > 0 or c.run_meter < c.sprint2_threshold)): desired_anim = "sprint_start"
								else: desired_anim = "walk"
							else: desired_anim = "idle"
					else:
						desired_anim = "jump" if c.velocity.y < 0 else "fall"

		try:
			if desired_anim and c.anim_player.current_animation != desired_anim:
				c.anim_player.play(desired_anim)
		except Exception:
			pass

		# Flip por ground speed (evita jitter)
		gs_for_flip = getattr(c, "_ground_speed", self._gs_from_velocity(c.velocity, t))
		if gs_for_flip > 0.1:   c.sprite.flip_h = True
		elif gs_for_flip < -0.1: c.sprite.flip_h = False

		c.last_input_dir = input_dir
		c.last_run_meter = c.run_meter
		c.last_down_pressed = down_pressed
