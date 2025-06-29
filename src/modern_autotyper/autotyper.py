"""Core AutoTyper implementation."""

import threading
import time
import logging
import os
from typing import Dict, Any

# Set DISPLAY if not set (for CLI usage)
if 'DISPLAY' not in os.environ:
    os.environ['DISPLAY'] = ':0'

try:
    import pyautogui
    import keyboard
    GUI_AVAILABLE = True
except ImportError as e:
    GUI_AVAILABLE = False
    _import_error = str(e)

from .config import AutoTyperConfig, TypingTask


class AutoTyper:
    """Multi-threaded autotyper with configurable intervals."""
    
    def __init__(self, config: AutoTyperConfig):
        if not GUI_AVAILABLE:
            raise RuntimeError(f"GUI libraries not available: {_import_error}")
        
        self.config = config
        self.threads: Dict[str, threading.Thread] = {}
        self.stop_events: Dict[str, threading.Event] = {}
        self.running = False
        
        # Configure pyautogui
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.01
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _press_key_combination(self, key_combination: str):
        """Press a key combination using pyautogui."""
        # Normalize the key combination
        combo = key_combination.lower().strip()
        
        # Handle common key combinations
        if combo == "enter":
            pyautogui.press('enter')
        elif combo == "tab":
            pyautogui.press('tab')
        elif combo == "escape" or combo == "esc":
            pyautogui.press('escape')
        elif combo == "space":
            pyautogui.press('space')
        elif combo == "backspace":
            pyautogui.press('backspace')
        elif combo == "delete" or combo == "del":
            pyautogui.press('delete')
        elif combo == "home":
            pyautogui.press('home')
        elif combo == "end":
            pyautogui.press('end')
        elif combo == "pageup":
            pyautogui.press('pageup')
        elif combo == "pagedown":
            pyautogui.press('pagedown')
        elif combo == "up":
            pyautogui.press('up')
        elif combo == "down":
            pyautogui.press('down')
        elif combo == "left":
            pyautogui.press('left')
        elif combo == "right":
            pyautogui.press('right')
        elif combo.startswith("f") and combo[1:].isdigit():
            # Function keys (f1, f2, etc.)
            pyautogui.press(combo)
        elif "+" in combo:
            # Handle modifier combinations like "ctrl+c", "alt+tab", etc.
            parts = [part.strip() for part in combo.split("+")]
            if len(parts) == 2:
                modifier, key = parts
                if modifier in ["ctrl", "control"]:
                    pyautogui.hotkey('ctrl', key)
                elif modifier in ["alt"]:
                    pyautogui.hotkey('alt', key)
                elif modifier in ["shift"]:
                    pyautogui.hotkey('shift', key)
                elif modifier in ["cmd", "command", "win", "windows"]:
                    pyautogui.hotkey('win', key)
                else:
                    # Try as a generic hotkey
                    pyautogui.hotkey(modifier, key)
            elif len(parts) == 3:
                # Handle three-key combinations like "ctrl+shift+t"
                pyautogui.hotkey(parts[0], parts[1], parts[2])
            else:
                self.logger.warning(f"Unsupported key combination format: {key_combination}")
        else:
            # Try pressing as a single key
            try:
                pyautogui.press(combo)
            except Exception as e:
                self.logger.error(f"Unknown key combination: {key_combination}")
                raise e
    
    def _typing_worker(self, task: TypingTask, stop_event: threading.Event):
        """Worker function for typing tasks."""
        # Initial delay
        if task.delay_before_start > 0:
            time.sleep(task.delay_before_start)
        
        count = 0
        while not stop_event.is_set():
            if task.count is not None and count >= task.count:
                break
                
            try:
                # Click at specified coordinates if provided
                if task.click_x is not None and task.click_y is not None:
                    if stop_event.is_set():
                        return
                    pyautogui.click(task.click_x, task.click_y)
                    time.sleep(0.1)  # Small delay after click
                
                # Type the keyword with character delay
                for char in task.keyword:
                    if stop_event.is_set():
                        return
                    pyautogui.write(char)
                    time.sleep(self.config.type_delay)
                
                # Press key combination if specified
                if task.key_combination:
                    if stop_event.is_set():
                        return
                    time.sleep(0.1)  # Small delay before key combination
                    try:
                        self._press_key_combination(task.key_combination)
                    except Exception as e:
                        self.logger.error(f"Error pressing key combination '{task.key_combination}': {e}")
                
                count += 1
                coords_info = f" at ({task.click_x}, {task.click_y})" if task.click_x is not None else ""
                key_info = f" + {task.key_combination}" if task.key_combination else ""
                self.logger.debug(f"Typed '{task.keyword}'{key_info}{coords_info} (#{count})")
                
                # Wait for next interval
                time.sleep(task.interval)
                
            except Exception as e:
                self.logger.error(f"Error typing '{task.keyword}': {e}")
                break
    
    def start(self):
        """Start all typing tasks."""
        if self.running:
            self.logger.warning("AutoTyper is already running")
            return
        
        self.running = True
        self.logger.info("Starting AutoTyper...")
        
        # Start threads for each task
        for i, task in enumerate(self.config.tasks):
            task_id = f"task_{i}_{task.keyword}"
            stop_event = threading.Event()
            
            thread = threading.Thread(
                target=self._typing_worker,
                args=(task, stop_event),
                name=task_id,
                daemon=True
            )
            
            self.threads[task_id] = thread
            self.stop_events[task_id] = stop_event
            thread.start()
            
            self.logger.info(f"Started task: {task.keyword} (interval: {task.interval}s)")
        
        # Setup stop key listener
        try:
            keyboard.add_hotkey(self.config.stop_key, self.stop)
            self.logger.info(f"Press '{self.config.stop_key}' to stop")
        except Exception as e:
            self.logger.warning(f"Could not setup stop key listener: {e}")
            self.logger.info("Use GUI stop button or call stop() method to stop")
    
    def stop(self):
        """Stop all typing tasks."""
        if not self.running:
            return
        
        self.logger.info("Stopping AutoTyper...")
        self.running = False
        
        # Signal all threads to stop
        for stop_event in self.stop_events.values():
            stop_event.set()
        
        # Wait for all threads to finish
        for thread in self.threads.values():
            thread.join(timeout=1.0)
        
        # Clear containers
        self.threads.clear()
        self.stop_events.clear()
        
        # Remove hotkey
        try:
            keyboard.remove_hotkey(self.config.stop_key)
        except:
            pass
        
        self.logger.info("AutoTyper stopped")
    
    def wait(self):
        """Wait for all tasks to complete or be stopped."""
        try:
            while self.running and any(t.is_alive() for t in self.threads.values()):
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.stop()
    
    def status(self) -> Dict[str, Any]:
        """Get current status of the autotyper."""
        return {
            "running": self.running,
            "active_tasks": len([t for t in self.threads.values() if t.is_alive()]),
            "total_tasks": len(self.config.tasks),
            "tasks": [
                {
                    "keyword": task.keyword,
                    "interval": task.interval,
                    "count": task.count,
                    "delay": task.delay_before_start
                }
                for task in self.config.tasks
            ]
        }
