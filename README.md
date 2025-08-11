# LiveRota

LiveRota watches a rota Excel file, regenerates `.ics` calendar files when it changes, and serves them over HTTP from a Raspberry Pi (or any Linux host).

## Features
- Watches your rota file for edits using `watchdog`.
- Runs a custom `make_ics.py` to generate `.ics` files.
- Serves files over HTTP via Python's built-in HTTP server.
- Outputs `.ics` into a subdirectory inside the served folder (e.g., `/foo`).
- Fully configurable via `config.yaml`.

## Installation
```bash
# Clone repository
git clone https://github.com/<your-username>/LiveRota.git
cd LiveRota

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Configuration
Run the interactive wizard:
```bash
python -m src.config
```
You will be prompted for:
- Path to rota Excel file
- Directory to serve over HTTP (`serve_root_dir`)
- Subdirectory inside served dir for `.ics` files (`ics_subdir`)
- List of people (comma-separated)
- Date column name in the Excel sheet
- Port to serve HTTP

This creates/updates `config.yaml`.

## Running LiveRota
```bash
python -m src.main -c config.yaml
```

The server will be available at:
```
http://<hostname>:<port>/
```
ICS files are located under:
```
http://<hostname>:<port>/<ics_subdir>/
```

## Autostart on Raspberry Pi
Add to crontab:
```bash
crontab -e
@reboot /bin/bash -lc 'cd /home/pi/LiveRota && source .venv/bin/activate && python -m src.main -c config.yaml >> live-rota.log 2>&1'
```

## Requirements
- Python 3.9+
- `watchdog`
- `PyYAML`
- `pandas`
- `openpyxl`
- `ics`

## License
MIT License
