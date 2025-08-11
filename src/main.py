#!/usr/bin/env python3
import argparse
import logging
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import List, Tuple

import yaml

from .watch import RotaWatcher
from .serve import start_http_server, stop_http_server

DEFAULT_CONFIG = Path.home() / "LiveRota" / "config.yaml"
DEFAULT_PORT = 8085

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
log = logging.getLogger("LiveRota")


def _expand(p: str) -> str:
    return str(Path(p).expanduser().resolve())


def read_config(cfg_path: Path) -> dict:
    with open(cfg_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    # Back-compat: if old ics_dir exists, derive serve_root_dir + ics_subdir from it
    serve_root_dir = raw.get("serve_root_dir")
    ics_subdir = raw.get("ics_subdir")
    legacy_ics_dir = raw.get("ics_dir")

    if not serve_root_dir or not ics_subdir:
        if legacy_ics_dir:
            p = Path(_expand(legacy_ics_dir))
            serve_root_dir = str(p.parent)
            ics_subdir = p.name
            log.info("Derived serve_root_dir=%s and ics_subdir=%s from legacy ics_dir=%s",
                     serve_root_dir, ics_subdir, legacy_ics_dir)
        else:
            # sensible defaults
            serve_root_dir = str(Path.home() / "LiveRota" / "public")
            ics_subdir = "foo"

    cfg = {
        "path_to_rota": _expand(raw.get("path_to_rota", "")),
        "serve_root_dir": _expand(serve_root_dir),
        "ics_subdir": str(ics_subdir),
        "people": list(raw.get("people", [])),
        "date_column": raw.get("date_column", "date"),
        "port": int(raw.get("port", DEFAULT_PORT)),
    }
    return cfg


def _resolve_make_ics() -> Path:
    here = Path(__file__).resolve().parent
    candidate = here / "make_ics.py"
    if candidate.exists():
        return candidate
    return Path("make_ics.py")


def run_make_ics(rota_path: Path, out_dir: Path, people: List[str], date_column: str) -> int:
    """
    Pass config values directly to make_ics.py:
      --rota <path> --output-dir <dir> --date-column <name> --people <...>
    """
    make_ics = _resolve_make_ics()
    cmd = [
        sys.executable, str(make_ics),
        "--rota", str(rota_path),
        "--output-dir", str(out_dir),
        "--date-column", str(date_column),
    ]
    if people:
        cmd += ["--people", *people]

    log.info("Running: %s", " ".join(cmd))
    try:
        res = subprocess.run(cmd, check=True, capture_output=True, text=True)
        if res.stdout:
            log.info("make_ics.py stdout:\n%s", res.stdout.strip())
        if res.stderr:
            log.debug("make_ics.py stderr:\n%s", res.stderr.strip())
        return 0
    except subprocess.CalledProcessError as e:
        log.error("make_ics.py failed (exit %s)\nstdout:\n%s\nstderr:\n%s",
                  e.returncode, e.stdout, e.stderr)
        return e.returncode


def main():
    parser = argparse.ArgumentParser(description="LiveRota runner (watch + serve)")
    parser.add_argument("-c", "--config", default=str(DEFAULT_CONFIG), help="Path to config.yaml")
    args = parser.parse_args()

    cfg_path = Path(args.config).expanduser().resolve()
    if not cfg_path.exists():
        log.error("Config not found: %s\nRun the wizard: python -m src.config %s", cfg_path, cfg_path)
        sys.exit(2)

    cfg = read_config(cfg_path)

    # Ensure logs dir exists for server logs
    logs_dir = Path.home() / "LiveRota" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

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
