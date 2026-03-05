# `LiveRota`

LiveRota converts a rota Excel file into `.ics` calendar files. It can generate them once as static files, or run as a persistent service that watches the rota for changes and serves the files over HTTP.

## Rota input
- File type: `.xlsx`
- Format: People are column names, rows are dates, values are shift names
- Dates in ISO8601 format in a date column (the name of which is configurable, default=`date`)
- People should be a single string e.g. `JamesCranley` not `James Cranley`

## Features
- Generate static `.ics` files from a rota with a single command — no config needed.
- Watches your rota file for edits using `watchdog` and rebuilds automatically.
- Serves files over HTTP via Python's built-in HTTP server.
- Fully configurable via `config.yaml`.

## Installation (Conda Environment)
```bash
# Create and activate a Conda environment
conda create -n LiveRota python=3.11 -y
conda activate LiveRota

# Clone repository
git clone git@github.com:james-cranley/LiveRota.git
cd LiveRota

# Install dependencies
pip install -r requirements.txt
```

## Usage

There are three modes:

### 1. Generate static `.ics` files (no config needed)
```bash
python -m src.generate --rota rota.xlsx --people JamesCranley --output-dir ./out
```
Writes `./out/JamesCranley.ics` and exits. Multiple people can be listed:
```bash
python -m src.generate --rota rota.xlsx --people JamesCranley JaneSmith --output-dir ./out
```

### 2. Generate from `config.yaml`
```bash
python -m src.generate -c config.yaml
```
Generates `.ics` files using settings from config, then exits.

### 3. Full watch + serve mode
```bash
python -m src.main -c config.yaml
```
Watches the rota file for changes, rebuilds `.ics` files automatically, and serves them over HTTP.

The server will be available at:
```
http://<hostname>:<port>/
```
ICS files are located under:
```
http://<hostname>:<port>/<ics_subdir>/
```

## Configuration
For modes 2 and 3, run the interactive wizard to create `config.yaml`:
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

## Serving via the web
Use Cloudflare or similar to forward `<port>` as a subdomain of an existing domain to make it web-accessible.

URL format:
```
https://SUBDOMAIN.DOMAIN/ICS_SUBDIR/PERSON.ics
```

For example:
```
https://liverota.jamescranley.co.uk/registrars/JamesCranley.ics
```

URL is **CASE SENSITIVE**.

## How to Subscribe via Calendar client

Once LiveRota is running and serving your `.ics` files, you can subscribe to them in your preferred calendar app.
Changes to the rota will be reflected in the subscribed calendar feed. You do need to ensure the calendar client refreshes automatically — updates will not be pushed to the client. Daily is fine since the rota shouldn't change often.

### Apple Calendar (macOS / iOS)
1. Open Calendar.
2. Go to **File → New Calendar Subscription...**
3. Enter the URL to the `.ics` file, for example:
   ```
   https://liverota.jamescranley.co.uk/registrars/JamesCranley.ics
   ```
   Note: URL is CASE SENSITIVE.
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
