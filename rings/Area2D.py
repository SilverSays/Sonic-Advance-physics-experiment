# res://sonic/ring.py
from godot import exposed, Area2D

@exposed
class Ring(Area2D):
	def _ready(self):
		self.anim = None
		self.shape = None
		try:
			self.anim = self.get_node("AnimationPlayer")
		except Exception:
			pass

		# intenta CollisionShape2D directo o primer hijo que lo sea
		try:
			self.shape = self.get_node("CollisionShape2D")
		except Exception:
			try:
				for i in range(self.get_child_count()):
					ch = self.get_child(i)
					if "CollisionShape2D" in str(type(ch)):
						self.shape = ch
						break
			except Exception:
				self.shape = None

		self._collected = False

		try:
			if self.anim and self.anim.has_animation("ring_idle"):
				self.anim.play("ring_idle")
		except Exception:
			pass

		try:
			self.connect("body_entered", self, "_on_body_entered")
		except Exception:
			pass
		try:
			if self.anim:
				self.anim.connect("animation_finished", self, "_on_anim_finished")
		except Exception:
			pass

	def _on_body_entered(self, body):
		if self._collected:
			return

		# 👉 SOLO recoger si el body realmente puede recoger (el jugador)
		if hasattr(body, "collect_ring"):
			try:
				body.collect_ring(1)
			except Exception:
				try:
					body.collect_ring()
				except Exception:
					pass

			self._collected = True

			# desactivar colisión/monitoring DEFERIDO para evitar warnings
			try:
				if self.shape:
					self.shape.set_deferred("disabled", True)
				self.set_deferred("monitoring", False)
				self.set_deferred("collision_layer", 0)
				self.set_deferred("collision_mask", 0)
			except Exception:
				pass

			# anim de recolección si existe; si no, borrar deferido
			try:
				if self.anim and self.anim.has_animation("collect"):
					self.anim.play("collect")
				else:
					self.call_deferred("queue_free")
			except Exception:
				self.call_deferred("queue_free")
		else:
			# No es el jugador -> IGNORAR (no liberar)
			return

	def _on_anim_finished(self, name):
		if name == "collect":
			self.call_deferred("queue_free")
