#!/usr/bin/env python3
"""
Generate .ics files from a rota, once, with no watching or serving.

Usage:
    python -m src.generate -c config.yaml
    python -m src.generate --rota rota.xlsx --people JamesCranley --output-dir ./out
"""
import argparse
import logging
import sys
from pathlib import Path

from .config import read_config, DEFAULT_CONFIG_PATH
from . import make_ics as _make_ics

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
log = logging.getLogger("LiveRota.generate")


def main():
    parser = argparse.ArgumentParser(
        description="Generate .ics files from a rota (no watching, no serving)."
    )

    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("-c", "--config", metavar="CONFIG_YAML",
                      help="Path to config.yaml (default: %(default)s)",
                      default=None)

    # Allow direct invocation without a config file
    parser.add_argument("-r", "--rota", help="Path to rota .xlsx file")
    parser.add_argument("-p", "--people", nargs="+", help="People (column names) to export")
    parser.add_argument("-d", "--date-column", default="date", help="Date column name")
    parser.add_argument("-o", "--output-dir", default="./ics_files", help="Output directory for .ics files")

    args = parser.parse_args()

    # If --rota is provided, bypass config and call make_ics directly
    if args.rota:
        argv = [
            "--rota", args.rota,
            "--output-dir", args.output_dir,
            "--date-column", args.date_column,
        ]
        if args.people:
            argv += ["--people", *args.people]
        sys.exit(_make_ics.main(argv))

    # Otherwise, load from config.yaml
    cfg_path = Path(args.config).expanduser().resolve() if args.config else DEFAULT_CONFIG_PATH
    if not cfg_path.exists():
        log.error("Config not found: %s\nRun the wizard: python -m src.config %s", cfg_path, cfg_path)
        sys.exit(2)

    cfg = read_config(cfg_path)
    rota = Path(cfg["path_to_rota"])
    out_dir = Path(cfg["serve_root_dir"]) / cfg["ics_subdir"].strip("/")
    out_dir.mkdir(parents=True, exist_ok=True)

    argv = [
        "--rota", str(rota),
        "--output-dir", str(out_dir),
        "--date-column", cfg["date_column"],
    ]
    if cfg["people"]:
        argv += ["--people", *cfg["people"]]

    log.info("Generating ICS files -> %s", out_dir)
    sys.exit(_make_ics.main(argv))


if __name__ == "__main__":
    main()
