# res://enemies/badnik_flyer.py
from godot import exposed, export, KinematicBody2D, Vector2, ResourceLoader
import math

@exposed
class BadnikFlyer(KinematicBody2D):
	# --- Patrulla (oscilación horizontal respecto al punto de spawn) ---
	patrol_amplitude = export(float, default=32.0)   # px a izquierda/derecha
	patrol_speed     = export(float, default=1.5)    # rapidez de oscilación

	# --- Disparo ---
	charge_time   = export(float, default=0.45)      # tiempo de "carga" antes de disparar
	fire_interval = export(float, default=1.20)      # enfriamiento entre disparos
	bullet_speed  = export(float, default=160.0)
	bullet_scene_path = export(str, default="res://enemies/badnik_bullet.tscn")
	face_target_while_charging = export(bool, default=True)

	# --- Contacto con jugador ---
	kill_on_stomp   = export(bool, default=True)     # si Sonic salta/rueda sobre él, muere
	stomp_bounce    = export(float, default=0.7)     # rebote a Sonic al matarlo
	damage_if_touch = export(bool, default=True)     # daña si Sonic lo toca sin saltar/rodar

	def _ready(self):
		# Asegurar que _physics_process corre (PythonScript)
		try:
			self.set_physics_process(True)
		except Exception:
			pass

		# Buscar nodos (ajusta los nombres si tus nodos se llaman distinto)
		self.sprite  = self._find_node_any(["Sprite", "AnimatedSprite", "Sprite2D"])
		self.anim    = self._find_node_any(["AnimationPlayer"])
		self.hurtbox = self._find_node_any(["Hurtbox"])
		self.aggro   = self._find_node_any(["AggroArea", "Aggro"])
		self.muzzle  = self._find_node_any(["Muzzle", "ShootPoint", "Gun"])

		# Habilitar áreas y shapes
		self._ensure_area_ready(self.hurtbox)
		self._ensure_area_ready(self.aggro)

		# Conectar señales (sólo si no están conectadas)
		self._connect_once(self.aggro,   "body_entered", self, "_on_aggro_enter")
		self._connect_once(self.aggro,   "body_exited",  self, "_on_aggro_exit")
		self._connect_once(self.hurtbox, "body_entered", self, "_on_hurtbox_enter")

		# Cargar escena de bala
		self._bullet_scene = None
		try:
			self._bullet_scene = ResourceLoader.load(self.bullet_scene_path)
		except Exception:
			self._bullet_scene = None

		# Estado
		gp = self.global_position
		self._origin = Vector2(gp.x, gp.y)
		self._t = 0.0
		self._target = None
		self._target_in_range = False
		self._charging_timer = 0.0
		self._cooldown_timer = 0.0

		self._play_anim_safe("idle")

	# -------------------- Helpers de setup --------------------
	def _find_node_any(self, names):
		for n in names:
			try:
				if self.has_node(n):
					return self.get_node(n)
			except Exception:
				pass
		return None

	def _ensure_area_ready(self, area):
		if not area:
			return
		# monitoring / monitorable
		for fn, val in (("set_monitoring", True), ("set_monitorable", True)):
			try:
				getattr(area, fn)(val)
			except Exception:
				pass
		# habilitar CollisionShape2D hijo(s)
		try:
			for child in area.get_children():
				if child.__class__.__name__ == "CollisionShape2D":
					try:
						child.disabled = False
					except Exception:
						pass
		except Exception:
			pass

	def _connect_once(self, node, signal, target, method):
		if not node:
			return
		try:
			if not node.is_connected(signal, target, method):
				node.connect(signal, target, method)
		except Exception:
			pass

	def _play_anim_safe(self, name):
		if self.anim:
			try:
				if self.anim.has_animation(name):
					self.anim.play(name)
			except Exception:
				pass

	# -------------------- Loop --------------------
	def _physics_process(self, delta):
		# Patrulla: sinusoide en X alrededor del punto de spawn
		self._t += delta * self.patrol_speed
		self.global_position = Vector2(
			self._origin.x + math.sin(self._t) * self.patrol_amplitude,
			self._origin.y
		)

		# Timers de disparo
		if self._cooldown_timer > 0.0:
			self._cooldown_timer -= delta
			if self._cooldown_timer < 0.0:
				self._cooldown_timer = 0.0

		if self._target_in_range and self._valid_target():
			# Mirar al objetivo mientras carga
			if self.face_target_while_charging and self.sprite:
				try:
					self.sprite.flip_h = (self._target.global_position.x >= self.global_position.x)
				except Exception:
					pass

			# Cargar y disparar
			if self._cooldown_timer <= 0.0:
				if self._charging_timer <= 0.0:
					self._charging_timer = float(self.charge_time)
					self._play_anim_safe("charge")
				else:
					self._charging_timer -= delta
					if self._charging_timer <= 0.0:
						self._shoot()
						self._cooldown_timer = float(self.fire_interval)
						self._play_anim_safe("shoot")
		else:
			# Sin objetivo: idle
			if self.anim:
				try:
					if self.anim.current_animation not in ("idle", "patrol"):
						self._play_anim_safe("idle")
				except Exception:
					self._play_anim_safe("idle")
			self._charging_timer = 0.0

	def _valid_target(self):
		try:
			return self._target is not None and self._target.is_inside_tree()
		except Exception:
			return False

	# -------------------- Disparo --------------------
	def _shoot(self):
		if not self._bullet_scene:
			return
		try:
			bullet = self._bullet_scene.instance()
		except Exception:
			return

		# Punto de spawn (antes de añadir al árbol)
		spawn = self.muzzle.global_position if self.muzzle else self.global_position
		try:
			bullet.global_position = spawn
		except Exception:
			bullet.position = spawn

		# Añadir al árbol PRIMERO (para que corra _ready del bullet)
		try:
			self.get_parent().add_child(bullet)
		except Exception:
			self.add_child(bullet)

		# Dirección hacia Sonic EN ESE INSTANTE
		try:
			tpos = self._target.global_position
		except Exception:
			tpos = Vector2(
				self.global_position.x + (10 if (self.sprite and self.sprite.flip_h) else -10),
				self.global_position.y
			)
		dir_vec = Vector2(tpos.x - spawn.x, tpos.y - spawn.y)

		# Pasar dirección + velocidad a la bala (después de estar en el árbol)
		try:
			bullet.setup(dir_vec, self.bullet_speed)
		except Exception:
			try:
				bullet.velocity = dir_vec.normalized() * float(self.bullet_speed)
			except Exception:
				pass

	# -------------------- Señales (lógica) --------------------
	def _on_aggro_enter(self, body):
		# Detecta al jugador de forma flexible: que tenga take_damage o collect_ring
		if hasattr(body, "take_damage") or hasattr(body, "collect_ring"):
			self._target = body
			self._target_in_range = True

	def _on_aggro_exit(self, body):
		if body == self._target:
			self._target = None
			self._target_in_range = False
			self._charging_timer = 0.0
			self._play_anim_safe("idle")

	def _on_hurtbox_enter(self, body):
		if not self.damage_if_touch or not hasattr(body, "take_damage"):
			return

		# Considerar "en aire" como salto
		try:
			in_air = not body.is_on_floor()
		except Exception:
			in_air = False
		is_rolling = bool(getattr(body, "is_rolling", False))

		if is_rolling or in_air:
			# Sonic salta/rueda -> matar badnik (si está habilitado)
			if self.kill_on_stomp:
				try:
					if hasattr(body, "velocity") and hasattr(body, "jump_speed"):
						body.velocity.y = -abs(body.jump_speed * float(self.stomp_bounce))
				except Exception:
					pass
				self._die()
			return
		else:
			# Sonic en suelo sin roll -> daño
			try:
				body.take_damage()
			except Exception:
				pass

	def _die(self):
		if self.anim and self.anim.has_animation("die"):
			try:
				self.anim.play("die")
				self.call_deferred("queue_free")
				return
			except Exception:
				pass
		self.queue_free()

	# -------------------- Wrappers (si conectaste señales en el editor) --------------------
	def _on_AggroArea_body_entered(self, body):
		sel
