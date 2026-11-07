# res://objects/Checkpoint.py
from godot import exposed, Area2D, Vector2

@exposed
class Checkpoint(Area2D):
	def _ready(self):
		self.active = False

		# Buscar AnimatedSprite primero (y NO reproducir nada en idle)
		self.sprite = None
		if self.has_node("AnimatedSprite"):
			self.sprite = self.get_node("AnimatedSprite")
		elif self.has_node("AnimatedSprite2D"):
			self.sprite = self.get_node("AnimatedSprite2D")

		# Fallback opcional a AnimationPlayer (por si lo usas)
		self.anim = None
		if self.has_node("AnimationPlayer"):
			self.anim = self.get_node("AnimationPlayer")

		# Asegurar detección de jugador
		try:
			self.monitoring = True
			self.monitorable = True
			self.collision_mask = (1 << 20) - 1  # máscara amplia (Godot 3: 20 capas)
		except Exception:
			pass

		# Señales
		try:
			self.disconnect("body_entered", self, "_on_body_entered")
		except Exception:
			pass
		try:
			self.connect("body_entered", self, "_on_body_entered")
		except Exception:
			pass

		if self.sprite:
			try:
				self.sprite.disconnect("animation_finished", self, "_on_anim_finished")
			except Exception:
				pass
			try:
				self.sprite.connect("animation_finished", self, "_on_anim_finished")
			except Exception:
				pass
		elif self.anim:
			try:
				self.anim.disconnect("animation_finished", self, "_on_anim_finished")
			except Exception:
				pass
			try:
				self.anim.connect("animation_finished", self, "_on_anim_finished")
			except Exception:
				pass

		# Mostrar idle estático (sin animar)
		self._show_idle_static()

	# ---------- Helpers de anim ----------
	def _show_idle_static(self):
		"""Dejar el checkpoint quieto, sin reproducir animación."""
		if self.sprite:
			try:
				# Si tienes anim "idle", colócate en frame 0 y NO play
				if hasattr(self.sprite, "frames") and self.sprite.frames and self.sprite.frames.has_animation("idle"):
					self.sprite.animation = "idle"
					try:
						self.sprite.frame = 0  # mostrar primer frame
					except Exception:
						pass
				self.sprite.stop()
				self.sprite.playing = False
			except Exception:
				pass
		elif self.anim:
			try:
				# No reproducir nada en AnimationPlayer
				self.anim.stop()
			except Exception:
				pass

	def _play_activate(self):
		if self.sprite:
			try:
				if hasattr(self.sprite, "frames") and self.sprite.frames and self.sprite.frames.has_animation("activate"):
					self.sprite.animation = "activate"
					self.sprite.playing = True
					self.sprite.play()
				else:
					self._loop_active()
			except Exception:
				self._loop_active()
		elif self.anim:
			try:
				self.anim.play("activate")
			except Exception:
				self._loop_active()

	def _loop_active(self):
		if self.sprite:
			try:
				if hasattr(self.sprite, "frames") and self.sprite.frames and self.sprite.frames.has_animation("active"):
					self.sprite.animation = "active"
				self.sprite.playing = True
				self.sprite.play()  # queda en loop
			except Exception:
				pass
		elif self.anim:
			try:
				self.anim.play("active")
			except Exception:
				pass

	# ---------- Señales ----------
	def _on_body_entered(self, body):
		if self.active:
			return
		# ¿Es el jugador?
		if hasattr(body, "set_respawn_point"):
			self.active = True
			try:
				body.set_respawn_point(self.global_position)
			except Exception:
				pass
			self._play_activate()

	# AnimatedSprite: animation_finished() sin args; AnimationPlayer: con nombre
	def _on_anim_finished(self, *args, **kwargs):
		if self.active:
			self._loop_active()
