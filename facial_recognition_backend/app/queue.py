from collections import deque
from threading import Thread, Event, Lock
from typing import Callable, Any
import logging


class TaskQueue:
    def __init__(self):
        self._queue = deque()
        self._lock = Lock()
        self._stop_event = Event()
        self._worker = Thread(target=self._run, daemon=True)
        self._started = False

    def start(self):
        if self._started:
            return
        self._started = True
        self._worker.start()

    def stop(self):
        self._stop_event.set()

    def enqueue(self, fn: Callable[..., Any], *args, **kwargs):
        with self._lock:
            self._queue.append((fn, args, kwargs))

    def _run(self):
        while not self._stop_event.is_set():
            task = None
            with self._lock:
                if self._queue:
                    task = self._queue.popleft()
            if not task:
                self._stop_event.wait(0.2)
                continue
            fn, args, kwargs = task
            try:
                fn(*args, **kwargs)
            except Exception as exc:
                logging.error(f"Background task failed: {exc}")


task_queue = TaskQueue()
