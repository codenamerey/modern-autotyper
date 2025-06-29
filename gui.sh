#!/bin/bash
# GUI launcher for Modern Autotyper (PyQt6)

cd /home/ryan/Documents/repos/modern-autotyper

echo "Starting Modern Autotyper GUI (PyQt6)..."

# Set DISPLAY if not set
export DISPLAY=${DISPLAY:-:0}

# Run the GUI
PYTHONPATH=src ./venv/bin/python -c "
import sys
sys.path.insert(0, 'src')

try:
    from modern_autotyper.gui import main
    main()
except Exception as e:
    print(f'Error starting GUI: {e}')
    print('Make sure you have a display available and PyQt6 installed')
"
