#!/bin/env python

def starter(fn):
	def wrap(*args, **kwargs):
		obj = fn(*args, **kwargs)
		obj.next()
		return obj
	return wrap

#-----------------------------------------------------
def pusher(iterable, target):
	for i in iterable:
		target.send(i)

#-----------------------------------------------------
@starter
def cfilter(pred, target):
	while True:
		x = (yield)
		if pred(x):
			target.send(x)

#-----------------------------------------------------
@starter
def cmap(fn, target):
	while True:
		arg = (yield)
		target.send(fn(arg))

#-----------------------------------------------------
@starter
def broadcast(*targets):
	while True:
		x = (yield)
		for t in targets:
			t.send(x)

#-----------------------------------------------------
@starter
def printer(fmt='%s'):
	while True:
		print fmt %((yield))

#-----------------------------------------------------
@starter
def caller(fn):
	while True:
		fn((yield))

#-----------------------------------------------------
def chain(*steps):
	steps = steps[::-1]
	arg = steps[0]
	if callable(arg):
		arg = arg()
	for s in steps[1:]:
		if callable(s):
			arg = s(srg)
		else:
			arg = s[0](*(tuple(s[1:])+(arg,)))
	return arg


if __name__ == '__main__':
	src = xrange(8)
	res = []
	expect_res = ['4040', '5050', '6060', '7070']
	pusher(
		src,
		broadcast(
			printer('val: %s'),
			chain(
				(cfilter, lambda x: x > 3),
				(cmap, lambda x: x*10),
				(cmap, str),
				(cmap, lambda x: x*2),
				caller(res.append),
			),
		)
	)
	if res == expect_res:
		print 'Pass'
	else:
		print('Fail, res: %s, expect_res: %s' %
			(res, expect_res))

