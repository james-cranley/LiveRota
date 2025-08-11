# `LiveRota`

LiveRota watches a rota Excel file, regenerates `.ics` calendar files when it changes, and serves them over HTTP from a Raspberry Pi (or any Linux host).

## Rota input
- .xlsx format
- People are column names, rows are dates, values are shift names
- Dates in ISO8601 format in a date column (the name of which is configurable, default=`date`)
- People shoud be single string e.g. 'JamesCranley' not 'James Cranley'

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

## Serving via the web
Use cloudflare or similar to forward <port> as a subdomain of an existing domain to make it web-accessible.

This is the sort of format:
https://liverota.jamescranley.co.uk/<ics_subdir>/<person>.ics

For a concrete example:
https://liverota.jamescranley.co.uk/registrars/JamesCranley.ics

 URL is **CASE SENSITIVE**

## How to Subscribe via Calendar client

Once LiveRota is running and serving your `.ics` files, you can subscribe to them in your preferred calendar app.
This means that changes in the rota will be reflected in the subscribed calendar feed.
You do need to ensure the calendar client 'refreshes' autoamtically, updates will not be 'pushed' to the client. Daily is fine since the rota shouldn't change often.

### Apple Calendar (macOS / iOS)
1. Open Calendar.
2. Go to **File → New Calendar Subscription...**
3. Enter the URL to the `.ics` file, for example:
   ```
   https://liverota.jamescranley.co.uk/registrars/JamesCranley.ics # NB again, it is CASE SENSITIVE
   ```
4. Click **Subscribe** and adjust settings (refresh interval, name, color, etc.).

### Google Calendar (Web)
1. Open Google Calendar in your browser.
2. On the left, click the **+** next to *Other calendars* and select **From URL**.
3. Paste the `.ics` file URL (as above).
4. Click **Add calendar**.

> **Note:** Google Calendar refreshes subscribed calendars approximately every 24 hours.

### Outlook (Desktop)
1. Open Outlook.
2. Go to **File → Account Settings → Account Settings**.
3. Select the **Internet Calendars** tab and click **New**.
4. Paste the `.ics` file URL.
5. Click **Add**, then configure folder name and description.

### Outlook.com (Web)
1. Open Outlook.com Calendar in your browser.
2. Select **Add calendar** → **Subscribe from web**.
3. Paste the `.ics` file URL.
4. Give it a name and click **Import**.
