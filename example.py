"""Example usage of Modern Autotyper."""

from modern_autotyper import AutoTyper, AutoTyperConfig, TypingTask
import time


def main():
    """Example usage."""
    
    # Create typing tasks
    tasks = [
        TypingTask(
            keyword="Hello World! ",
            interval=2.0,
            count=3,
            delay_before_start=1.0
        ),
        TypingTask(
            keyword="Python is great! ",
            interval=3.0,
            count=2,
            delay_before_start=0.5
        )
    ]
    
    # Create configuration
    config = AutoTyperConfig(
        tasks=tasks,
        stop_key="esc",
        type_delay=0.05
    )
    
    # Create autotyper
    autotyper = AutoTyper(config)
    
    print("Starting autotyper in 3 seconds...")
    print("Open a text editor and position your cursor")
    print("Press ESC to stop at any time")
    
    time.sleep(3)

    try:
        autotyper.start()
        autotyper.wait()
    except KeyboardInterrupt:
        print("\nStopped by user")
    finally:
        autotyper.stop()


if __name__ == "__main__":
    main()
