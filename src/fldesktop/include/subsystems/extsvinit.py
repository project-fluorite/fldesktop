import os
import sys
sys.path.insert(0, os.getcwd())


from fldesktop.include.subsystem import Subsystem

import subprocess
import threading
import logging
import time
import signal


SERVICES = {
    "udev": {
        "exec": (
            "mkdir -p /run/udev && "
            "/usr/lib/systemd/systemd-udevd --daemon && "
            "while [ ! -S /run/udev/control ]; do sleep 0.1; done && "
            "udevadm trigger --type=subsystems --action=add && "
            "udevadm trigger --type=devices --action=add && "
            "udevadm settle && "
            "udevadm control --exit && "
            "sleep 0.5 && "
            "exec /usr/lib/systemd/systemd-udevd -N late"
        ),
        "wait": "while [ ! -S /run/udev/control ]; do sleep 0.05; done",
        "user": 0
    },
    "dbus": {
        "exec": "mkdir -p /var/run/dbus /var/lib/dbus && dbus-uuidgen --ensure 2>/dev/null; exec dbus-daemon --system --nofork",
        "wait": "while [ ! -S /run/dbus/system_bus_socket ]; do sleep 0.05; done",
        "user": 0
    },
    "weston": {
        "exec": (
            "mkdir -p /tmp/.X11-unix && "
            "chmod 1777 /tmp/.X11-unix && "
            "export XDG_RUNTIME_DIR=/run/user/0 && "
            "export XDG_SEAT=seat0 && "
            "export SEATD_VTBOUND=0 && "
            "export LIBSEAT_BACKEND=builtin && "
            "exec weston --backend=drm --socket=wayland-0 --xwayland"
        ),
        "wait": "while [ ! -S /run/user/0/wayland-0 ]; do sleep 0.05; done",
        "user": 0,
    },
    "bluetooth": {
        "exec": "exec /usr/sbin/bluetoothd --nodetach",
        "wait": "while [ ! -S /run/dbus/system_bus_socket ]; do sleep 0.05; done",
        "user": 0
    },
    "networkmanager": {
        "exec": "exec /usr/sbin/NetworkManager --no-daemon",
        "wait": "while [ ! -S /run/dbus/system_bus_socket ]; do sleep 0.05; done",
        "user": 0
    },
    "cups": {
        "exec": "exec /usr/sbin/cupsd -f",
        "wait": "while [ ! -S /run/cups/cups.sock ]; do sleep 0.05; done",
        "user": 0
    },
    "pipewire": {
        "exec": (
            "export XDG_RUNTIME_DIR=/run/user/0 && "
            "exec pipewire"
        ),
        "wait": "while [ ! -S /run/user/0/pipewire-0 ]; do sleep 0.05; done",
        "user": 0
    },
    "wireplumber": {
        "exec": (
            "export XDG_RUNTIME_DIR=/run/user/0 && "
            "exec /usr/bin/wireplumber"
        ),
        "wait": "while [ ! -S /run/user/0/pipewire-0 ]; do sleep 0.05; done",
        "user": 0
    }
}


class ServiceWrapper:
    def __init__(self, comm, service):
        self.comm = comm
        self.service = service

        self.comm.request("extsvinit", "start_service", self.service)

    def sv_cleanup(self):

        self.comm.request("extsvinit", "stop_service", self.service)


class Service:
    def __init__(self, name: str, exec: str = "", wait: str = "",
                 user: int = 0):

        self.name = name
        self.exec = exec
        self.wait = wait
        self.user = user

        self.proc = None
        self.is_ready = False

        self.thread = threading.Thread(target=self.supervise)
        self.shutdown = threading.Event()

    @property
    def is_active(self) -> bool:
        return (
            self.thread.is_alive()
            and self.is_ready
            and self.proc is not None
            and self.proc.poll() is None
        )

    def _wrap(self, cmd: str) -> str:
        if self.user != 0 and os.getuid() != self.user:
            return (
                f"setpriv --reuid={self.user} --regid={self.user} "
                f"--init-groups --inh-caps=-all -- "
                f"/bin/sh -c {self._quote(cmd)}"
            )
        return cmd

    @staticmethod
    def _quote(s: str) -> str:
        return "'" + s.replace("'", "'\\''") + "'"

    def _log_stream(self, stream, level: int):
        for line in iter(stream.readline, b""):
            text = line.decode(errors="replace").rstrip()
            if text:
                logging.log(level, f"[{self.name}] {text}")

    def supervise(self):
        while not self.shutdown.is_set():
            try:
                self.proc = subprocess.Popen(
                    self._wrap(self.exec),
                    shell=True,
                    start_new_session=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                )
            except Exception:
                logging.exception(f"[{self.name}] failed to spawn")
                if self.shutdown.wait(1):
                    break
                continue

            self.is_ready = False

            log_thread = threading.Thread(
                target=self._log_stream,
                args=(self.proc.stdout, logging.WARNING),
                daemon=True,
            )
            log_thread.start()

            while not self.shutdown.is_set():
                if self.proc.poll() is not None:
                    break
                time.sleep(0.1)

            self.is_ready = False

            if self.shutdown.is_set():
                break

            logging.warning(
                f"[{self.name}] exited with code {self.proc.returncode}, restarting"
            )
            if self.shutdown.wait(1):
                break

        if self.proc is not None and self.proc.poll() is None:
            try:
                os.killpg(self.proc.pid, signal.SIGTERM)
            except (ProcessLookupError, PermissionError):
                pass
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(self.proc.pid, signal.SIGKILL)
                except (ProcessLookupError, PermissionError):
                    pass
                self.proc.wait()
        self.is_ready = False

    def wait_ready(self, timeout: float = 10.0) -> bool:
        if not self.wait:
            self.is_ready = True
            return True

        deadline = time.monotonic() + timeout

        while not self.shutdown.is_set():
            if time.monotonic() >= deadline:
                break

            if self.proc is None or self.proc.poll() is not None:
                self.shutdown.wait(0.1)
                continue

            try:
                r = subprocess.run(
                    self._wrap(self.wait),
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    timeout=max(0.1, deadline - time.monotonic()),
                )
            except subprocess.TimeoutExpired:
                break
            except Exception:
                logging.exception(f"[{self.name}] wait spawn failed")
                self.shutdown.wait(1)
                continue

            if self.proc is None or self.proc.poll() is not None:
                continue

            if r.returncode != 0:
                out = r.stdout.decode(errors="replace").rstrip()
                logging.warning(
                    f"[{self.name}] wait failed (rc={r.returncode} {out!r})"
                )
                self.shutdown.wait(0.1)
                continue

            if self.shutdown.wait(1):
                break
            if self.proc is not None and self.proc.poll() is None:
                self.is_ready = True
                return True

        if not self.shutdown.is_set():
            logging.warning(
                f"[{self.name}] timed out after {timeout:g}s"
            )
        return False

    def start(self, timeout: float = 10.0) -> bool:
        if self.thread.is_alive():
            if self.is_ready:
                return True
            return self.wait_ready(timeout)

        logging.debug(f"Starting external service {self.name}...")
        if self.thread.ident is not None:
            self.thread = threading.Thread(target=self.supervise)
        self.shutdown.clear()
        self.is_ready = False
        self.thread.start()
        return self.wait_ready(timeout)

    def stop(self):
        if not self.thread.is_alive() and (
            self.proc is None or self.proc.poll() is not None
        ):
            return

        logging.debug(f"Stopping external service {self.name}...")

        self.shutdown.set()

        proc = self.proc
        if proc is not None and proc.poll() is None:
            try:
                os.killpg(proc.pid, signal.SIGTERM)
            except (ProcessLookupError, PermissionError):
                pass

        self.thread.join(timeout=5)
        if proc is not None and proc.poll() is None:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                pass
        self.thread.join(timeout=5)
        if self.thread.is_alive() or (proc is not None and proc.poll() is None):
            raise TimeoutError(f"[{self.name}] service did not stop")


class ExtSvInit(Subsystem):
    def __init__(self):
        super().__init__("extsvinit")

        self.gen_svs()

        self.services = {}
        self.load_services()
        self.comm.register(
            "extsvinit", {
                "start_service": self.start_service,
                "stop_service": self.stop_service,
            }
        )

        self.locked = bool(
            self.comm.request("lifecycle", "is_dev_environment")
        )

    def gen_svs(self):

        svs = {}

        for i in SERVICES:
            svs[i] = lambda comm, s=i: ServiceWrapper(comm, s)

        self.init.set_services(svs)

    def load_services(self):
        for name, cfg in SERVICES.items():
            self.services[name] = Service(name, **cfg)

    def start_service(self, service: str) -> bool:
        if self.locked:
            return False
        svc = self.services.get(service)
        if svc is None:
            raise ValueError(f"Unknown service: {service}")
        return svc.start()

    def stop_service(self, service: str) -> bool:
        if self.locked:
            return False
        svc = self.services.get(service)
        if svc is None:
            raise ValueError(f"Unknown service: {service}")
        svc.stop()
        return True
