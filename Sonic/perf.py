# res://Sonic/perf.py
# Mide cuánto cuesta SonicPhysics.step() cada frame.
#   total  = step() completo
#   engine = solo las llamadas a move_and_slide* (motor, C++)
#   python = total - engine  -> lo que cuesta nuestra lógica en Python
# Acumula durante `window` frames e imprime una sola línea (un print por frame
# costaría más que lo que se está midiendo).
from godot import OS

FRAME_BUDGET_US = 1000000.0 / 60.0


class StepProfiler:
	def __init__(self, window=120, label="step"):
		self.window = max(1, int(window))
		self.label = label
		self._now = OS.get_ticks_usec  # se guarda el método: evita buscar OS cada llamada
		self._t0 = 0
		self._e0 = 0
		self._engine_frame = 0
		self._reset()
		self.timer_overhead = self._calibrate()
		print("[perf] costo de un par de OS.get_ticks_usec(): %.2f us (ruido incluido en cada medición)" % self.timer_overhead)

	def _reset(self):
		self._n = 0
		self._sum_total = 0
		self._sum_engine = 0
		self._max_total = 0
		self._max_python = 0

	def _calibrate(self, n=1000):
		now = self._now
		start = now()
		for _ in range(n):
			now()
			now()
		return (now() - start) / float(n)

	# --- step completo ---
	def begin(self):
		self._engine_frame = 0
		self._t0 = self._now()

	def end(self):
		total = self._now() - self._t0
		engine = self._engine_frame
		python = total - engine
		self._n += 1
		self._sum_total += total
		self._sum_engine += engine
		if total > self._max_total:
			self._max_total = total
		if python > self._max_python:
			self._max_python = python
		if self._n >= self.window:
			self._report()
			self._reset()

	# --- solo la llamada al motor (puede haber varias por frame) ---
	def engine_begin(self):
		self._e0 = self._now()

	def engine_end(self):
		self._engine_frame += self._now() - self._e0

	def _report(self):
		n = float(self._n)
		avg_total = self._sum_total / n
		avg_engine = self._sum_engine / n
		avg_python = avg_total - avg_engine
		print("[perf] %s | %d frames | total %.1f us (max %d) | python %.1f us (max %d) | motor %.1f us | %.2f%% del frame"
			% (self.label, self._n, avg_total, self._max_total, avg_python, self._max_python,
			   avg_engine, 100.0 * avg_total / FRAME_BUDGET_US))
