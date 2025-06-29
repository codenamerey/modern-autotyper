#!/bin/bash
# Simple run script for modern-autotyper

cd /home/ryan/Documents/repos/modern-autotyper

# Generate sample config if it doesn't exist
if [ ! -f "sample-config.json" ]; then
    echo "Creating sample config..."
    ./venv/bin/python -c "
import json
config = {
    'tasks': [
        {'keyword': 'Hello World! ', 'interval': 2.0, 'count': 3, 'delay_before_start': 1.0},
        {'keyword': 'Python rocks! ', 'interval': 3.0, 'count': 2, 'delay_before_start': 0.5}
    ],
    'stop_key': 'esc',
    'type_delay': 0.05
}
with open('sample-config.json', 'w') as f:
    json.dump(config, f, indent=2)
print('Sample config created!')
"
fi

echo "Starting Modern Autotyper..."
echo "Open a text editor and position your cursor"
echo "The autotyper will start in 3 seconds"
echo "Press ESC to stop at any time"
echo ""

# Set DISPLAY if not set
export DISPLAY=${DISPLAY:-:0}

# Run the autotyper
PYTHONPATH=src ./venv/bin/python -c "
import sys
sys.path.insert(0, 'src')

from modern_autotyper.cli import load_config_from_file
from modern_autotyper.autotyper import AutoTyper
import time

try:
    config = load_config_from_file('sample-config.json')
    autotyper = AutoTyper(config)
    
    print('Starting in 3 seconds...')
    time.sleep(3)
    
    autotyper.start()
    autotyper.wait()
    
except KeyboardInterrupt:
    print('\\nStopped by user')
except Exception as e:
    print(f'Error: {e}')
finally:
    try:
        autotyper.stop()
    except:
        pass
"
