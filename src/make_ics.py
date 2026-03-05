#!/usr/bin/env python3
"""
Generate .ics calendar files from an Excel rota.

Events are created from 09:00 to 17:00 on each date, using the cell's
text as the event title (e.g., "0800-1430", "OffRota", etc.).
"""
import argparse
import sys
import uuid
from datetime import datetime
from pathlib import Path

import pandas as pd

# === DEFAULT CONFIGURATION (can be overridden via CLI) ===
DEFAULT_ROTA_FILE_PATH = \
    "/Users/jamescranley/Library/CloudStorage/OneDrive-NHS/SpR Information/SpR Rota/Termly/Sep2025_rota.xlsx"
DEFAULT_DATE_COLUMN = "date"
DEFAULT_OUTPUT_DIR = Path("ics_files")  # Subdirectory to store ICS files


def parse_args(argv: list[str]):
    parser = argparse.ArgumentParser(
        description="Generate .ics files for one or more rota columns (people)."
    )
    parser.add_argument(
        "names",
        nargs="*",
        help="Positional column names (legacy usage). Ignored if --people is used.",
    )
    parser.add_argument(
        "-r",
        "--rota",
        default=DEFAULT_ROTA_FILE_PATH,
        help="Path to the rota .xlsx file.",
    )
    parser.add_argument(
        "-p",
        "--people",
        nargs="+",
        help="One or more column names to export. Overrides positional names.",
    )
    parser.add_argument(
        "-d",
        "--date-column",
        default=DEFAULT_DATE_COLUMN,
        help="Name of the date column in the Excel sheet.",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Directory to write .ics files to.",
    )
    parser.add_argument(
        "-D",
        "--developing",
        action="store_true",
        help="Limit output to first 5 shifts for quick testing.",
    )

    args = parser.parse_args(argv)
    return args


def _normalize_dates(df: pd.DataFrame, date_column: str) -> pd.DataFrame:
    """
    Make the date column robust:
      - If already datetime, keep it.
      - If numeric, treat as Excel serial days (origin 1899-12-30).
      - Else, parse with pandas.
    """
    s = df[date_column]
    if pd.api.types.is_datetime64_any_dtype(s):
        return df
    if pd.api.types.is_numeric_dtype(s):
        df[date_column] = pd.to_datetime(s, unit="D", origin="1899-12-30", errors="coerce")
    else:
        df[date_column] = pd.to_datetime(s, errors="coerce")
    return df


def _serialize_ics(events: list) -> str:
    FMT = "%Y%m%dT%H%M%S"
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//LiveRota//LiveRota//EN",
        "CALSCALE:GREGORIAN",
    ]
    for dtstart, dtend, title in events:
        lines += [
            "BEGIN:VEVENT",
            f"UID:{uuid.uuid4()}@liverota",
            f"DTSTART:{dtstart.strftime(FMT)}",
            f"DTEND:{dtend.strftime(FMT)}",
            f"SUMMARY:{title}",
            "END:VEVENT",
        ]
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"


def main(argv: list[str]) -> int:
    args = parse_args(argv)

    rota_path = Path(args.rota).expanduser()
    date_column = args.date_column
    output_dir = Path(args.output_dir)
    developing = bool(args.developing)

    # Determine which names to process
    names: list[str] = args.people if args.people else args.names
    if not names:
        print("Usage: python make_ics.py --rota <path.xlsx> --people <Name1> [Name2 ...]")
        return 1

    if not rota_path.exists():
        print(f"❌ Rota file not found: {rota_path}")
        return 1

    try:
        df = pd.read_excel(rota_path, engine="openpyxl")
    except Exception as e:
        print(f"❌ Failed to read Excel file '{rota_path}': {e}")
        return 1

    if date_column not in df.columns:
        print(f"❌ Date column '{date_column}' not found in file. Available columns: {list(df.columns)}")
        return 1

    # Robust date handling (prevents 1970-01-01 issues)
    df = _normalize_dates(df, date_column)

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Process each requested name
    for column in names:
        if column not in df.columns:
            print(f"⚠️ Column '{column}' not found in rota file. Skipping.")
            continue

        # Keep rows where date is valid and the cell has some text (any text is a valid "title")
        sub_df = df[[date_column, column]].copy()
        sub_df = sub_df.dropna(subset=[date_column])                      # date must exist
        sub_df[column] = sub_df[column].astype(str).str.strip()           # normalize to string
        sub_df = sub_df[sub_df[column] != ""]                             # require non-empty text

        if developing:
            sub_df = sub_df.head(5)

        events = []
        for _, row in sub_df.iterrows():
            date = row[date_column]
            if pd.isna(date):
                continue
            if hasattr(date, "date"):
                date = date.date()  # pandas Timestamp -> date
            title = row[column]
            dtstart = datetime.combine(date, datetime.strptime("09:00", "%H:%M").time())
            dtend = datetime.combine(date, datetime.strptime("17:00", "%H:%M").time())
            events.append((dtstart, dtend, title))

        ics_filename = output_dir / f"{column}.ics"
        ics_filename.write_text(_serialize_ics(events))
        print(f"✅ {ics_filename} written.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
