import logging
import uuid
import time
import threading


class GlobalComm:
    def __init__(self, core):
        self.core = core

        self.services = {}
        self.local_services = {}
        self.subsystem_mapping = {}

        self.replies = {}
        self._cond = threading.Condition()
        self._service_events = {}

    def register(self, subsystem: str, name: str, methods: list):
        self.services[name] = methods
        self.subsystem_mapping[name] = subsystem
        logging.debug(f"Registered service {name}")

        ev = self._service_events.get(name)
        if ev:
            ev.set()

    def local_register(self, name: str, methods: dict):
        self.local_services[name] = methods
        logging.debug(f"Registered local service {name}")

    def request(self, service: str, method: str, *args, **kwargs):
        if service in self.local_services:
            if method in self.local_services[service]:
                return self.local_services[service][method](*args, **kwargs)

        if service in self.services:
            if method in self.services[service]:
                subsystem = self.subsystem_mapping[service]
                return self.send(
                    "request", {
                        "service": service,
                        "method": method,
                        "args": args,
                        "kwargs": kwargs,
                    }, subsystem, True,
                )
        return None

    def emit(self, signal: str, *args, **kwargs):
        for ssn in self.core.init.subsystems.keys():
            self.send(
                "emit", {"signal": signal, "args": args, "kwargs": kwargs},
                ssn,
            )

    def wait_for_sv(self, service: str, timeout: float = 5):
        ev = self._service_events.setdefault(service, threading.Event())
        st = time.time()
        while not ev.is_set():
            if time.time() - st > timeout:
                self.request(
                    "lifecycle", "panic",
                    f"Timeout reached while waiting for service {service}",
                )
                return
            self.collect()
            ev.wait(timeout=0.01)

    def collect(self):
        while True:
            msg = self.core.socket.collect()
            if not msg:
                break
            self.process_message(msg, msg["subsystem"])
        self.request("tasksched", "schedule", self.collect)

    def process_message(self, msg: dict, subsystem: str):
        #logging.debug(f"{subsystem}: {msg}")

        for i in ("type", "args", "id"):
            if i not in msg:
                return

        match msg["type"]:
            case "register":
                self.register(
                    subsystem,
                    msg["args"]["service"], msg["args"]["methods"],
                )

            case "request":
                threading.Thread(
                    target=self._handle_remote_request,
                    args=(msg, subsystem),
                    daemon=True,
                ).start()

            case "emit":
                logging.debug(f"EMIT {msg}")
                self.emit(
                    msg["args"]["signal"],
                    *msg["args"]["args"], **msg["args"]["kwargs"],
                )

            case "reply":
                with self._cond:
                    self.replies[msg["id"]] = msg["args"]
                    self._cond.notify_all()

            case "log":
                logging.log(
                    msg["args"]["level"],
                    f"{subsystem}: {msg['args']['text']}",
                )

    def _handle_remote_request(self, msg: dict, subsystem: str):
        try:
            r = self.request(
                msg["args"]["service"], msg["args"]["method"],
                *msg["args"]["args"], **msg["args"]["kwargs"],
            )
        except Exception:
            logging.exception(f"request handler failed: {msg!r}")
            r = None

        if isinstance(r, dict):
            r = r.get("reply")
        self.send("reply", {"reply": r}, subsystem, False, msg["id"])

    def send(self, type: str, args: dict, ss: str,
             blocking: bool = False, reqid: str = ""):
        if type == "emit":
            logging.debug(f"Sending message {type} {args} to {ss}")

        if not reqid:
            reqid = str(uuid.uuid4())
        req = {"type": type, "args": args, "id": reqid}

        if ss in self.core.init.subsystems:
            self.request("socketserver", "send", ss, req)

        if blocking:
            st = time.time()
            while True:
                with self._cond:
                    if reqid in self.replies:
                        return self.replies.pop(reqid)
                    remaining = 5 - (time.time() - st)
                    if remaining <= 0:
                        return None
                    self._cond.wait(timeout=min(remaining, 0.01))
                self.collect()
        return None
