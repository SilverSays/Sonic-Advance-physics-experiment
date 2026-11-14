# res://Sonic/sonic_physics.py
# Física de Sonic basada en la Sonic Physics Guide (SPG).
# FASES HECHAS: A1 suelo plano · A2 salto y aire.
# Referencia: docs/10-forces.md ("Running", "Jumping", "Midair"),
# docs/11-forces-subtopics/{jumping,air-state}.md y docs/12-main-game-loop.md
# del repo trentbrew/sonic-physics-guide.
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
# FUERA DE ALCANCE TODAVÍA: roll, spindash, pendientes (slope factor), daño,
# look up/down, crouch y casi todas las animaciones.
# Ver docs/legacy-animations.md.

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

# ---------------- Constantes SPG: salto y aire (fase A2) ----------------
JMP = 6.5              # 6 px + 128 spx: fuerza de salto, a lo largo de la normal del suelo
JMP_RELEASE = -4.0     # salto variable: al soltar el botón, ysp no puede ser menor que -4
AIR_ACC = 24 / SUBPX   # 0.09375  aceleración en el aire (el doble que en suelo)
GRV = 56 / SUBPX       # 0.21875  gravedad, se aplica DESPUÉS de mover
AIR_DRAG_YMIN = -4.0   # el air drag solo actúa con -4 < ysp < 0 (cerca del ápice del salto)
MAX_FALL = 16.0        # PROVISIONAL: la guía solo lista un tope de caída para Sonic CD
JUMP_DELAY = True      # fiel a Genesis: el frame en que salta, Sonic no se mueve
					   # (Sonic Mania lo quitó; candidato a ajuste en la fase A5)

# ---------------- Ajustes de Godot (no vienen de la guía) ----------------
FLOOR_MAX_ANGLE = math.radians(65.0)  # mismo valor que usaba el sistema viejo
SNAP_MIN = 4.0         # px; largo del snap al suelo = SNAP_MIN + |gs|, hasta SNAP_MAX
SNAP_MAX = 20.0

# ---------------- Animación mínima (docs/21-animations.md) ----------------
# idle / walk / run / runmax / break en suelo; jump (salto) o fall (caer de un borde) en el aire.
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
		self.jumping = False    # en el aire por un salto (habilita el salto variable)
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
		self.jumping = False   # un resorte o un boost no es un salto: sin salto variable
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
		jump_pressed = Input.is_action_just_pressed("jump")
		jump_held = Input.is_action_pressed("jump")

		# ---- antes de mover ----
		if self.grounded:
			# Orden SPG en suelo: (slope factor, fase A4) -> salto -> input/fricción -> mover.
			if jump_pressed:
				self._jump()
				if JUMP_DELAY:
					# El juego original sale del ciclo de movimiento en el frame del salto.
					self._animate(left, right)
					return
			else:
				self._ground_input(left, right)
				# gs -> xsp/ysp a lo largo de la superficie (tangente = normal rotada 90°).
				# Sin slope factor todavía: en pendientes se mueve, pero la pendiente no acelera ni frena.
				n = self.up
				self.xsp = self.gs * -n.y
				self.ysp = self.gs * n.x
		else:
			# Orden SPG en el aire (docs/12-main-game-loop.md):
			# salto variable -> input -> air drag -> mover -> gravedad.
			if self.jumping and not jump_held and self.ysp < JMP_RELEASE:
				self.ysp = JMP_RELEASE
			self._air_input(left, right)
			self._air_drag()

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

	# =========================================================
	#   Salto y aire (SPG "Jumping", "Midair", "Air State")
	# =========================================================
	def _jump(self):
		# La guía resta jump_force * (sin, cos) del ángulo del suelo: es saltar a lo largo
		# de la normal. Se SUMA a la velocidad que ya traía (xsp/ysp vienen de gs).
		n = self.up
		self.xsp += JMP * n.x
		self.ysp += JMP * n.y
		self.grounded = False
		self.jumping = True
		self.up = UP
		self._brake_frames = 0

	def _air_input(self, left, right):
		# "Limitado por top_speed". Igual que en suelo, se usa la versión S2+: el input no
		# acelera por encima del tope, pero si ya vas más rápido (resorte, rampa) no te recorta.
		# DUDA: no está confirmado si S1/S2 recortaban en el aire. Hoy no importa: sin
		# pendientes ni resortes, xsp no puede pasar de 6.
		x = self.xsp
		if left and x > -TOP:
			x -= AIR_ACC
			if x < -TOP:
				x = -TOP
		if right and x < TOP:
			x += AIR_ACC
			if x > TOP:
				x = TOP
		self.xsp = x

	def _air_drag(self):
		# Solo cerca del ápice (-4 < ysp < 0): resta ~1/32 de xsp por frame.
		# El Markdown de la SPG dice "floor(X Speed >> 2) / 256", que parece mal convertido.
		# Se usa xsp -= floor(xsp * 8) / 256, que equivale a (subpíxeles >> 5) / 256.
		# HIPÓTESIS: sale de memoria (wiki y desensamblado de S2). Verificar en la wiki.
		if AIR_DRAG_YMIN < self.ysp < 0:
			self.xsp -= math.floor(self.xsp * 8.0) / SUBPX

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
		self.jumping = False
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
			anim = "jump" if self.jumping else "fall"
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

		# El sprite base mira a la izquierda. En suelo mira según gs (durante el break no se
		# voltea); en el aire mira hacia donde se presiona.
		if not self.grounded:
			if right and not left:
				c.sprite.flip_h = True
			elif left and not right:
				c.sprite.flip_h = False
		elif self._brake_frames <= 0:
			if gs > 0:
				c.sprite.flip_h = True
			elif gs < 0:
				c.sprite.flip_h = False
