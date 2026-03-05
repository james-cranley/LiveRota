#!/usr/bin/env python3
import argparse
import logging
import signal
import sys
import threading
import time
from pathlib import Path
from typing import List

from .config import read_config
from .watch import RotaWatcher
from .serve import start_http_server, stop_http_server
from . import make_ics as _make_ics

DEFAULT_CONFIG = Path.home() / "LiveRota" / "config.yaml"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
log = logging.getLogger("LiveRota")


def run_make_ics(rota_path: Path, out_dir: Path, people: List[str], date_column: str) -> int:
    argv = [
        "--rota", str(rota_path),
        "--output-dir", str(out_dir),
        "--date-column", date_column,
    ]
    if people:
        argv += ["--people", *people]
    log.info("Generating ICS files -> %s", out_dir)
    return _make_ics.main(argv)


def main():
    parser = argparse.ArgumentParser(description="LiveRota runner (watch + serve)")
    parser.add_argument("-c", "--config", default=str(DEFAULT_CONFIG), help="Path to config.yaml")
    args = parser.parse_args()

    cfg_path = Path(args.config).expanduser().resolve()
    if not cfg_path.exists():
        log.error("Config not found: %s\nRun the wizard: python -m src.config %s", cfg_path, cfg_path)
        sys.exit(2)

    cfg = read_config(cfg_path)

    rota = Path(cfg["path_to_rota"])
    serve_root_dir = Path(cfg["serve_root_dir"])
    ics_subdir = cfg["ics_subdir"].strip("/")  # keep filesystem dir clean
    outdir = serve_root_dir / ics_subdir
    people = cfg["people"]
    date_column = cfg["date_column"]
    port = cfg["port"]

    log.info("Serving root: %s | ICS subdir: %s | People: %s | date_column: %s",
             serve_root_dir, ics_subdir, people, date_column)

    # Ensure directories exist
    serve_root_dir.mkdir(parents=True, exist_ok=True)
    outdir.mkdir(parents=True, exist_ok=True)

    if not rota.exists():
        log.warning("Rota file does not exist yet: %s (will watch and build when created)", rota)

    # Initial build -> writes into serve_root_dir/ics_subdir
    run_make_ics(rota, outdir, people, date_column)

    # Start HTTP server that serves the *root* directory
    httpd, http_thread = start_http_server(serve_root_dir, port)

    # Watcher callback: rebuild ICS into the same subdir
    def _on_rota_change():
        run_make_ics(rota, outdir, people, date_column)

    watcher = RotaWatcher(rota, _on_rota_change)
    watcher.start()

    # Graceful shutdown
    shutdown_called = False
    stop_event = threading.Event()

    def _shutdown(signum=None, frame=None):
        nonlocal shutdown_called
        if shutdown_called:
            return
        shutdown_called = True
        log.info("Shutting down...")
        try:
            stop_http_server(httpd)
            if http_thread.is_alive():
                http_thread.join(timeout=3)
        except Exception:
            pass
        try:
            watcher.stop()
        except Exception:
            pass
        stop_event.set()

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    try:
        while not stop_event.is_set():
            time.sleep(0.5)
    except KeyboardInterrupt:
        _shutdown()


if __name__ == "__main__":
    main()
