# res://items/springs/spring_up/SpringUp.py
from godot import exposed, export, Area2D, Vector2

@exposed
class SpringUp(Area2D):
	launch_speed = export(float, default=900.0)   # fuerza del salto hacia arriba
	lock_time    = export(float, default=0.22)    # cuánto tiempo bloquear input contrario
	cooldown     = export(float, default=0.15)    # tiempo mínimo entre impulsos

	def _ready(self):
		self._armed = True   # listo para impulsar
		self._cd_left = 0.0

		# AnimatedSprite / AnimatedSprite2D
		self.sprite = None
		if self.has_node("AnimatedSprite"):
			self.sprite = self.get_node("AnimatedSprite")
		elif self.has_node("AnimatedSprite2D"):
			self.sprite = self.get_node("AnimatedSprite2D")

		# Señal de entrada (solo body_entered para evitar duplicados)
		try: self.disconnect("body_entered", self, "_on_body_entered")
		except Exception: pass
		try: self.connect("body_entered", self, "_on_body_entered")
		except Exception: pass

		# Señal de fin de animación -> volver a idle
		if self.sprite:
			try: self.sprite.connect("animation_finished", self, "_on_anim_finished")
			except Exception: pass

		# Dejar en idle (parado) por defecto
		if self.sprite:
			try:
				if hasattr(self.sprite, "frames") and self.sprite.frames and self.sprite.frames.has_animation("idle"):
					self.sprite.animation = "idle"
				self.sprite.stop()
				self.sprite.playing = False
				try: self.sprite.frame = 0
				except Exception: pass
			except Exception:
				pass

		# Asegurar monitoreo activo
		try:
			self.monitoring = True
			self.monitorable = True
		except Exception:
			pass

	def _physics_process(self, delta):
		# Fallback para cooldown si no usamos SceneTreeTimer
		if not self._armed and self._cd_left > 0.0:
			self._cd_left -= delta
			if self._cd_left <= 0.0:
				self._rearm()

	def _on_body_entered(self, body):
		if not self._armed:
			return

		player = self._find_player_node(body)
		if not player:
			return

		# Impulso vertical hacia arriba
		if hasattr(player, "external_boost"):
			try:
				# keep_rolling=None -> conserva si venía rodando o de pie
				player.external_boost(Vector2(0, -1), self.launch_speed, self.lock_time, None)
			except Exception:
				try:
					player.external_boost(Vector2(0, -1), self.launch_speed, self.lock_time)
				except Exception:
					pass
		else:
			try:
				player.velocity.y = -abs(float(self.launch_speed))
				if hasattr(player, "control_lock_timer"):
					player.control_lock_timer = max(player.control_lock_timer, float(self.lock_time))
			except Exception:
				pass

		self._play_boing()
		self._disarm_temporarily()  # evita re-impulsos mientras sigue encima

	def _disarm_temporarily(self):
		self._armed = False
		self._cd_left = float(self.cooldown)
		try:
			# al desactivar monitoring, no volverá a emitir body_entered hasta rearmar
			self.set_deferred("monitoring", False)
		except Exception:
			pass

		# Intento con SceneTreeTimer (si falla, _physics_process maneja el cooldown)
		try:
			t = self.get_tree().create_timer(float(self.cooldown))
			t.connect("timeout", self, "_rearm")
		except Exception:
			pass

	def _rearm(self):
		self._armed = True
		self._cd_left = 0.0
		try:
			self.monitoring = True
			self.set_deferred("monitoring", True)
		except Exception:
			pass

	def _find_player_node(self, node):
		# Busca un nodo con external_boost (tu Personaje) subiendo unos niveles
		try:
			if hasattr(node, "external_boost"):
				return node
			up = node
			for _ in range(3):
				up = up.get_parent()
				if not up:
					break
				if hasattr(up, "external_boost"):
					return up
		except Exception:
			pass
		return None

	def _play_boing(self):
		if not self.sprite:
			return
		try:
			if hasattr(self.sprite, "frames") and self.sprite.frames and self.sprite.frames.has_animation("boing"):
				self.sprite.animation = "boing"
			self.sprite.playing = True
			self.sprite.play()
		except Exception:
			pass

	def _on_anim_finished(self, *args):
		self._back_to_idle()

	def _back_to_idle(self):
		if not self.sprite:
			return
		try:
			if hasattr(self.sprite, "frames") and self.sprite.frames and self.sprite.frames.has_animation("idle"):
				self.sprite.animation = "idle"
			self.sprite.stop()
			self.sprite.playing = False
			try: self.sprite.frame = 0
			except Exception: pass
		except Exception:
			pass
