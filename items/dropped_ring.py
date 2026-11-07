# res://items/dropped_ring.py
from godot import exposed, export, RigidBody2D, Vector2, Area2D, CollisionShape2D, CircleShape2D

@exposed
class DroppedRing(RigidBody2D):
	# ===== Vida / parpadeo / pickup =====
	lifetime = export(float, default=6.0)
	blink_start = export(float, default=3.0)
	blink_freq = export(float, default=12.0)
	pickup_delay = export(float, default=0.25)

	# ===== Capas (ajusta si usas otras) =====
	# Convención sugerida:
	#   Player capa 1, Suelo (TileMap/StaticBody2D) capa 2
	player_layer_bit   = export(int, default=2)
	ground_layer_bit   = export(int, default=1)   # la capa en la que está TU suelo
	ring_body_layer_bit = export(int, default=6)  # capa propia del cuerpo del ring
	ring_area_layer_bit = export(int, default=7)  # capa del Area2D de pickup

	def _bitmask(self, bit_1_based):
		b = int(bit_1_based)
		if b < 1: b = 1
		return 1 << (b - 1)

	def _ready(self):
		# refs
		self.sprite = None
		self.anim_player = None
		try:
			self.sprite = self.get_node("Sprite")
		except Exception:
			pass
		try:
			self.anim_player = self.get_node("AnimationPlayer")
			if self.anim_player:
				try:
					self.anim_player.play("ring_idle")
				except Exception:
					pass
		except Exception:
			pass

		# timers
		self.age = 0.0
		self.blink_accum = 0.0
		self.can_pick = False

		# Evitar rotación + CCD para no atravesar el piso
		try:
			self.angular_velocity = 0.0
			self.rotation = 0.0
			self.continuous_cd = True      # CCD ON (Godot 3)
			self.contact_monitor = True
			self.contacts_reported = 4
		except Exception:
			pass

		# ===== CUERPO: en su propia capa y máscara SOLO al suelo =====
		try:
			self.collision_layer = self._bitmask(self.ring_body_layer_bit)
			# máscara provisional (si luego autodetecta, la reescribimos)
			self.collision_mask  = self._bitmask(self.ground_layer_bit)
		except Exception:
			pass

		# ===== PICKUP AREA: crea/configura si falta =====
		self._ensure_pickup_area()

		# ===== AUTODETECCIÓN de capa del suelo (por si tu suelo NO está en la 2) =====
		self._try_autodetect_ground_mask()

	def _ensure_pickup_area(self):
		# Busca/crea Area2D hijo llamado "PickupArea"
		area = None
		try:
			area = self.get_node("PickupArea")
		except Exception:
			pass
		if area is None:
			try:
				area = Area2D.new()
				area.set_name("PickupArea")
				shape_node = CollisionShape2D.new()
				shape = CircleShape2D.new()
				shape.set_radius(8.0)
				shape_node.shape = shape
				area.add_child(shape_node)
				self.add_child(area)
			except Exception:
				area = None
		self.pickup_area = area

		# Configurar capas/máscaras del Área: solo ve al Player
		if self.pickup_area:
			try:
				self.pickup_area.collision_layer = self._bitmask(self.ring_area_layer_bit)
				self.pickup_area.collision_mask  = self._bitmask(self.player_layer_bit)
				# conectar señal
				# (si ya estaba conectada, Godot ignora conexiones duplicadas)
				self.pickup_area.connect("body_entered", self, "_on_pickup_body")
			except Exception:
				pass

	def _try_autodetect_ground_mask(self):
		"""Lanza un raycast hacia abajo y toma la collision_layer del primer suelo.
		   Ajusta la máscara del ring a esa capa (quitando el bit del player si coincide)."""
		try:
			space = self.get_world_2d().direct_space_state
			from_pt = self.global_position
			to_pt   = self.global_position + Vector2(0, 96)  # 96px hacia abajo
			# exclude este rigid
			exclude = [self]
			# 0xFFFFF -> todos los 20 bits
			res = space.intersect_ray(from_pt, to_pt, exclude, 0xFFFFF, True, False)
			if res and "collider" in res and res["collider"]:
				col = res["collider"]
				# Lee bitmask del suelo detectado
				ground_mask = int(getattr(col, "collision_layer", 0))
				if ground_mask == 0:
					return
				# Asegúrate de NO incluir al player si comparten bit
				player_mask = self._bitmask(self.player_layer_bit)
				ground_mask &= ~player_mask
				if ground_mask != 0:
					self.collision_mask = ground_mask
		except Exception:
			pass

	def setup(self, initial_velocity=None, pickup_delay=None):
		if initial_velocity is not None:
			self.linear_velocity = Vector2(initial_velocity.x, initial_velocity.y)
		if pickup_delay is not None:
			self.pickup_delay = float(pickup_delay)

	# Mantenerlo vertical SIEMPRE
	def _integrate_forces(self, state):
		try:
			self.rotation = 0.0
			self.angular_velocity = 0.0
		except Exception:
			pass

	def _physics_process(self, delta):
		# Forzar verticalidad (doble seguro)
		try:
			if self.rotation != 0.0:
				self.rotation = 0.0
			if self.angular_velocity != 0.0:
				self.angular_velocity = 0.0
		except Exception:
			pass

		# timers
		self.age += delta
		if not self.can_pick and self.age >= self.pickup_delay:
			self.can_pick = True

		if self.age >= self.blink_start:
			self.blink_accum += delta
			vis = (int(self.blink_accum * self.blink_freq) & 1) == 0
			try:
				if self.sprite:
					self.sprite.visible = vis
			except Exception:
				pass

		if self.age >= self.lifetime:
			self.queue_free()

	def _on_pickup_body(self, body):
		if not self.can_pick:
			return
		try:
			# Recoge solo si el body sabe sumar rings (tu Player lo tiene)
			if hasattr(body, "collect_ring"):
				body.collect_ring(1)
				self.queue_free()
		except Exception:
			pass
