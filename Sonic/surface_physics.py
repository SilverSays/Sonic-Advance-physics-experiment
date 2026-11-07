# res://Sonic/surface_physics.py
from godot import Vector2

class SurfaceController:
	def __init__(self, character):
		self.c = character
		# Parámetros ajustables
		self.max_attach_angle_deg = 60.0   # ángulo máx de suelo para “pegarse”
		self.stick_force = 900.0           # pequeña fuerza hacia la normal
		self.slope_influence = getattr(character, "slope_influence", 1.0)
		self.static_friction_threshold = getattr(character, "static_friction_threshold", 80.0)
		self.g = getattr(character, "gravity", 900.0)
		# Nombres esperados de raycasts (opcional)
		self.ray_names = ("RayFront", "RayBack")

	def _get_rays(self):
		"""Busca RayCast2D hijos opcionalmente."""
		rays = []
		for n in self.ray_names:
			try:
				rc = self.c.get_node(n)
				if rc and hasattr(rc, "is_enabled") and rc.is_enabled():
					rays.append(rc)
			except Exception:
				pass
		return rays

	def _probe_ground(self):
		"""
		Devuelve (has_ground, ground_normal (Vector2 norm), ground_pos (Vector2), angle_deg).
		Usa 2 RayCast2D (si existen). Si no, cae al get_floor_normal().
		"""
		rays = self._get_rays()
		if len(rays) >= 1:
			hits = []
			for rc in rays:
				try:
					if rc.is_colliding():
						hits.append( (rc.get_collision_point(), rc.get_collision_normal()) )
				except Exception:
					pass
			if len(hits) == 0:
				return (False, Vector2(0, -1), self.c.global_position, 0.0)

			# Promedia normales
			n = Vector2(0, 0)
			prom_pos = Vector2(0, 0)
			for p, norm in hits:
				n += Vector2(norm.x, norm.y)
				prom_pos += Vector2(p.x, p.y)
			n_len = n.length()
			if n_len == 0:
				n = Vector2(0, -1)
			else:
				n = n / n_len
			prom_pos *= 1.0 / len(hits)

			# Ángulo con respecto a up global
			up = Vector2(0, -1)
			dot = max(-1.0, min(1.0, n.dot(up)))
			# acos seguro:
			import math
			angle = math.degrees(math.acos(dot))
			return (True, n, prom_pos, angle)

		# Fallback si no hay RayCast2D
		try:
			if self.c.is_on_floor():
				n = self.c.get_floor_normal()
				n_len = n.length()
				if n_len == 0:
					n = Vector2(0, -1)
				else:
					n = n / n_len
				up = Vector2(0, -1)
				import math
				dot = max(-1.0, min(1.0, n.dot(up)))
				angle = math.degrees(math.acos(dot))
				return (True, n, self.c.global_position, angle)
		except Exception:
			pass
		return (False, Vector2(0, -1), self.c.global_position, 0.0)

	def pre_move(self, delta):
		"""
		Calcula up_dir (normal del suelo si procede) y añade la aceleración por pendiente.
		Debe llamarse ANTES de move_and_slide.
		"""
		has_ground, n, _, angle_deg = self._probe_ground()

		# Si no hay buen suelo o demasiado inclinado, usar up global
		if not has_ground or angle_deg > self.max_attach_angle_deg:
			return Vector2(0, -1)

		# Tangente (unitaria) con n = (nx, ny): t = (ny, -nx)
		t = Vector2(n.y, -n.x)

		# Aceleración por pendiente: g * sin(theta) ≡ g proyectado en tangente
		# Componente tangencial de la gravedad (dirección del “bajón”)
		# Gravity (0, g) proyectada en t -> (0, g)·t = g * t.y
		# Añadimos a vel.x en dirección t.x y a vel.y en dirección t.y (pero como horizontal ya la llevas, solo x es útil)
		try:
			# influencia y umbral para impedir que se deslice parado
			slope_ax = self.g * t.y * self.slope_influence
			if abs(slope_ax) > self.static_friction_threshold or abs(self.c.velocity.x) > 1e-3:
				self.c.velocity.x += slope_ax * delta
		except Exception:
			pass

		# Stick: pequeña “presión” hacia la normal para que no salte en micro-baches
		try:
			self.c.velocity += n * (-self.stick_force * delta)
		except Exception:
			pass

		# Usar la normal como up_direction para move_and_slide
		return n
