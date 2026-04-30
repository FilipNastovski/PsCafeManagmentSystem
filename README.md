# PlayStation Management System

A lightweight desktop application for managing PlayStation devices in a café.

## Requirements

- Python 3.8+
- PySide6
- Linux Mint (or any Debian-based Linux distribution)

## Installation

### 1. Install Python and dependencies

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv libportaudio2
```

### 2. Set up the application

```bash
cd PsCafeManagmentSystem

# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

```

### 3. Run the application

```bash
python3 main.py
```

Or use the run script:

```bash
chmod +x run.sh
./run.sh
```

## Features

- **Dashboard**: View all devices with real-time status
- **Session Management**: Start timed or open-ended sessions
- **Pricing**: Automatic minute-based billing in MKD
- **Alerts**: Sound notification when timed sessions expire
- **Reports**: Today, Week, Month, or custom date ranges
- **Device Management**: Add, edit, or remove devices

## Usage

### Starting a Session

1. Click "Start" on an available device card
2. Choose Timed (fixed duration) or Open (no time limit) session
3. For timed sessions, select duration and confirm

### Ending a Session

1. Click "End" on an active device
2. Review the session summary
3. Optionally extend the session if needed
4. Confirm to end and calculate final price

### Viewing Reports

1. Click "Reports" button
2. Select period (Today, Week, Month, or Custom)
3. Filter by device if needed
4. Click "Refresh" to update

## Database

All data is stored locally in `pscafe.db`. The database is automatically created on first run.

## Troubleshooting

### No sound alert
- Install libportaudio: `sudo apt install libportaudio2`
- Or ensure alert.wav exists in the resources folder

### Qt errors
- Try: `sudo apt install libxcb-cursor0 libxkbcommon-x11-0`

### Device in use error
- End the current session first, or check for sessions that weren't properly closed