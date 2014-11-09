#!/bin/env python

import sys
import optparse
import time
from subprocess import Popen

import path_resolve
from lib.coroutines.scheduler import Scheduler


def exe_task(cmd):
	sh = (yield)
	p = Popen(cmd, shell=True)
	while True:
		# scheduler was stopped
		if (yield):
			break
		rc = p.poll()
		if rc is None:
			# running
			continue
		if rc:
			# bad exit
			print 'bad status'
			sh.stop()
			sys.exit(1)
		else:
			# good exit
			sh.add(exe_task(cmd))
			break

def timeout(end_time):
	sh = (yield)
	while True:
		if (yield):
			break
		if end_time <= time.time():
			sh.stop()
		time.sleep(0.01)

if __name__ == '__main__':
	parser = optparse.OptionParser()
	group = optparse.OptionGroup(parser, 'Some desc')
	group.add_option('-c', '--cmd',
		help='Name program and args (in quotas)')
	group.add_option('-r', '--rate',
		type='int',
		help='Count of simultaneously program')
	group.add_option('-d', '--duration',
		type='int',
		help='Timeout of executions in sec')
	parser.add_option_group(group)

	(options, _) = parser.parse_args()
	sh = Scheduler()
	sh.add(timeout(time.time() + options.duration))
	for _ in xrange(options.rate):
		sh.add(exe_task(options.cmd))
	sh.run()
