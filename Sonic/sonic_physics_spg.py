# res://Sonic/sonic_physics.py
# Física de Sonic basada en la Sonic Physics Guide (SPG). FASE A: suelo plano.
# Referencia: docs/10-forces.md ("Running") y docs/12-main-game-loop.md del repo
# trentbrew/sonic-physics-guide.
#
# UNIDADES: píxeles por frame (px/f) y px/f por frame, a 60 Hz fijos. No se usa delta.
#
# REGLA DE UNIDADES: gs, xsp y ysp (px/f) viven SOLO en este módulo.
#   - Código externo cambia la velocidad con set_ground_speed() / set_air_speed().
#   - c.velocity (px/s) es solo la entrada/salida de move_and_slide; no es estado.
#   PENDIENTE: todavía escriben c.velocity directamente (y este módulo los ignora):
#   personaje.py (external_boost, hit, death, respawn, spindash, roll, loops),
#   loop_path.py, y como respaldo los 4 resortes y DashPanel.py.
#
# FUERA DE ALCANCE EN ESTA FASE: salto, roll, spindash, pendientes (slope factor),
# control aéreo, daño, look up/down, crouch y casi todas las animaciones.
# Ver docs/animaciones-legacy.md.

import math
from godot import Vector2, Input, Engine

FPS = 60.0
UP = Vector2(0, -1)
SUBPX = 256.0  # 1 píxel = 256 subpíxeles

# ---------------- Constantes SPG (Sonic, normal) ----------------
ACC = 12 / SUBPX       # 0.046875  aceleración con input
DEC = 128 / SUBPX      # 0.5       desaceleración al presionar contra el movimiento
FRC = 12 / SUBPX       # 0.046875  fricción sin input
TOP = 6.0              # tope de velocidad por input (S2+: no recorta si ya vas más rápido)
DEC_QUIRK = 128 / SUBPX  # 0.5     al cruzar 0 frenando, gs salta a ±0.5 al otro lado

# ---------------- Provisionales (no son de esta fase) ----------------
# Solo para no flotar al salir de un borde. El aire se hace en su propia fase.
GRV = 56 / SUBPX       # 0.21875
MAX_FALL = 16.0        # PROVISIONAL: la guía solo lista un tope de caída para Sonic CD

# ---------------- Ajustes de Godot (no vienen de la guía) ----------------
FLOOR_MAX_ANGLE = math.radians(65.0)  # mismo valor que usaba el sistema viejo
SNAP_MIN = 4.0         # px; largo del snap al suelo = SNAP_MIN + |gs|, hasta SNAP_MAX
SNAP_MAX = 20.0

# ---------------- Animación mínima (docs/21-animations.md) ----------------
RUN_ANIM_SPEED = 6.0       # |gs| >= 6 -> run
RUNMAX_ANIM_SPEED = 10.0   # |gs| >= 10 -> runmax (en la guía es el "dash" de Sonic CD)
BRAKE_ANIM_SPEED = 4.0     # girar con |gs| >= 4 -> break


def _sign(x):
	return (x > 0) - (x < 0)


class SonicPhysics:
	def __init__(self, character):
		self.c = character
		self.gs = 0.0          # ground speed (px/f), fuente de verdad en el suelo
		self.xsp = 0.0         # px/f
		self.ysp = 0.0         # px/f
		self.grounded = False  # empieza en el aire: cae y aterriza
		self.up = UP           # normal del suelo actual (up_direction para Godot)
		self._brake_frames = 0
		self._anim = None

		ips = Engine.iterations_per_second
		if ips != 60:
			print("[SonicPhysics] AVISO: physics_fps = %s. Las constantes asumen 60 Hz; todo irá %.2fx de rápido." % (ips, ips / 60.0))

	# =========================================================
	#   API para código externo (regla de unidades)
	# =========================================================
	def set_ground_speed(self, gs):
		"""Fija la velocidad sobre el suelo en px/f. Sigue en el suelo."""
		self.gs = float(gs)

	def set_air_speed(self, xsp, ysp):
		"""Fija la velocidad en px/f y pasa al aire."""
		self.xsp = float(xsp)
		self.ysp = float(ysp)
		self.grounded = False
		self.up = UP

	def get_speed(self):
		return self.xsp, self.ysp

	# =========================================================
	#   Paso de física (1 llamada = 1 frame)
	# =========================================================
	def step(self, delta):
		c = self.c

		# Muerte: se mantiene el código viejo (px/s) hasta rehacer daño/muerte.
		if getattr(c, "is_dead", False):
			c._death_tick(delta)
			return

		left = Input.is_action_pressed("ui_left")
		right = Input.is_action_pressed("ui_right")

		# ---- antes de mover ----
		if self.grounded:
			self._ground_input(left, right)
			# gs -> xsp/ysp a lo largo de la superficie (tangente = normal rotada 90°).
			# Sin slope factor todavía: en pendientes se mueve, pero la pendiente no acelera ni frena.
			n = self.up
			self.xsp = self.gs * -n.y
			self.ysp = self.gs * n.x
		# En el aire no hay nada antes de mover (sin control aéreo en esta fase).

		# ---- mover (único punto donde se convierte a px/s) ----
		vel = Vector2(self.xsp * FPS, self.ysp * FPS)
		perf = getattr(c, "_perf", None)
		if perf: perf.engine_begin()
		if self.grounded:
			snap = -self.up * min(SNAP_MAX, SNAP_MIN + abs(self.gs))
			out = c.move_and_slide_with_snap(vel, snap, self.up, True, 4, FLOOR_MAX_ANGLE)
		else:
			out = c.move_and_slide(vel, UP, True, 4, FLOOR_MAX_ANGLE)
		if perf: perf.engine_end()

		# ---- después de mover ----
		on_floor = c.is_on_floor()
		if self.grounded:
			if on_floor:
				self.up = self._floor_up()
				if c.is_on_wall() and self._wall_ahead():
					self.gs = 0.0
			else:
				# Se salió del suelo (borde): sigue con la velocidad que llevaba.
				self.grounded = False
				self.up = UP
				self.xsp = out.x / FPS
				self.ysp = out.y / FPS
		else:
			self.xsp = out.x / FPS
			self.ysp = out.y / FPS
			if on_floor:
				self._land()
			else:
				# Gravedad DESPUÉS de mover: así lo hace el juego (define la altura del salto).
				self.ysp = min(self.ysp + GRV, MAX_FALL)

		self._animate(left, right)

	# =========================================================
	#   Suelo: aceleración, desaceleración, fricción (SPG "Running")
	# =========================================================
	def _ground_input(self, left, right):
		gs = self.gs
		# Con izquierda y derecha a la vez se ejecutan los dos bloques (como en el juego).
		if left:
			if gs > 0:
				gs -= DEC
				if gs <= 0:
					gs = -DEC_QUIRK
			elif gs > -TOP:
				gs -= ACC
				if gs <= -TOP:
					gs = -TOP
		if right:
			if gs < 0:
				gs += DEC
				if gs >= 0:
					gs = DEC_QUIRK
			elif gs < TOP:
				gs += ACC
				if gs >= TOP:
					gs = TOP
		if not left and not right:
			gs -= min(abs(gs), FRC) * _sign(gs)
		self.gs = gs

	def _floor_up(self):
		n = self.c.get_floor_normal()
		if n.length() > 1e-6:
			return n.normalized()
		return UP

	def _wall_ahead(self):
		# ¿Alguna colisión de este frame es una pared en la dirección de gs?
		c = self.c
		for i in range(c.get_slide_count()):
			n = c.get_slide_collision(i).normal
			if n.x * self.gs < 0 and abs(n.x) > abs(n.y):
				return True
		return False

	def _land(self):
		# PROVISIONAL: proyecta la velocidad sobre la superficie. En plano da gs = xsp,
		# que es lo que dice la guía. Las reglas por ángulo se hacen en la fase de pendientes.
		self.grounded = True
		self.up = self._floor_up()
		n = self.up
		self.gs = self.xsp * -n.y + self.ysp * n.x
		self.ysp = 0.0

	# =========================================================
	#   Animación mínima (idle / walk / run / runmax / break / fall)
	# =========================================================
	def _animate(self, left, right):
		c = self.c
		ap = c.anim_player
		if ap is None:
			return
		gs = self.gs
		agsp = abs(gs)

		if not self.grounded:
			self._brake_frames = 0
			anim = "fall"
		else:
			# Girar a alta velocidad: break hasta que la animación termine (comportamiento S2/S3K).
			turning = (left and gs > 0) or (right and gs < 0)
			if turning and agsp >= BRAKE_ANIM_SPEED and self._brake_frames <= 0:
				self._brake_frames = max(1, int(round(c._anim_len.get("break", 0.0) * FPS)))
			if self._brake_frames > 0:
				self._brake_frames -= 1
				anim = "break"
			elif gs == 0.0:
				anim = "idle"
			elif agsp >= RUNMAX_ANIM_SPEED:
				anim = "runmax"
			elif agsp >= RUN_ANIM_SPEED:
				anim = "run"
			else:
				anim = "walk"

		if anim != self._anim:
			ap.play(anim)
			self._anim = anim

		# El sprite base mira a la izquierda. Durante el break no se voltea.
		if self._brake_frames <= 0:
			if gs > 0:
				c.sprite.flip_h = True
			elif gs < 0:
				c.sprite.flip_h = False
