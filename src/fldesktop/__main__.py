# fldesktop - Fluorite main system service and graphical environment
# Copyright (C) 2025-2026 Iamha111
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.


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
