# res://Sonic/loop_path.py
from godot import exposed, export, Node2D, Area2D, Path2D, Vector2

@exposed
class LoopPath(Node2D):
	# -------- parámetros editables --------
	min_enter_speed   = export(float, default=220.0)   # baja esto para probar (p. ej. 120)
	require_on_floor  = export(bool,  default=True)
	ground_offset     = export(float, default=12.0)
	use_tangent_grav  = export(bool,  default=True)
	min_top_speed     = export(float, default=320.0)
	player_name_hint  = export(str,   default="Personaje")
	poll_enter        = export(bool,  default=True)    # sondeo de entrada (por si la señal no llega)
	poll_radius       = export(float, default=48.0)    # radio desde EnterZone para enganchar
	debug             = export(bool,  default=True)

	def _ready(self):
		# nodos
		self.path  = self.get_node("Path2D")
		self.curve = self.path.curve
		self.enter = self.get_node("EnterZone")

		# Asegurar Area2D de entrada
		if isinstance(self.enter, Area2D):
			try:
				self.enter.set_deferred("monitoring", True)
				self.enter.set_deferred("monitorable", True)
				# ver TODOS los cuerpos (20 bits en Godot 3.x)
				self.enter.set_deferred("collision_mask", (1 << 20) - 1)
			except Exception:
				pass
			# Conectar señales
			self.enter.connect("body_entered", self, "_on_enter_any")
			self.enter.connect("area_entered", self, "_on_enter_any")

		# estado runtime
		self.player = None
		self.s = 0.0
		self.v = 0.0

		if self.debug:
			try:
				print("[LoopPath] ready. EnterZone mask:", self.enter.collision_mask)
			except Exception:
				pass

	# ====== utilidades ======
	def _find_player_node(self):
		# 1) por nombre sugerido
		try:
			root = self.get_tree().get_root()
			n = root.find_node(self.player_name_hint, recursive=True, owned=True)
			if n is not None:
				return n
		except Exception:
			pass
		# 2) Por grupo "Player" (si lo usas)
		try:
			arr = self.get_tree().get_nodes_in_group("Player")
			if arr and len(arr) > 0:
				return arr[0]
		except Exception:
			pass
		# 3) Buscar un nodo cercano con los métodos requeridos
		try:
			root = self.get_tree().get_root()
			stack = [root]
			while stack:
				n = stack.pop()
				if hasattr(n, "attach_path_driver") and hasattr(n, "detach_path_driver"):
					return n
				try:
					for c in n.get_children():
						stack.append(c)
				except Exception:
					pass
		except Exception:
			pass
		return None

	def _to_player(self, node):
		# sube por padres hasta encontrar tu Personaje
		cur, depth = node, 0
		while cur is not None and depth < 6:
			if hasattr(cur, "attach_path_driver") and hasattr(cur, "detach_path_driver"):
				return cur
			try:
				cur = cur.get_parent()
			except Exception:
				break
			depth += 1
		return None

	def _closest_offset_safe(self, pos):
		try:
			return float(self.curve.get_closest_offset(pos))
		except Exception:
			bl = float(self.curve.get_baked_length())
			if bl <= 0.0:
				return 0.0
			steps = 96
			best_s, best_d = 0.0, 1e9
			for i in range(steps + 1):
				t = bl * i / steps
				p = self.curve.interpolate_baked(t)
				d = (p - pos).length()
				if d < best_d:
					best_d, best_s = d, t
			return best_s

	# ====== entrada por señal (Area2D) ======
	def _on_enter_any(self, obj):
		body = self._to_player(obj)
		if body is None:
			if self.debug:
				print("[LoopPath] enter from non-player:", getattr(obj, "name", obj))
			return
		self._try_attach(body)

	# ====== entrada por sondeo (fallback) ======
	def _process(self, delta):
		if not self.poll_enter or self.player is not None:
			return
		pl = self._find_player_node()
		if pl is None:
			return
		try:
			ez_pos = self.enter.global_position
		except Exception:
			return
		try:
			dist = (pl.global_position - ez_pos).length()
		except Exception:
			dist = 1e9
		if dist <= float(self.poll_radius):
			self._try_attach(pl)

	# ====== lógica de enganche ======
	def _try_attach(self, body):
		try:
			sp = float(body.velocity.length())
		except Exception:
			sp = 0.0
		if sp < float(self.min_enter_speed):
			if self.debug:
				print("[LoopPath] reject speed:", sp, "<", self.min_enter_speed)
			return
		if self.require_on_floor:
			try:
				if not body.is_on_floor():
					if self.debug:
						print("[LoopPath] reject: not on floor")
					return
			except Exception:
				return

		# enganchar
		self.s = self._closest_offset_safe(body.global_position)
		tan = self.curve.interpolate_baked_tangent(self.s)
		if tan.length() == 0:
			tan = Vector2(1, 0)
		t_hat = tan / tan.length()
		try:
			vel = body.velocity
		except Exception:
			vel = Vector2(0, 0)
		self.v = vel.length() * (1 if t_hat.dot(vel) >= 0 else -1)

		body.attach_path_driver(self)
		self.player = body
		if self.debug:
			print("[LoopPath] ATTACH s=%.1f v=%.1f" % (self.s, self.v))

	# ====== conducción mientras está enganchado ======
	def drive(self, delta, body):
		if body is None or body != self.player:
			return

		tan = self.curve.interpolate_baked_tangent(self.s)
		if tan.length() == 0:
			tan = Vector2(1, 0)
		t_hat = tan / tan.length()
		n_hat = Vector2(-t_hat.y, t_hat.x)

		if self.use_tangent_grav:
			g = float(getattr(body, "gravity", 900.0))
			self.v += Vector2(0, g).dot(t_hat) * delta

		self.s += self.v * delta
		total = float(self.curve.get_baked_length())

		if self.s <= 0.0 or self.s >= total:
			# salir por extremos
			out_tan = self.curve.interpolate_baked_tangent(
				max(0.0, min(total, self.s))
			)
			if out_tan.length() == 0:
				out_tan = Vector2(1, 0)
			self._detach(out_tan.normalized() * self.v)
			return

		pos = self.curve.interpolate_baked(self.s)
		body.global_position = pos - n_hat * float(self.ground_offset)
		body.velocity = t_hat * self.v

		if abs(n_hat.y) > 0.95 and abs(self.v) < float(self.min_top_speed):
			self._detach(t_hat * self.v)

	def _detach(self, out_velocity):
		if self.player and self.debug:
			print("[LoopPath] DETACH v=", out_velocity)
		if self.player:
			try:
				self.player.detach_path_driver(self, out_velocity=out_velocity)
			except Exception:
				pass
		self.player = None
		self.s = 0.0
		self.v = 0.0
