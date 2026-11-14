# res://Sonic/bench.py
# Microbenchmark: ¿cuánto cuesta una llamada de Python a Godot comparada con Python puro?
# Se corre UNA vez, en el primer _physics_process del jugador, si el export
# `bench_on_start` está activado. No toca la física ni el estado del juego
# (move_and_slide se llama con velocidad cero).
#
# Método: cada prueba repite la operación N veces dentro de un bucle, 3 rondas, y se
# queda con la ronda más rápida (menos ruido). Al resultado se le resta el costo del
# bucle vacío, así que "neto" es el costo de la operación sola.
from godot import OS, Input, Engine, Vector2

N = 2000
ROUNDS = 3


def _time_loop(fn, n):
	now = OS.get_ticks_usec
	t0 = now()
	fn(n)
	return now() - t0


def _best(fn):
	return min(_time_loop(fn, N) for _ in range(ROUNDS))


class _Plain:
	"""Objeto de Python puro, para comparar acceso a atributos."""
	def __init__(self):
		self.gs = 3.0


def run_bridge_bench(body):
	plain = _Plain()
	sprite = getattr(body, "sprite", None)
	anim = getattr(body, "anim_player", None)
	v = Vector2(1.0, 2.0)
	is_pressed = Input.is_action_pressed  # método guardado: sin buscar el atributo cada vez

	space = None
	try:
		space = body.get_world_2d().direct_space_state
	except Exception as e:
		print("[bench] sin direct_space_state:", e)
	p0 = body.global_position
	p1 = p0 + Vector2(0, 32)

	# Cada prueba es una función que repite la operación n veces.
	def empty(n):
		for _ in range(n):
			pass

	def py_math(n):
		a, b, c = 1.5, 2.5, 3.5
		for _ in range(n):
			x = a * b + c

	def py_attr(n):
		for _ in range(n):
			x = plain.gs

	def py_tuple(n):
		for _ in range(n):
			t = (1.0, 2.0)

	def g_vector2_new(n):
		for _ in range(n):
			t = Vector2(1.0, 2.0)

	def g_vector2_mul(n):
		for _ in range(n):
			t = v * 60.0

	def g_vector2_x(n):
		for _ in range(n):
			x = v.x

	def g_input(n):
		for _ in range(n):
			x = Input.is_action_pressed("ui_left")

	def g_input_cached(n):
		for _ in range(n):
			x = is_pressed("ui_left")

	def g_input_just(n):
		for _ in range(n):
			x = Input.is_action_just_pressed("jump")

	def g_is_on_floor(n):
		for _ in range(n):
			x = body.is_on_floor()

	def g_floor_normal(n):
		for _ in range(n):
			x = body.get_floor_normal()

	def g_global_pos(n):
		for _ in range(n):
			x = body.global_position

	def g_engine_prop(n):
		for _ in range(n):
			x = Engine.iterations_per_second

	def g_ticks(n):
		now = OS.get_ticks_usec
		for _ in range(n):
			x = now()

	def g_sprite_flip(n):
		for _ in range(n):
			sprite.flip_h = True

	def g_anim_current(n):
		for _ in range(n):
			x = anim.current_animation

	def g_move_zero(n):
		z = Vector2(0, 0)
		for _ in range(n):
			body.move_and_slide(z)

	def g_raycast(n):
		for _ in range(n):
			x = space.intersect_ray(p0, p1)

	tests = [
		("python: bucle vacío (referencia)", empty),
		("python: a*b+c con floats", py_math),
		("python: leer atributo de objeto Python", py_attr),
		("python: crear tupla (1.0, 2.0)", py_tuple),
		("godot: crear Vector2(1, 2)", g_vector2_new),
		("godot: Vector2 * 60.0", g_vector2_mul),
		("godot: leer Vector2.x", g_vector2_x),
		("godot: Input.is_action_pressed", g_input),
		("godot: is_action_pressed (método guardado)", g_input_cached),
		("godot: Input.is_action_just_pressed", g_input_just),
		("godot: body.is_on_floor()", g_is_on_floor),
		("godot: body.get_floor_normal()", g_floor_normal),
		("godot: leer body.global_position", g_global_pos),
		("godot: leer Engine.iterations_per_second", g_engine_prop),
		("godot: OS.get_ticks_usec()", g_ticks),
	]
	if sprite is not None:
		tests.append(("godot: sprite.flip_h = True", g_sprite_flip))
	if anim is not None:
		tests.append(("godot: anim_player.current_animation", g_anim_current))
	tests.append(("godot: move_and_slide(Vector2(0,0))", g_move_zero))
	if space is not None:
		tests.append(("godot: intersect_ray (32 px)", g_raycast))

	print("[bench] ---- Python vs Godot: %d repeticiones, mejor de %d rondas ----" % (N, ROUNDS))
	base_us = _best(empty)
	for name, fn in tests:
		try:
			us = _best(fn)
		except Exception as e:
			print("[bench] %-46s ERROR: %s" % (name, e))
			continue
		per_ns = us * 1000.0 / N
		net_ns = (us - base_us) * 1000.0 / N
		print("[bench] %-46s %8.0f ns/op   neto %8.0f ns" % (name, per_ns, net_ns))
	print("[bench] ---- fin. Para no repetirlo: desactiva bench_on_start en el inspector ----")
