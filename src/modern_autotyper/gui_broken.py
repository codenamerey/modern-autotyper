"""PySimpleGUI interface for Modern Autotyper."""

import os
import sys
import json
import threading
import time
from typing import List, Optional

# Set DISPLAY if not set
if 'DISPLAY' not in os.environ:
    os.environ['DISPLAY'] = ':0'

try:
    import PySimpleGUI as sg
    from .autotyper import AutoTyper
    from .config import AutoTyperConfig, TypingTask
    GUI_AVAILABLE = True
except ImportError as e:
    GUI_AVAILABLE = False
    _import_error = str(e)


class AutoTyperGUI:
    """GUI application for Modern Autotyper."""
    
    def __init__(self):
        if not GUI_AVAILABLE:
            raise RuntimeError(f"GUI libraries not available: {_import_error}")
        
        self.autotyper: Optional[AutoTyper] = None
        self.tasks: List[dict] = []
        self.running = False
        
        # Configure PySimpleGUI theme
        sg.theme('DarkBlue3')
        
    def create_task_layout(self, task_num: int = 0, task_data: dict = None) -> List:
        """Create layout for a single task configuration."""
        if task_data is None:
            task_data = {"keyword": "", "interval": 1.0, "count": None, "delay": 0.0}
        
        return [
            [
                sg.Text(f"Task {task_num + 1}:", size=(8, 1)),
                sg.Input(
                    task_data["keyword"], 
                    key=f"KEYWORD_{task_num}", 
                    size=(20, 1),
                    tooltip="Text to type"
                ),
                sg.Text("Interval:"),
                sg.Input(
                    str(task_data["interval"]), 
                    key=f"INTERVAL_{task_num}", 
                    size=(8, 1),
                    tooltip="Seconds between typing"
                ),
            ],
            [
                sg.Text("", size=(8, 1)),  # Spacer
                sg.Text("Count:"),
                sg.Input(
                    str(task_data["count"]) if task_data["count"] else "", 
                    key=f"COUNT_{task_num}", 
                    size=(8, 1),
                    tooltip="Number of times (empty = infinite)"
                ),
                sg.Text("Delay:"),
                sg.Input(
                    str(task_data["delay"]), 
                    key=f"DELAY_{task_num}", 
                    size=(8, 1),
                    tooltip="Delay before starting (seconds)"
                ),
                sg.Button("Remove", key=f"REMOVE_{task_num}", size=(8, 1))
            ],
            [sg.HorizontalSeparator()]
        ]
    
    def create_main_layout(self) -> List:
        """Create the main application layout."""
        # Header
        header = [
            [sg.Text("Modern Autotyper", font=("Arial", 16, "bold"))],
            [sg.Text("Multi-threaded autotyper with configurable intervals")],
            [sg.HorizontalSeparator()]
        ]
        
        # Global settings
        settings = [
            [sg.Text("Global Settings", font=("Arial", 12, "bold"))],
            [
                sg.Text("Stop Key:"),
                sg.Combo(
                    ["esc", "f1", "f2", "ctrl+c"], 
                    default_value="esc",
                    key="STOP_KEY",
                    size=(10, 1),
                    readonly=True
                ),
                sg.Text("Type Delay:"),
                sg.Input("0.05", key="TYPE_DELAY", size=(8, 1), tooltip="Delay between characters")
            ],
            [sg.HorizontalSeparator()]
        ]
        
        # Tasks section
        tasks_header = [
            [sg.Text("Tasks", font=("Arial", 12, "bold"))],
            [sg.Button("Add Task", key="ADD_TASK"), sg.Button("Clear All", key="CLEAR_ALL")]
        ]
        
        # Initial task
        tasks_area = [
            [sg.Column([], key="TASKS_COLUMN", scrollable=True, vertical_scroll_only=True, size=(650, 300))]
        ]
        
        # Control buttons
        controls = [
            [sg.HorizontalSeparator()],
            [
                sg.Button("Start", key="START", size=(10, 1), button_color=("white", "green")),
                sg.Button("Stop", key="STOP", size=(10, 1), button_color=("white", "red"), disabled=True),
                sg.Text("", size=(20, 1)),  # Spacer
                sg.Button("Load Config", key="LOAD", size=(12, 1)),
                sg.Button("Save Config", key="SAVE", size=(12, 1)),
                sg.Button("Exit", key="EXIT", size=(8, 1))
            ]
        ]
        
        # Status area
        status = [
            [sg.HorizontalSeparator()],
            [sg.Text("Status:", font=("Arial", 10, "bold"))],
            [sg.Multiline("", key="STATUS", size=(80, 6), disabled=True, autoscroll=True)]
        ]
        
        return header + settings + tasks_header + tasks_area + controls + status
    
    def add_task(self, window: sg.Window, task_data: dict = None):
        """Add a new task to the GUI."""
        task_num = len(self.tasks)
        
        if task_data is None:
            task_data = {"keyword": "", "interval": 1.0, "count": None, "delay": 0.0}
        
        self.tasks.append(task_data)
        
        # Update the tasks column
        tasks_layout = []
        for i, task in enumerate(self.tasks):
            tasks_layout.extend(self.create_task_layout(i, task))
        
        window["TASKS_COLUMN"].update(tasks_layout)
    
    def remove_task(self, window: sg.Window, task_num: int):
        """Remove a task from the GUI."""
        if 0 <= task_num < len(self.tasks):
            self.tasks.pop(task_num)
            
            # Rebuild tasks layout
            tasks_layout = []
            for i, task in enumerate(self.tasks):
                tasks_layout.extend(self.create_task_layout(i, task))
            
            window["TASKS_COLUMN"].update(tasks_layout)
    
    def clear_all_tasks(self, window: sg.Window):
        """Clear all tasks."""
        self.tasks.clear()
        window["TASKS_COLUMN"].update([])
    
    def collect_task_data(self, window: sg.Window) -> List[dict]:
        """Collect task data from the GUI."""
        tasks = []
        for i in range(len(self.tasks)):
            try:
                keyword = window[f"KEYWORD_{i}"].get().strip()
                if not keyword:
                    continue
                
                interval = float(window[f"INTERVAL_{i}"].get() or "1.0")
                count_str = window[f"COUNT_{i}"].get().strip()
                count = int(count_str) if count_str else None
                delay = float(window[f"DELAY_{i}"].get() or "0.0")
                
                tasks.append({
                    "keyword": keyword,
                    "interval": interval,
                    "count": count,
                    "delay_before_start": delay
                })
            except ValueError as e:
                self.log_status(window, f"Error in task {i+1}: {e}")
                continue
        
        return tasks
    
    def log_status(self, window: sg.Window, message: str):
        """Log a status message."""
        timestamp = time.strftime("%H:%M:%S")
        window["STATUS"].print(f"[{timestamp}] {message}")
    
    def start_autotyper(self, window: sg.Window):
        """Start the autotyper."""
        if self.running:
            self.log_status(window, "Autotyper is already running!")
            return
        
        # Collect configuration
        tasks_data = self.collect_task_data(window)
        if not tasks_data:
            self.log_status(window, "No valid tasks configured!")
            return
        
        try:
            # Create tasks
            tasks = []
            for task_data in tasks_data:
                task = TypingTask(
                    keyword=task_data["keyword"],
                    interval=task_data["interval"],
                    count=task_data["count"],
                    delay_before_start=task_data["delay_before_start"]
                )
                tasks.append(task)
            
            # Create config
            config = AutoTyperConfig(
                tasks=tasks,
                stop_key=window["STOP_KEY"].get(),
                type_delay=float(window["TYPE_DELAY"].get() or "0.05")
            )
            
            # Create autotyper
            self.autotyper = AutoTyper(config)
            
            # Update UI
            window["START"].update(disabled=True)
            window["STOP"].update(disabled=False)
            self.running = True
            
            self.log_status(window, "Starting autotyper in 3 seconds...")
            self.log_status(window, "Switch to your target window!")
            
            # Start in separate thread to avoid blocking GUI
            def start_delayed():
                time.sleep(3)
                if self.autotyper and self.running:
                    self.autotyper.start()
                    self.log_status(window, f"Autotyper started with {len(tasks)} tasks")
                    self.log_status(window, f"Press '{config.stop_key}' to stop")
            
            threading.Thread(target=start_delayed, daemon=True).start()
            
        except Exception as e:
            self.log_status(window, f"Error starting autotyper: {e}")
            self.reset_ui(window)
    
    def stop_autotyper(self, window: sg.Window):
        """Stop the autotyper."""
        if self.autotyper and self.running:
            self.autotyper.stop()
            self.log_status(window, "Autotyper stopped")
        
        self.reset_ui(window)
    
    def reset_ui(self, window: sg.Window):
        """Reset UI state."""
        self.running = False
        self.autotyper = None
        window["START"].update(disabled=False)
        window["STOP"].update(disabled=True)
    
    def load_config(self, window: sg.Window):
        """Load configuration from file."""
        filename = sg.popup_get_file(
            "Load Configuration",
            file_types=(("JSON Files", "*.json"), ("All Files", "*.*"))
        )
        
        if not filename:
            return
        
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            
            # Clear current tasks
            self.clear_all_tasks(window)
            
            # Load global settings
            window["STOP_KEY"].update(data.get("stop_key", "esc"))
            window["TYPE_DELAY"].update(str(data.get("type_delay", 0.05)))
            
            # Load tasks
            for task_data in data.get("tasks", []):
                self.add_task(window, {
                    "keyword": task_data.get("keyword", ""),
                    "interval": task_data.get("interval", 1.0),
                    "count": task_data.get("count"),
                    "delay": task_data.get("delay_before_start", 0.0)
                })
            
            self.log_status(window, f"Loaded configuration from {filename}")
            
        except Exception as e:
            sg.popup_error(f"Error loading configuration: {e}")
    
    def save_config(self, window: sg.Window):
        """Save configuration to file."""
        filename = sg.popup_get_file(
            "Save Configuration",
            save_as=True,
            file_types=(("JSON Files", "*.json"), ("All Files", "*.*")),
            default_extension=".json"
        )
        
        if not filename:
            return
        
        try:
            tasks_data = self.collect_task_data(window)
            
            config_data = {
                "tasks": tasks_data,
                "stop_key": window["STOP_KEY"].get(),
                "type_delay": float(window["TYPE_DELAY"].get() or "0.05")
            }
            
            with open(filename, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            self.log_status(window, f"Saved configuration to {filename}")
            
        except Exception as e:
            sg.popup_error(f"Error saving configuration: {e}")
    
    def run(self):
        """Run the GUI application."""
        layout = self.create_main_layout()
        window = sg.Window(
            "Modern Autotyper",
            layout,
            finalize=True,
            resizable=True,
            size=(700, 600)
        )
        
        # Add initial task
        self.add_task(window)
        
        self.log_status(window, "Modern Autotyper GUI ready")
        self.log_status(window, "Add tasks and click Start when ready")
        
        try:
            while True:
                event, values = window.read(timeout=100)
                
                if event in (sg.WIN_CLOSED, "EXIT"):
                    break
                
                elif event == "ADD_TASK":
                    self.add_task(window)
                
                elif event == "CLEAR_ALL":
                    self.clear_all_tasks(window)
                
                elif event.startswith("REMOVE_"):
                    task_num = int(event.split("_")[1])
                    self.remove_task(window, task_num)
                
                elif event == "START":
                    self.start_autotyper(window)
                
                elif event == "STOP":
                    self.stop_autotyper(window)
                
                elif event == "LOAD":
                    self.load_config(window)
                
                elif event == "SAVE":
                    self.save_config(window)
                
                # Check if autotyper finished
                if self.running and self.autotyper:
                    if not any(t.is_alive() for t in self.autotyper.threads.values()):
                        self.log_status(window, "All tasks completed")
                        self.reset_ui(window)
        
        finally:
            if self.autotyper and self.running:
                self.autotyper.stop()
            window.close()


def main():
    """Main entry point for GUI application."""
    if not GUI_AVAILABLE:
        print(f"GUI not available: {_import_error}")
        print("Please install PySimpleGUI: pip install PySimpleGUI")
        return 1
    
    try:
        app = AutoTyperGUI()
        app.run()
        return 0
    except Exception as e:
        sg.popup_error(f"Application error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
    
    def stop_autotyper(self):
        """Stop the autotyper."""
        if self.autotyper and self.running:
            self.autotyper.stop()
            self.log_status("Autotyper stopped")
        
        self.reset_ui()
    
    def reset_ui(self):
        """Reset UI state."""
        self.running = False
        self.autotyper = None
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        
        # Reset task status
        for row in range(self.tasks_table.rowCount()):
            self.tasks_table.setItem(row, 5, QTableWidgetItem("Ready"))
    
    def update_status(self):
        """Update status display."""
        if self.running and self.autotyper:
            # Check if autotyper finished
            if not any(t.is_alive() for t in self.autotyper.threads.values()):
                self.log_status("All tasks completed")
                self.reset_ui()
            else:
                # Update task status
                for row in range(self.tasks_table.rowCount()):
                    self.tasks_table.setItem(row, 5, QTableWidgetItem("Running"))
    
    def load_config(self):
        """Load configuration from file."""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Load Configuration", "", "JSON Files (*.json);;All Files (*)"
        )
        
        if filename:
            try:
                with open(filename, 'r') as f:
                    data = json.load(f)
                
                # Load global settings
                self.stop_key_combo.setCurrentText(data.get("stop_key", "esc"))
                self.type_delay_spin.setValue(data.get("type_delay", 0.05))
                
                # Load tasks
                self.tasks_data.clear()
                for task_data in data.get("tasks", []):
                    self.tasks_data.append({
                        "keyword": task_data.get("keyword", ""),
                        "interval": task_data.get("interval", 1.0),
                        "count": task_data.get("count"),
                        "delay_before_start": task_data.get("delay_before_start", 0.0),
                        "click_x": task_data.get("click_x"),
                        "click_y": task_data.get("click_y")
                    })
                
                self.update_tasks_table()
                self.log_status(f"Loaded configuration from {filename}")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error loading configuration: {e}")
    
    def save_config(self):
        """Save configuration to file."""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Configuration", "", "JSON Files (*.json);;All Files (*)"
        )
        
        if filename:
            try:
                config_data = {
                    "tasks": self.tasks_data,
                    "stop_key": self.stop_key_combo.currentText(),
                    "type_delay": self.type_delay_spin.value()
                }
                
                with open(filename, 'w') as f:
                    json.dump(config_data, f, indent=2)
                
                self.log_status(f"Saved configuration to {filename}")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error saving configuration: {e}")
    
    def closeEvent(self, event):
        """Handle window close event."""
        if self.running:
            reply = QMessageBox.question(
                self, "Autotyper Running",
                "The autotyper is currently running. Stop it and exit?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.stop_autotyper()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


class AutoTyperApp:
    """Main application class."""
    
    def __init__(self):
        if not GUI_AVAILABLE:
            raise RuntimeError(f"GUI libraries not available: {_import_error}")
        
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("Modern Autotyper")
        self.app.setOrganizationName("Modern Autotyper")
        
        # Set application style
        self.app.setStyle('Fusion')
        
        self.main_window = AutoTyperMainWindow()
    
    def run(self):
        """Run the application."""
        self.main_window.show()
        return self.app.exec()


def main():
    """Main entry point for GUI application."""
    if not GUI_AVAILABLE:
        print(f"GUI not available: {_import_error}")
        print("Please install PyQt6: pip install PyQt6")
        return 1
    
    try:
        app = AutoTyperApp()
        return app.run()
    except Exception as e:
        print(f"Application error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
