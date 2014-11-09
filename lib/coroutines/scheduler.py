#!/bin/env python


class Scheduler(object):
	#TODO: whay as class attr?
	_stop_flag = None
	_tick = 0

	def __init__(self):
		self._queue = []

	@property
	def tick(self):
		return self._tick

	def run(self):
		self._stop_flag = False
		self._tick = 1

		for t in self._queue:
			t.next()
			t.send(self)

		while self._queue:
			for t in self._queue[:]:
				try:
					t.send(self._stop_flag)
				except StopIteration:
					self._queue.remove(t)
			self._tick += 1

	def stop(self):
		self._stop_flag = True

	def add(self, task):
		if self._stop_flag:
			return

		if self._tick:
			task.next()
			task.send(self)
		self._queue.append(task)
		return task


def stop_at(tick):
	sh = (yield)
	while True:
		if (yield):
			break
		if sh.tick >= tick:
			sh.stop()

def respawner(fn = lambda: None):
	sh = (yield)
	# stop flag
	if not (yield):
		fn()
		print 'Respawn, tick: %s' % sh.tick
		sh.add(respawner(fn))

if __name__ == '__main__':
	res = []
	res_expect = range(1, 11)
	sh = Scheduler()
	sh.add(stop_at(11))
	sh.add(respawner(lambda: res.append(sh.tick)))
	sh.run()
	if res == res_expect:
		print 'Pass'
	else:
		print('Fail, res: %s, res_expect: %s' %
				(res, res_expect))
