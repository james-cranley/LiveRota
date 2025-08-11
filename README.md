# `LiveRota`

LiveRota watches a rota Excel file, regenerates `.ics` calendar files when it changes, and serves them over HTTP from a Raspberry Pi (or any Linux host).

## Features
- Watches your rota file for edits using `watchdog`.
- Runs a custom `make_ics.py` to generate `.ics` files.
- Serves files over HTTP via Python's built-in HTTP server.
- Outputs `.ics` into a subdirectory inside the served folder (e.g., `/foo`).
- Fully configurable via `config.yaml`.

## Installation (Conda Environment)
```bash
# Create and activate a Conda environment called LiveRota
conda create -n LiveRota python=3.11 -y
conda activate LiveRota

# Clone repository
git clone git@github.com:james-cranley/LiveRota.git
cd LiveRota

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

## Autostart on Raspberry Pi (cron)
To run LiveRota on boot, add to crontab:
```bash
crontab -e
```
Then add:
```bash
@reboot bash -c 'sleep 30; source ~/miniforge3/etc/profile.d/conda.sh && conda activate LiveRota && cd ~/LiveRota && nohup python -m src.main -c config.yaml > ~/LiveRota/logs/server.log 2>&1 &'
```
Explanation:
- `sleep 30` gives the network time to come up after boot.
- `source ~/miniforge3/etc/profile.d/conda.sh` initializes Conda in non-interactive shells.
- `conda activate LiveRota` activates your environment.
- `nohup ... &` runs the server in the background and detaches it from the terminal.
- Logs are written to `~/LiveRota/logs/server.log`.

Ensure the logs directory exists:
```bash
mkdir -p ~/LiveRota/logs
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
