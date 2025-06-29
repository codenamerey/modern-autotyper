"""Command line interface for Modern Autotyper."""

import argparse
import json
import sys
import os
from pathlib import Path


def load_config_from_file(config_path: str):
    """Load configuration from JSON file."""
    try:
        with open(config_path, 'r') as f:
            data = json.load(f)
        
        # Import here to avoid GUI dependency for config operations
        from .config import AutoTyperConfig, TypingTask
        
        tasks = [
            TypingTask(
                keyword=task["keyword"],
                interval=task["interval"],
                count=task.get("count"),
                delay_before_start=task.get("delay_before_start", 0.0)
            )
            for task in data["tasks"]
        ]
        
        return AutoTyperConfig(
            tasks=tasks,
            stop_key=data.get("stop_key", "esc"),
            type_delay=data.get("type_delay", 0.05)
        )
    except Exception as e:
        print(f"Error loading config: {e}")
        sys.exit(1)


def create_sample_config(output_path: str):
    """Create a sample configuration file."""
    from .config_gen import create_sample_config as _create_sample_config
    _create_sample_config(output_path)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Modern Autotyper - Multi-threaded autotyper")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Run command
    run_parser = subparsers.add_parser("run", help="Run autotyper")
    run_parser.add_argument("config", help="Path to configuration file")
    run_parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    # Sample config command
    sample_parser = subparsers.add_parser("sample", help="Generate sample config")
    sample_parser.add_argument("output", help="Output path for sample config")
    
    # Quick run command
    quick_parser = subparsers.add_parser("quick", help="Quick run with simple config")
    quick_parser.add_argument("keyword", help="Text to type")
    quick_parser.add_argument("interval", type=float, help="Interval in seconds")
    quick_parser.add_argument("--count", "-c", type=int, help="Number of times to type")
    quick_parser.add_argument("--delay", "-d", type=float, default=0.0, help="Delay before start")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == "sample":
        create_sample_config(args.output)
        return
    
    elif args.command == "run":
        # Check display for GUI operations
        if 'DISPLAY' not in os.environ:
            os.environ['DISPLAY'] = ':0'
            
        from .autotyper import AutoTyper
        config = load_config_from_file(args.config)
        
    elif args.command == "quick":
        # Check display for GUI operations
        if 'DISPLAY' not in os.environ:
            os.environ['DISPLAY'] = ':0'
            
        from .autotyper import AutoTyper
        from .config import TypingTask, AutoTyperConfig
        
        task = TypingTask(
            keyword=args.keyword,
            interval=args.interval,
            count=args.count,
            delay_before_start=args.delay
        )
        config = AutoTyperConfig(tasks=[task])
    
    # Create and run autotyper
    if args.command in ["run", "quick"]:
        autotyper = AutoTyper(config)
        
        try:
            print("Starting in 3 seconds... Move cursor to target window")
            import time
            time.sleep(3)
            
            autotyper.start()
            autotyper.wait()
            
        except KeyboardInterrupt:
            print("\nInterrupted by user")
        finally:
            autotyper.stop()


if __name__ == "__main__":
    main()
