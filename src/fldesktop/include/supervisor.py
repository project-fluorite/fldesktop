from pathlib import Path
import subprocess
import threading
import logging


class SVWorker:
    def __init__(self, fpath: str):
        self.fpath = fpath
        self.stop = threading.Event()

        self.proc = None

    def run(self):
        try:
            while not self.stop.is_set():
                if not self.proc or self.proc.poll() is not None:
                    self._respawn()

                self.stop.wait(0.5)
        finally:
            # Сначала гасим процесс (закроет pipe -> reader получит EOF),
            # потом останавливаем потоки.
            self.kill()

    def _respawn(self):
        # корректно застрелить старый, если был
        if self.proc and self.proc.poll() is None:
            self.kill()

        self.proc = None

        self.spawn()

    def spawn(self):
        args = ["/usr/bin/env", "/bin/python", self.fpath]

        proc = subprocess.Popen(
            args,
            cwd=str(Path(__file__).parent.parent.parent),
            start_new_session=True
        )
        self.proc = proc

        logging.debug(f"Spawned new python instance")

    def kill(self):
        proc = self.proc
        if not proc:
            return
        if proc.poll() is not None:
            return

        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()


class Supervisor:
    def __init__(self, fpath):
        self.worker = SVWorker(fpath)
        self.worker_thread = threading.Thread(target=self.worker.run, daemon=True)

    def start(self):
        self.worker_thread.start()

    def stop(self):
        self.worker.stop.set()
        self.worker_thread.join(timeout=10)
