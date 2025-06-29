#!/bin/bash
# Activation script for modern-autotyper virtual environment

cd /home/ryan/Documents/repos/modern-autotyper
source venv/bin/activate

echo "Virtual environment activated!"
echo "Available commands:"
echo "  modern-autotyper sample config.json    # Generate sample config"
echo "  modern-autotyper run config.json       # Run from config file" 
echo "  modern-autotyper quick 'text' 2.0      # Quick run"
echo "  python example.py                      # Run example"
echo ""
echo "To deactivate: deactivate"
