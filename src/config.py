#!/usr/bin/env python3
"""
Interactive wizard to create/update config.yaml for LiveRota.
Run:  python -m src.config
"""
from pathlib import Path
import os
import sys
import yaml

DEFAULT_PORT = 8085
DEFAULT_DATE_COLUMN = "date"
DEFAULT_SERVE_ROOT = Path.home() / "LiveRota" / "public"
DEFAULT_ICS_SUBDIR = "foo"
DEFAULT_CONFIG = Path.home() / "LiveRota" / "config.yaml"


def _ask(prompt: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    val = input(f"{prompt}{suffix}: ").strip()
    return val or default


def _ask_list(prompt: str, default_list=None):
    default_list = default_list or []
    default = ",".join(default_list)
    raw = _ask(prompt + " (comma-separated)", default)
    return [x.strip() for x in raw.split(",") if x.strip()]


def _expand_abs(path: str) -> str:
    return str(Path(os.path.expanduser(path)).resolve())


DEFAULT_CONFIG_PATH = DEFAULT_CONFIG


def _expand(p: str) -> str:
    return str(Path(p).expanduser().resolve())


def read_config(cfg_path: Path) -> dict:
    with open(cfg_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    serve_root_dir = raw.get("serve_root_dir")
    ics_subdir = raw.get("ics_subdir")
    legacy_ics_dir = raw.get("ics_dir")

    if not serve_root_dir or not ics_subdir:
        if legacy_ics_dir:
            p = Path(_expand(legacy_ics_dir))
            serve_root_dir = str(p.parent)
            ics_subdir = p.name
        else:
            serve_root_dir = str(Path.home() / "LiveRota" / "public")
            ics_subdir = "foo"

    return {
        "path_to_rota": _expand(raw.get("path_to_rota", "")),
        "serve_root_dir": _expand(serve_root_dir),
        "ics_subdir": str(ics_subdir),
        "people": list(raw.get("people", [])),
        "date_column": raw.get("date_column", "date"),
        "port": int(raw.get("port", DEFAULT_PORT)),
    }


def load_existing(config_path: Path):
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return {}
    return {}


def main():
    cfg_path = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DEFAULT_CONFIG
    cfg = load_existing(cfg_path)

    # Ensure logs dir exists for server logs
    logs_dir = Path.home() / "LiveRota" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nLiveRota config wizard → {cfg_path}\n(press Enter to accept defaults)\n")

    path_to_rota = _expand_abs(_ask("Path to rota file", cfg.get("path_to_rota", "")))
    serve_root_dir = _expand_abs(_ask("Directory to SERVE over HTTP", cfg.get("serve_root_dir", str(DEFAULT_SERVE_ROOT))))
    ics_subdir = _ask("Subdirectory (inside served dir) for .ics files", cfg.get("ics_subdir", DEFAULT_ICS_SUBDIR)).strip() or DEFAULT_ICS_SUBDIR
    people = _ask_list("People to generate calendars for", cfg.get("people", []))
    date_column = _ask("Name of the date column", cfg.get("date_column", DEFAULT_DATE_COLUMN))
    port_raw = _ask("Port to serve HTTP", str(cfg.get("port", DEFAULT_PORT)))
    try:
        port = int(port_raw)
    except ValueError:
        port = DEFAULT_PORT

    # Ensure directories exist
    Path(serve_root_dir).mkdir(parents=True, exist_ok=True)
    Path(serve_root_dir, ics_subdir).mkdir(parents=True, exist_ok=True)

    out = {
        "path_to_rota": path_to_rota,
        "serve_root_dir": serve_root_dir,  # e.g. /home/pi/LiveRota/public
        "ics_subdir": ics_subdir,          # e.g. foo
        "people": people,                   # YAML list
        "date_column": date_column,         # e.g. "date"
        "port": port,
        # tip: we no longer need to store ics_dir directly
    }
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    with open(cfg_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(out, f, sort_keys=False)

    print("\nSaved config:")
    print(yaml.safe_dump(out, sort_keys=False))


if __name__ == "__main__":
    main()
