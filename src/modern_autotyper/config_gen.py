"""Standalone config generator that doesn't require GUI libraries."""

import json
import argparse
from pathlib import Path


def create_sample_config(output_path: str):
    """Create a sample configuration file."""
    sample_config = {
        "tasks": [
            {
                "keyword": "Hello World!",
                "interval": 2.0,
                "count": 5,
                "delay_before_start": 1.0
            },
            {
                "keyword": "Python is awesome",
                "interval": 3.5,
                "count": None,
                "delay_before_start": 0.5
            }
        ],
        "stop_key": "esc",
        "type_delay": 0.05
    }
    
    with open(output_path, 'w') as f:
        json.dump(sample_config, f, indent=2)
    
    print(f"Sample config created: {output_path}")


def main():
    """Config generator entry point."""
    parser = argparse.ArgumentParser(description="Generate sample config for Modern Autotyper")
    parser.add_argument("output", help="Output path for sample config")
    
    args = parser.parse_args()
    create_sample_config(args.output)


if __name__ == "__main__":
    main()
