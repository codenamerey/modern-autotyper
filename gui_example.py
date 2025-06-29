"""GUI example for Modern Autotyper."""

import os
import sys

# Add src to path for development
sys.path.insert(0, 'src')

def main():
    """Run the GUI example."""
    # Set display
    if 'DISPLAY' not in os.environ:
        os.environ['DISPLAY'] = ':0'
    
    try:
        from modern_autotyper.gui import AutoTyperGUI
        
        print("Starting Modern Autotyper GUI...")
        print("Features:")
        print("- Add/remove multiple tasks")
        print("- Configure intervals, counts, and delays")
        print("- Load/save configurations")
        print("- Real-time status updates")
        print("- Start/stop controls")
        print("")
        
        app = AutoTyperGUI()
        app.run()
        
    except ImportError as e:
        print(f"GUI not available: {e}")
        print("Install PySimpleGUI: pip install PySimpleGUI")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
