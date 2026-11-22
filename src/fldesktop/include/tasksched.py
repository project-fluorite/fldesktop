import queue
import logging


class TaskSched:
    def __init__(self, comm):

        self.comm = comm
        self.comm.local_register(
            "tasksched", {
                "schedule": self.schedule
            }
        )

        self.tasks = queue.Queue()

    def tick(self):

        task = self.tasks.get()
        #logging.debug(f"running task {task}")
        task()

    def schedule(self, task):

        self.tasks.put(task)
