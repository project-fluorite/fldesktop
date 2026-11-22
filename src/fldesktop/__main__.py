from fldesktop.include import (
    lifecycle, init, comm, logconfig, tasksched, socket
)

import logging


class Main:
    def __init__(self):

        logging.basicConfig(
            level=logging.DEBUG if True else logging.INFO,
            format="%(asctime)s: %(filename)s: %(levelname)s: %(message)s",
            handlers=[logconfig.handler]
        )

        logging.info(f"Welcome to fldesktop")

        self.comm = comm.GlobalComm(self)

        self.tasksched = tasksched.TaskSched(self.comm)

        self.init = init.Init(self.comm)

        self.socket = socket.SocketServer(self.comm)

        self.lifecycle = lifecycle.Lifecycle(self)

        self.lifecycle.mainloop()


if __name__ == "__main__":
    Main()
