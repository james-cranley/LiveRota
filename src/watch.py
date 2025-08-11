#!/usr/bin/env python3
from __future__ import annotations
import logging
import threading
from pathlib import Path
from typing import Callable, Optional

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

log = logging.getLogger("LiveRota.watch")
DEBOUNCE_SECONDS = 1.0  # avoid rapid double builds on save


class _DebouncedHandler(FileSystemEventHandler):
    def __init__(self, target_file: Path, on_change: Callable[[], None]):
        super().__init__()
        self.target_file = target_file
        self.on_change = on_change
        self._timer: Optional[threading.Timer] = None
        self._lock = threading.Lock()

    def _schedule(self):
        with self._lock:
            if self._timer:
                self._timer.cancel()
            self._timer = threading.Timer(DEBOUNCE_SECONDS, self._run)
            self._timer.daemon = True
            self._timer.start()

    def _run(self):
        try:
            self.on_change()
        except Exception as e:
            log.exception("on_change callback raised: %s", e)

    def _matches(self, path: str) -> bool:
        return Path(path) == self.target_file

    def on_modified(self, event):
        if not event.is_directory and self._matches(event.src_path):
            log.info("Rota modified: %s", event.src_path)
            self._schedule()

    def on_created(self, event):
        if not event.is_directory and self._matches(event.src_path):
            log.info("Rota created: %s", event.src_path)
            self._schedule()

    def on_moved(self, event):
        dest = getattr(event, "dest_path", None)
        if dest and self._matches(dest):
            log.info("Rota moved/replaced: %s", dest)
            self._schedule()


class RotaWatcher:
    """
    Watches a single rota file and invokes `on_change()` (debounced) when it changes.
    """
    def __init__(self, rota_file: Path, on_change: Callable[[], None]):
        self.rota_file = rota_file
        self.on_change = on_change
        self._observer: Optional[Observer] = None

    def start(self):
        handler = _DebouncedHandler(self.rota_file, self.on_change)
        self._observer = Observer()
        watch_dir = self.rota_file.parent if self.rota_file.parent.exists() else Path(".").resolve()
        self._observer.schedule(handler, str(watch_dir), recursive=False)
        self._observer.start()
        log.info("Watching %s for changes", self.rota_file)

    def stop(self):
        if self._observer:
            self._observer.stop()
            self._observer.join()
            self._observer = None
