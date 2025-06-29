# Modern Autotyper

A multi-threaded autotyper that enables multiple keywords to be typed on predetermined intervals simultaneously.

## Features

- **Multi-threaded**: Run multiple typing tasks concurrently
- **Configurable intervals**: Set different typing intervals for each keyword
- **Count control**: Specify how many times each keyword should be typed
- **Delay control**: Set initial delay before each task starts
- **Stop key**: Emergency stop functionality (default: ESC)
- **CLI interface**: Command line tool for easy usage

## Quick Start

```bash
# Clone and setup
git clone <repo-url>
cd modern-autotyper

# Create virtual environment and install
python3 -m venv venv
source venv/bin/activate
pip install -e .

# Quick demo
./run.sh
```

## Installation

### Virtual Environment (Recommended)
```bash
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

### System Installation
```bash
pip install -e .
```

## Usage

### Quick Demo
```bash
./run.sh  # Runs with sample configuration
```

### Activation Script
```bash
source activate.sh  # Activates venv and shows commands
```

### Command Line

Generate sample config:
```bash
modern-autotyper-config sample-config.json
# or create manually - see Configuration Format below
```

Run with config file:
```bash
modern-autotyper run sample-config.json
```

Quick run:
```bash
modern-autotyper quick "Hello World" 2.0 --count 5
```

## GUI Usage

### Installing GUI Support
```bash
# Install PyQt6
./venv/bin/pip install PyQt6
```

### Running the GUI
```bash
# Method 1: Direct launcher
./gui.sh

# Method 2: Using virtual environment
source activate.sh
modern-autotyper-gui

# Method 3: Python directly
PYTHONPATH=src ./venv/bin/python -c "from modern_autotyper.gui import main; main()"
```

### GUI Features
- **Add/Edit Tasks**: Click "Add Task" to open a detailed task configuration dialog
- **Mouse Coordinates**: Optionally specify click coordinates for each task
- **Interactive Coordinate Picker**: Click "Pick Coordinates Interactively" then:
  1. Move mouse to desired location
  2. Press SPACE to select coordinates
  3. Press ESC to cancel
- **Task Management**: Edit, remove, or clear tasks with dedicated buttons
- **Real-time Status**: Monitor task execution with live status updates
- **Configuration**: Save/load task configurations as JSON files

**Note**: GUI requires a display server (X11/Wayland). For headless systems, use CLI interface.

### Configuration Format

```json
{
  "tasks": [
    {
      "keyword": "Hello World!",
      "interval": 2.0,
      "count": 5,
      "delay_before_start": 1.0
    },
    {
      "keyword": "Python rocks!",
      "interval": 3.5,
      "count": null,
      "delay_before_start": 0.5
    }
  ],
  "stop_key": "esc",
  "type_delay": 0.05
}
```

## Safety

- Built-in pyautogui failsafe (move mouse to corner to stop)
- Configurable stop key (default: ESC)
- Exception handling for robust operation

## Requirements

- Python 3.8+
- pyautogui
- keyboard
