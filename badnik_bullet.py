from godot import exposed, export, Area2D, Vector2

@exposed
class BadnikBullet(Area2D):
	speed = export(float, default=360.0)
	lifetime = export(float, default=3.0)

	def _ready(self):
		# ¡NO vuelvas a inicializar self.velocity aquí!
		# Solo crea si no existe (por seguridad).
		if not hasattr(self, "velocity"):
			self.velocity = Vector2()
		self._life = 0.0

		try:
			self.set_physics_process(True)
		except Exception:
			pass

		try:
			if not self.is_connected("body_entered", self, "_on_body_entered"):
				self.connect("body_entered", self, "_on_body_entered")
		except Exception:
			pass

		# print("[BULLET] ready")

	def setup(self, dir_vec, speed=None):
		# Le damos dirección/velocidad definitiva
		try:
			if dir_vec.length() == 0:
				dir_vec = Vector2(1, 0)
		except Exception:
			dir_vec = Vector2(1, 0)

		spd = float(speed if speed is not None else self.speed)
		self.velocity = dir_vec.normalized() * spd

		# orientar sprite (opcional)
		try:
			self.rotation = self.velocity.angle()
		except Exception:
			pass

		# print("[BULLET] setup vel=", self.velocity)

	def _physics_process(self, delta):
		# Mover en línea recta
		try:
			self.position = Vector2(
				self.position.x + self.velocity.x * delta,
				self.position.y + self.velocity.y * delta
			)
		except Exception:
			try:
				self.translate(self.velocity * delta)
			except Exception:
				pass

		# vida limitada
		self._life += delta
		if self._life >= float(self.lifetime):
			self.queue_free()

	def _on_body_entered(self, body):
		if hasattr(body, "take_damage"):
			try:
				body.take_damage()
			except Exception:
				pass
		self.queue_free()
