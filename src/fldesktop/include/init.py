from fldesktop.include.subsystems import subsystems, init_seq, cleanup_seq
from fldesktop.include.supervisor import Supervisor

from pathlib import Path
import inspect
import logging


class Subsystem:
    def __init__(self, name: str, path: Path):

        self.name = name
        self.path = path

        self.sv = Supervisor(str(self.path))

    def start(self):

        self.sv.start()

    def stop(self):

        self.sv.stop()


class Init:
    def __init__(self, comm):

        self.comm = comm

        self.is_ready = False

        self.subsystems = {}

        self.preload_subsystems()

        self.done_tasks = []

    def start(self):

        self.mark_ready(False)

        logging.info(f"Running init...")

        for i in init_seq:

            self.comm.request(
                "tasksched", "schedule", lambda i=i: self.run_task(i)
            )

        self.comm.request("tasksched", "schedule", self.mark_ready)

    def stop(self):

        self.mark_ready(False)

        logging.info(f"Stopping...")

        for i in cleanup_seq:

            self.comm.request(
                "tasksched", "schedule", lambda i=i: self.run_task(i, True)
            )

        self.comm.request(
            "tasksched", "schedule", lambda: \
                self.comm.request("lifecycle", "quit")
        )

        self.comm.request(
            "tasksched", "schedule", lambda: self.mark_ready(False)
        )

    def run_task(self, task: str, stop: bool = False):

        logging.info(f"Running {"stop" if stop else "start"} task {task}...")

        if "." not in task: # start subsystem
            logging.info(
                f"{"Starting" if not stop else "Stopping"} subsystem {task}"
            )
            if task in self.subsystems:
                if not stop:
                    self.subsystems[task].start()
                    self.comm.wait_for_sv(f"{task}-core")
                else:
                    self.subsystems[task].stop()

            self.done_tasks.append(task)

        else: # start subsystem service
            logging.info(
                f"{"Starting" if not stop else "Stopping"} service {task}"
            )
            spl = task.split(".")
            if len(spl) >= 2:
                ss = spl[0]
                if ss in self.subsystems:
                    self.comm.wait_for_sv(f"{ss}-core")
                    self.comm.request(
                        f"{ss}-core",
                        "start_service" if not stop else "stop_service",
                        ".".join(spl[1:])
                    )

            if task in self.done_tasks:
                self.done_tasks.remove(task)

    def preload_subsystems(self):

        for name, ss in subsystems.items():
            try:
                logging.info(f"Preloading subsystem {name}")
                sscp = Path(inspect.getfile(ss))
                ssinst = Subsystem(name, sscp)
                self.subsystems[name] = ssinst
            except Exception as e:
                logging.error(f"Failed to preload subsystem {ss}: {e}")

    def mark_ready(self, ready: bool = True):
        self.is_ready = ready
        logging.info(f"Setting ready flag to {ready}")
