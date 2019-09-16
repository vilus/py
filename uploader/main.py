import collections
import itertools
import threading
import queue
import time
import random
import multiprocessing as mp


# TODO: add trap SIGINT ?

Progress = collections.namedtuple('Progress', 'uploading, done, error, total')


def upload(q_in, q_out):
    while True:
        file_name = q_in.get()
        if file_name is None:
            break

        try:
            q_out.put((file_name, 'uploading'))  # TODO: hardcode
            # --------
            time.sleep(random.randint(1, 2))
            if file_name == '4th':
                raise RuntimeError
            # --------
        # except Full ?
        except Exception:
            q_out.put((file_name, 'error'))  # TODO: hardcode
        else:
            q_out.put((file_name, 'done'))  # TODO: hardcode


def report(q_in, report_dict, q_out):
    while True:
        file_name, status = q_in.get()
        if file_name is None:
            break

        report_dict[file_name] = status

        statuses = list(report_dict.values())
        progr = Progress(done=statuses.count('done'),
                         uploading=statuses.count('uploading'),
                         error=statuses.count('error'),
                         total=len(statuses))  # TODO: hardcode

        q_out.put(progr)


class Uploader:
    def __init__(self, files_list, max_proc, q_progress):
        self.manager = mp.Manager()
        self.q_progress = q_progress

        self.q_file_names = self.manager.Queue()
        [self.q_file_names.put(f) for f in files_list]

        self.q_statuses = self.manager.Queue()

        self.report = {f: 'pending' for f in files_list}
        self.reporter_thread = threading.Thread(target=report,
                                                args=(self.q_statuses, self.report, self.q_progress),
                                                daemon=False)

        self.max_proc = max_proc
        self.loaders = mp.Pool(max_proc)
        self.terminated = False

    def start(self):
        self.reporter_thread.start()
        self.loaders.starmap_async(upload,
                                   itertools.repeat([self.q_file_names, self.q_statuses], self.max_proc))

    def is_active(self):
        if self.terminated:
            return

        statuses = list(self.report.values())
        return (self.q_file_names.qsize() or
                'pending' in statuses or
                'uploading' in statuses)

    def terminate(self):
        if self.terminated:
            return

        self.loaders.terminate()

        self.q_statuses.put((None, None))
        self.reporter_thread.join()
        self.terminated = True


fl = ['1th', '2th', '3th', '4th', '5th', '6th', '7th']
q = queue.Queue()
uploader = Uploader(fl, 5, q)
uploader.start()

while uploader.is_active():
    progress = q.get()
    print(f'uploading: {progress.uploading}, done: {progress.done}, '
          f'error: {progress.error}, total: {progress.total}')

print(uploader.report)
uploader.terminate()
