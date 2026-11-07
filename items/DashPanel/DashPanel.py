# res://objects/DashPanel.py
from godot import exposed, export, Area2D, Vector2
import math

@exposed
class DashPanel(Area2D):
	launch_speed = export(float, default=1200.0)
	use_node_rotation = export(bool, default=True)
	angle_deg = export(float, default=0.0)
	cooldown_time = export(float, default=0.20)
	set_run_meter_to = export(float, default=1.0)
	lock_time = export(float, default=0.30)  # <- un pelín más largo

	def _ready(self):
		self.anim = None
		try:
			self.anim = self.get_node("AnimationPlayer")
			if self.anim and self.anim.has_animation("idle"):
				self.anim.play("idle")
		except Exception:
			pass
		try:
			self.set_monitoring(True); self.set_monitorable(True)
			self.connect("body_entered", self, "_on_body_entered")
			self.connect("body_exited", self, "_on_body_exited")
		except Exception:
			pass
		self._cool = {}

	def _physics_process(self, delta):
		for k in list(self._cool.keys()):
			self._cool[k] -= delta
			if self._cool[k] <= 0: del self._cool[k]

	def _panel_dir(self):
		d = Vector2(1, 0)
		if self.use_node_rotation:
			try: d = d.rotated(self.global_rotation)
			except Exception: pass
		if abs(self.angle_deg) > 1e-3:
			d = d.rotated(math.radians(self.angle_deg))
		return d.normalized() if d.length() != 0 else Vector2(1, 0)

	def _on_body_entered(self, body):
		try: iid = body.get_instance_id()
		except Exception: iid = 0
		if iid in self._cool: return

		dirv = self._panel_dir(); speed = float(self.launch_speed)
		print("[DASHPANEL] hit ->", str(body), "dir=", dirv, "speed=", speed)

		try:
			if hasattr(body, "external_boost"):
				# Mantener roll y aplicar lock
				body.call_deferred("external_boost", dirv, speed, float(self.lock_time))
			else:
				# Fallback mínimo
				body.set_deferred("velocity", Vector2(dirv.x * speed, dirv.y * speed))
		except Exception as e:
			print("[DASHPANEL] apply error:", e)

		self._cool[iid] = float(self.cooldown_time)

	def _on_body_exited(self, body):
		pass
