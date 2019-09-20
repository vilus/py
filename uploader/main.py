import collections
import copy
import functools
import itertools
import multiprocessing as mp
import queue
import random
import threading
import time
import uuid
from datetime import datetime

Progress = collections.namedtuple('Progress', 'pending, started, done, error, total')


def dummy(file_name):
    time.sleep(random.randint(2, 4))
    if file_name in ['4th', '5th']:
        raise RuntimeError('dummy')


class TaskStatus:
    PENDING = 'pending'
    STARTED = 'started'
    ERROR = 'error'
    DONE = 'done'

    def __init__(self, alias=None, timestamp=None, status=PENDING, where=None, msg=None):
        self.alias = alias if alias else str(uuid.uuid4())
        self.timestamp = timestamp if timestamp else datetime.utcnow()
        self.status = status
        self.where = where
        self.msg = msg

    def _update(self, status, timestamp=None, where=None):
        self.status = status
        self.timestamp = timestamp if timestamp else datetime.utcnow()
        self.where = where if where else self.where

    def started(self, timestamp=None, where=None):
        self._update(status=self.STARTED, timestamp=timestamp, where=where)
        return self

    def failed(self, timestamp=None, where=None, msg=None):
        self._update(status=self.ERROR, timestamp=timestamp, where=where)
        self.msg = msg if msg else self.msg
        return self

    def done(self, timestamp=None, where=None):
        self._update(status=self.DONE, timestamp=timestamp, where=where)
        return self

    def clone(self):
        return copy.deepcopy(self)

    def __str__(self):
        return f'Task status: {self.alias}, {self.status}, {self.timestamp}, {self.where}, {self.msg}'


class Task:
    def __init__(self, run_func, status=None):
        self.run_func = run_func
        self.status = status if status else TaskStatus()

    def run(self):
        res = None
        try:
            res = self.run_func()
        except Exception as e:
            self.status.failed(msg=repr(e))
        else:
            self.status.done()
        return res


class Report:
    def __init__(self):
        self.current = {}
        self.history = []

    def add_task_status(self, task_status):
        self.current[task_status.alias] = task_status.status
        self.history.append(task_status.clone())

    def progress(self):
        statuses = list(self.current.values())
        progress = Progress(pending=statuses.count(TaskStatus.PENDING),
                            started=statuses.count(TaskStatus.STARTED),
                            done=statuses.count(TaskStatus.DONE),
                            error=statuses.count(TaskStatus.ERROR),
                            total=len(statuses))
        return progress

    def __str__(self):
        return str(self.current)


def worker(q_in, q_out, get_where=lambda: mp.current_process().name):
    while True:
        task = q_in.get()

        if task is None:
            break

        q_out.put(task.status.started(where=get_where()))
        task.run()
        q_out.put(task.status)


def reduce(q_in, report, q_out):
    while True:
        task_status = q_in.get()
        if task_status is None:
            break

        # no need sync until in wan thread
        report.add_task_status(task_status)

        q_out.put(report.progress())


class Uploader:
    def __init__(self, file_names, max_proc, q_progress, upload_fn=None):
        self.upload_fn = upload_fn if upload_fn else dummy
        self.manager = mp.Manager()
        self.q_progress = q_progress

        self.report = Report()
        self.q_tasks = self.manager.Queue()

        for file_name in file_names:
            task = Task(functools.partial(self.upload_fn, file_name), TaskStatus(alias=file_name))
            self.report.add_task_status(task.status)
            self.q_tasks.put(task)

        self.q_statuses = self.manager.Queue()

        self.reporter_thread = threading.Thread(target=reduce,
                                                args=(self.q_statuses, self.report, self.q_progress),
                                                daemon=False)

        self.max_proc = max_proc
        self.loaders = mp.Pool(max_proc)
        self.terminated = False

    def start(self):
        self.reporter_thread.start()
        self.loaders.starmap_async(worker,
                                   itertools.repeat([self.q_tasks, self.q_statuses], self.max_proc))

    def is_active(self):
        if self.terminated:
            return

        progress = self.report.progress()
        return (self.q_tasks.qsize() or
                progress.pending > 0 or
                progress.started > 0)

    def terminate(self):
        if self.terminated:
            return

        self.loaders.terminate()

        self.q_statuses.put(None)
        self.reporter_thread.join()
        self.terminated = True


fl = ['1th', '2th', '3th', '4th', '5th', '6th', '7th']
q = queue.Queue()
uploader = Uploader(fl, 5, q)
uploader.start()

while uploader.is_active():
    progress = q.get()
    print(f'uploading: {progress.started}, done: {progress.done}, '
          f'error: {progress.error}, total: {progress.total}')

uploader.terminate()
print(uploader.report)

