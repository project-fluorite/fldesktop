import os
import time
import logging


class Lifecycle:
    def __init__(self, core):

        self.core = core
        self.core.comm.local_register(
            "lifecycle", {
                "quit": self.quit,
                "panic": self.panic,
                "shutdown": self.shutdown,
                "reboot": self.reboot,
                "is_dev_environment": self.get_is_dev_env,
                "is_ready": self.get_is_ready,
                "is_task_done": self.is_task_done
            }
        )

        self.is_dev_environment = any(
            os.path.exists(p) for p in (
                "/run/systemd/system",
                "/run/runit",
                "/run/openrc"
            )
        )

        self.alive = True

        self.core.comm.collect()
        self.core.init.start()

    def mainloop(self):
        while self.alive:

            try:
                self.tick()
            except KeyboardInterrupt:
                self.logout()

    def tick(self):

        self.core.tasksched.tick()

        time.sleep(0.0001)

    def quit(self):

        self.alive = False

    def panic(self, reason: str = ""):

        logging.critical(
            "Something very bad had occured, " +
            "fldesktop is now halting. " + str(reason)
        )

        while True:
            time.sleep(1)

    def get_is_dev_env(self):
        return self.is_dev_environment

    def get_is_ready(self):
        return self.core.init.is_ready

    def is_task_done(self, task: str):
        return task in self.core.init.done_tasks

    def logout(self):

        self.core.init.stop()
        self.core.socket.stop()
        self.core.comm.request("tasksched", "schedule", self.quit)

    def shutdown(self):
        self.logout()

    def reboot(self):
        self.logout()
