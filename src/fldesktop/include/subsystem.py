import threading
import queue
import time
import uuid
import msgpack
import struct
import os
import sys
import socket
import logging
import traceback


_CLOSED = object()


class Service:
    def __init__(self, name: str, obj, comm) -> None:
        self.name = name
        self.comm = comm
        self.obj = obj
        self.started = False

    def start(self) -> None:
        if self.started:
            return

        logging.info(f"Starting internal service {self.name}")

        try:
            self.obj = self.obj(self.comm)
        except ArithmeticError as e:
            tb = traceback.extract_tb(e.__traceback__)[-1]
            file = tb.filename.split("/")[-1]
            logging.critical(
                f"Service {self.name} failed: {file}, line {tb.lineno}: {e}"
            )
        else:
            self.started = True

    def cleanup(self) -> None:
        if hasattr(self.obj, "srv_cleanup") and self.started:
            logging.info(f"Performing cleanup for service {self.name}")
            try:
                self.obj.srv_cleanup()
            except Exception as e:
                logging.info(f"Cleanup for {self.name} failed: {e}")


class Init:
    def __init__(self, comm):
        self.comm = comm
        self.services = {}

    def set_services(self, services: dict):
        for n, o in services.items():
            service = Service(n, o, self.comm)
            self.services[n] = service

    def start_service(self, service: str):
        if service in self.services:
            self.services[service].start()


class Comm:
    def __init__(self, ss):
        self._ss = ss
        self.services = {}
        self.signal_subs = []

    def register(self, service: str, methods: dict):
        self.services[service] = methods
        self._ss.request("register", {
            "service": service, "methods": list(methods.keys())
        }, False)

    def request(self, service: str, method: str, *args, **kwargs):
        if service in self.services:
            if method in self.services[service]:
                return self.services[service][method](*args, **kwargs)
        reply = self._ss.request("request", {
            "service": service, "method": method, "args": args, "kwargs": kwargs
        })
        if reply is None:
            return None
        return reply.get("reply")

    def subscribe(self, signal: str, action):
        self.signal_subs.append({"signal": signal, "action": action})

    def unsubscribe(self, action):
        for i in self.signal_subs:
            if i["action"] == action:
                self.signal_subs.remove(i)

    def emit(self, signal: str, *args, **kwargs):
        self._ss.request(
            "emit", {"signal": signal, "args": args, "kwargs": kwargs},
            False
        )

    def emit_(self, signal: str, *args, **kwargs):
        for i in self.signal_subs:
            if i["signal"] == signal:
                i["action"](*args, **kwargs)


class SSIO:
    def __init__(self, path: str | None = None):
        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._receive_buffer = bytearray()
        self._request_lock = threading.Lock()
        self._state_lock = threading.Lock()
        self._events = queue.Queue()
        self._pending_reply = None
        self._pending_id = None
        self._closed = False

        if path is None:
            path = os.path.join(os.environ["XDG_RUNTIME_DIR"], "fdcomm")

        self._connect(path)

        self._reader = threading.Thread(target=self._read_loop, daemon=True)
        self._reader.start()

    def _connect(self, path: str):
        try:
            self.socket.connect(path)
        except FileNotFoundError:
            raise RuntimeError("socket is unaccesible")

    @property
    def closed(self) -> bool:
        return self._closed

    def send(self, data: dict, blocking: bool = True, timeout: float | None = None):
        data_bytes = msgpack.packb(data)
        prefix = struct.pack(">I", len(data_bytes))

        reply_queue = queue.Queue(maxsize=1) if blocking else None

        with self._request_lock:
            if blocking:
                with self._state_lock:
                    if self._closed:
                        return None
                    self._pending_reply = reply_queue
                    self._pending_id = data.get("id")

            try:
                self.socket.sendall(prefix + data_bytes)
            except OSError:
                if blocking:
                    with self._state_lock:
                        if self._pending_reply is reply_queue:
                            self._pending_reply = None
                            self._pending_id = None
                raise

            if not blocking:
                return None

            try:
                return reply_queue.get(timeout=timeout)
            except queue.Empty:
                with self._state_lock:
                    if self._pending_reply is reply_queue:
                        self._pending_reply = None
                        self._pending_id = None
                return None

    def receive(self, blocking: bool = True) -> dict | None:
        try:
            event = self._events.get(block=blocking)
        except queue.Empty:
            with self._state_lock:
                return None if self._closed else {}

        if event is _CLOSED:
            return None
        return event

    def _read_message(self):
        while len(self._receive_buffer) < 4:
            chunk = self.socket.recv(65536)
            if not chunk:
                return None
            self._receive_buffer.extend(chunk)

        data_length = struct.unpack(">I", self._receive_buffer[:4])[0]
        if data_length > 64 * 1024 * 1024:
            raise ValueError(f"message too large: {data_length}")
        message_length = 4 + data_length

        while len(self._receive_buffer) < message_length:
            chunk = self.socket.recv(65536)
            if not chunk:
                return None
            self._receive_buffer.extend(chunk)

        data = bytes(self._receive_buffer[4:message_length])
        del self._receive_buffer[:message_length]
        return msgpack.unpackb(data)

    def _read_loop(self):
        try:
            while True:
                message = self._read_message()
                if message is None:
                    break

                if isinstance(message, dict) and message.get("type") == "reply":
                    with self._state_lock:
                        reply_queue = self._pending_reply
                        reqid = self._pending_id
                        if reply_queue is not None and message.get("id") == reqid:
                            self._pending_reply = None
                            self._pending_id = None
                        else:
                            reply_queue = None
                    if reply_queue is not None:
                        reply_queue.put(message.get("args") or {})
                    continue

                if isinstance(message, dict) and "type" in message:
                    self._events.put(message)
                    continue

                with self._state_lock:
                    reply_queue = self._pending_reply
                    self._pending_reply = None
                    self._pending_id = None
                if reply_queue is not None:
                    reply_queue.put(message)
        except (OSError, ValueError):
            pass
        finally:
            with self._state_lock:
                self._closed = True
                reply_queue = self._pending_reply
                self._pending_reply = None
                self._pending_id = None
            if reply_queue is not None:
                reply_queue.put(None)
            self._events.put(_CLOSED)


class _LogHandler(logging.Handler):
    def __init__(self, request_cb):
        super().__init__()
        self._request = request_cb
        self.setFormatter(logging.Formatter(
            f"%(filename)s: %(message)s"
        ))

    def emit(self, record):
        try:
            text = self.format(record)
        except Exception:
            self.handleError(record)
            return
        try:
            self._request("log", {"text": text, "level": record.levelno}, False)
        except Exception:
            self.handleError(record)


class Subsystem:
    def __init__(self, name: str, socket_path: str | None = None):
        self.name = name
        self.ssio = SSIO(socket_path)
        self.comm = Comm(self)
        self.init = Init(self.comm)

        self._alive = True

        self.request("init", {"name": self.name}, False)

        self.comm.register(
            f"{self.name}-core", {"start_service": self.init.start_service}
        )

        self._setup_logging()

        logging.info(f"Greetings from {self.name}!")

    def _setup_logging(self):
        def send_log(type_, args, blocking):
            self.request(type_, args, blocking)

        root = logging.getLogger()
        for h in list(root.handlers):
            root.removeHandler(h)
        handler = _LogHandler(send_log)
        root.addHandler(handler)
        root.setLevel(logging.DEBUG)

        def excepthook(exc_type, exc_value, exc_tb):
            text = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
            send_log("log", {
                "text": text.rstrip("\n"),
                "level": logging.ERROR,
            }, False)

        sys.excepthook = excepthook

        def thread_excepthook(args):
            text = "".join(traceback.format_exception(
                args.exc_type, args.exc_value, args.exc_traceback
            ))
            send_log("log", {
                "text": f"[thread {args.thread.name}] {text.rstrip(chr(10))}",
                "level": logging.ERROR,
            }, False)

        threading.excepthook = thread_excepthook

    def tick(self):
        r = self.ssio.receive(blocking=False)
        if r is None:
            if self.ssio.closed:
                self._alive = False
            return
        if not r:
            return
        self.process_msg(r)

    def mainloop(self):
        while self._alive:
            self.tick()
            time.sleep(0.01)

    def process_msg(self, msg: dict):
        if not isinstance(msg, dict):
            return

        for i in ("type", "args", "id"):
            if not i in msg:
                return

        match msg["type"]:
            case "request":
                r = self.comm.request(
                    msg["args"]["service"], msg["args"]["method"],
                    *msg["args"]["args"], **msg["args"]["kwargs"]
                )
                self.request("reply", {"reply": r}, False, msg["id"])

            case "emit":
                self.comm.emit_(
                    msg["args"]["signal"],
                    *msg["args"]["args"], **msg["args"]["kwargs"]
                )

            case "reply":
                pass

    def request(self, type: str, args: dict,
                blocking: bool = True, reqid: str = ""):
        if not reqid:
            reqid = str(uuid.uuid4())

        req = {"type": type, "args": args, "id": reqid}

        if blocking:
            return self.ssio.send(req, blocking=True, timeout=5)
        self.ssio.send(req, blocking=False)
        return None
