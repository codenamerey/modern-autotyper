"""PyQt6 GUI interface for Modern Autotyper."""

import os
import sys
import json
import threading
import time
from typing import List, Optional, Dict, Any

# Set DISPLAY if not set
if 'DISPLAY' not in os.environ:
    os.environ['DISPLAY'] = ':0'

try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QLabel, QLineEdit, QPushButton, QTextEdit, QComboBox, QSpinBox,
        QDoubleSpinBox, QTableWidget, QTableWidgetItem, QHeaderView,
        QDialog, QFormLayout, QCheckBox, QGroupBox,
        QMessageBox, QFileDialog
    )
    from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
    from PyQt6.QtGui import QFont
    
    from .autotyper import AutoTyper
    from .config import AutoTyperConfig, TypingTask
    GUI_AVAILABLE = True
    
    # Simplified coordinate picker without QThread
    class CoordinatePickerWorker:
        """Simple coordinate picker without threads."""
        
        def __init__(self, dialog):
            self.dialog = dialog
            self.cancelled = False
        
        def start_picking(self):
            """Start coordinate picking with timer-based approach."""
            print("Starting coordinate picker...")
            
            # Try fallback approach - just wait a moment then pick coordinates
            try:
                import pyautogui
                print("Using simple coordinate picker - will pick coordinates after 2 seconds")
                
                # Use QTimer for the delay instead of threading
                QTimer.singleShot(2000, self.pick_coordinates)
                
            except Exception as e:
                print(f"Error in coordinate picker: {e}")
                self.dialog.on_picking_cancelled()
        
        def pick_coordinates(self):
            """Pick coordinates after delay."""
            if self.cancelled:
                return
                
            try:
                import pyautogui
                x, y = pyautogui.position()
                print(f"Picked coordinates: {x}, {y}")
                self.dialog.on_coordinates_picked(x, y)
            except Exception as e:
                print(f"Error getting mouse position: {e}")
                self.dialog.on_picking_cancelled()
        
        def cancel(self):
            """Cancel coordinate picking."""
            self.cancelled = True

    class SimpleCoordinatePickerDialog(QDialog):
        """Simplified coordinate picker that directly updates parent."""
        
        def __init__(self, parent_dialog):
            super().__init__(parent_dialog)
            self.parent_dialog = parent_dialog
            self.setWindowTitle("Pick Mouse Coordinates")
            self.setModal(True)
            self.resize(450, 250)
            self.picking = False
            
            layout = QVBoxLayout()
            
            instructions = QLabel(
                "Click 'Start Picking' to begin coordinate selection.\n"
                "The dialog will minimize so you can see other applications.\n\n"
                "Move your mouse to the desired location and press SPACE\n"
                "to select those coordinates, or press ESC to cancel."
            )
            instructions.setWordWrap(True)
            layout.addWidget(instructions)
            
            self.status_label = QLabel("Ready to pick coordinates")
            self.status_label.setFont(QFont("monospace", 12))
            self.status_label.setStyleSheet("background: #f0f0f0; padding: 10px; border: 1px solid #ccc;")
            layout.addWidget(self.status_label)
            
            button_layout = QHBoxLayout()
            
            self.pick_button = QPushButton("Start Picking")
            self.pick_button.clicked.connect(self.start_picking)
            button_layout.addWidget(self.pick_button)
            
            self.cancel_button = QPushButton("Cancel Picking")
            self.cancel_button.clicked.connect(self.cancel_picking)
            self.cancel_button.setEnabled(False)
            button_layout.addWidget(self.cancel_button)
            
            close_button = QPushButton("Close")
            close_button.clicked.connect(self.accept)
            button_layout.addWidget(close_button)
            
            layout.addLayout(button_layout)
            self.setLayout(layout)
            
            # Timer for checking mouse clicks
            self.click_timer = QTimer()
            self.click_timer.timeout.connect(self.check_for_click)
            self.last_mouse_pos = None
        
        def start_picking(self):
            """Start coordinate picking."""
            self.picking = True
            self.pick_button.setEnabled(False)
            self.cancel_button.setEnabled(True)
            self.status_label.setText("Move mouse to desired location and press SPACE\nPress ESC to cancel")
            
            # Minimize dialog so user can click anywhere
            self.showMinimized()
            
            # Start checking for mouse clicks
            try:
                import pyautogui
                self.last_mouse_pos = pyautogui.position()
                self.click_timer.start(50)  # Check every 50ms
            except Exception as e:
                print(f"Error starting picker: {e}")
                self.cancel_picking()
        
        def check_for_click(self):
            """Check if mouse has been clicked."""
            if not self.picking:
                return
                
            try:
                import pyautogui
                
                # Check for ESC key to cancel
                try:
                    import keyboard
                    if keyboard.is_pressed('escape'):
                        self.cancel_picking()
                        return
                except:
                    pass  # Ignore keyboard errors
                
                # Simple approach: try to detect mouse button state
                try:
                    # Get current mouse position
                    current_pos = pyautogui.position()
                    
                    # Try pynput for better click detection
                    try:
                        from pynput import mouse
                        # Check if mouse button is currently pressed
                        # This is a simple workaround - we'll use a different approach
                        pass
                    except ImportError:
                        pass
                    
                    # Fallback: use a simple approach with SPACE key
                    try:
                        import keyboard
                        if keyboard.is_pressed('space'):
                            # User pressed space, pick current coordinates
                            while keyboard.is_pressed('space'):
                                import time
                                time.sleep(0.05)  # Wait for key release
                            self.pick_coordinates_at_position(current_pos)
                            return
                    except:
                        pass
                        
                    # Update status with current position
                    if hasattr(self, 'last_status_update'):
                        import time
                        if time.time() - self.last_status_update > 0.5:  # Update every 500ms
                            self.status_label.setText(f"Current position: ({current_pos[0]}, {current_pos[1]})\nPress SPACE to select, ESC to cancel")
                            self.last_status_update = time.time()
                    else:
                        import time
                        self.last_status_update = time.time()
                        
                except Exception as e:
                    print(f"Error in click detection: {e}")
                    
            except Exception as e:
                print(f"Error checking for click: {e}")
                self.cancel_picking()
        
        def pick_coordinates_at_position(self, pos):
            """Pick coordinates at the given position."""
            self.picking = False
            self.click_timer.stop()
            
            x, y = pos
            print(f"Picked coordinates: x={x}, y={y}")
            
            # Directly update the parent dialog
            self.parent_dialog.use_coords_check.setChecked(True)
            self.parent_dialog.x_spin.setValue(x)
            self.parent_dialog.y_spin.setValue(y)
            
            print(f"Updated parent: checkbox={self.parent_dialog.use_coords_check.isChecked()}")
            print(f"Updated parent: x={self.parent_dialog.x_spin.value()}, y={self.parent_dialog.y_spin.value()}")
            
            # Restore dialog
            self.showNormal()
            self.activateWindow()
            self.raise_()
            
            self.status_label.setText(f"Coordinates picked: ({x}, {y})\nUpdated task configuration.")
            self.pick_button.setText("Pick Again")
            self.pick_button.setEnabled(True)
            self.cancel_button.setEnabled(False)
        
        def cancel_picking(self):
            """Cancel coordinate picking."""
            self.picking = False
            self.click_timer.stop()
            
            # Restore dialog
            self.showNormal()
            self.activateWindow()
            self.raise_()
            
            self.status_label.setText("Coordinate picking cancelled")
            self.pick_button.setEnabled(True)
            self.cancel_button.setEnabled(False)
        
        def keyPressEvent(self, event):
            """Handle key press events."""
            if event.key() == Qt.Key.Key_Escape and self.picking:
                self.cancel_picking()
            else:
                super().keyPressEvent(event)

    class CoordinatePickerDialog(QDialog):
        """Dialog for picking mouse coordinates interactively."""
        
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setWindowTitle("Pick Mouse Coordinates")
            self.setModal(True)
            self.resize(400, 300)
            
            layout = QVBoxLayout()
            
            instructions = QLabel(
                "Instructions:\n"
                "1. Click 'Start Picking'\n"
                "2. Move mouse to desired location\n"
                "3. Coordinates will be picked automatically after 2 seconds\n\n"
                "Note: Position your mouse where you want to click\n"
                "before clicking 'Start Picking'."
            )
            instructions.setWordWrap(True)
            layout.addWidget(instructions)
            
            self.coord_label = QLabel("No coordinates selected")
            self.coord_label.setFont(QFont("monospace", 12))
            self.coord_label.setStyleSheet("background: #f0f0f0; padding: 10px; border: 1px solid #ccc;")
            layout.addWidget(self.coord_label)
            
            button_layout = QHBoxLayout()
            
            self.pick_button = QPushButton("Start Picking")
            self.pick_button.clicked.connect(self.start_picking)
            button_layout.addWidget(self.pick_button)
            
            self.ok_button = QPushButton("OK")
            self.ok_button.clicked.connect(self.accept)
            self.ok_button.setEnabled(False)
            button_layout.addWidget(self.ok_button)
            
            cancel_button = QPushButton("Cancel")
            cancel_button.clicked.connect(self.reject)
            button_layout.addWidget(cancel_button)
            
            layout.addLayout(button_layout)
            self.setLayout(layout)
            
            self.selected_x = None
            self.selected_y = None
            self.coord_timer = QTimer()
            self.coord_timer.timeout.connect(self.update_coordinates)
            self.picking = False
        
        def start_picking(self):
            """Start the coordinate picking process."""
            try:
                self.picking = True
                self.pick_button.setText("Picking in 2 seconds...")
                self.pick_button.setEnabled(False)
                self.hide()
                
                # Create picker worker
                self.picker_worker = CoordinatePickerWorker(self)
                self.picker_worker.start_picking()
                
            except Exception as e:
                print(f"Error starting coordinate picker: {e}")
                import traceback
                traceback.print_exc()
                self.on_picking_cancelled()
        
        def update_coordinates(self):
            """Update current mouse coordinates display."""
            if self.picking:
                try:
                    import pyautogui
                    x, y = pyautogui.position()
                    self.coord_label.setText(f"Current position: ({x}, {y})\nPress SPACE to select")
                except:
                    pass
        
        def on_coordinates_picked(self, x, y):
            """Handle coordinates being picked."""
            print(f"on_coordinates_picked called with x={x}, y={y}")
            self.selected_x = x
            self.selected_y = y
            self.picking = False
            self.coord_timer.stop()
            
            self.show()
            self.coord_label.setText(f"Selected coordinates: ({x}, {y})")
            self.pick_button.setText("Pick Different Coordinates")
            self.pick_button.setEnabled(True)
            self.ok_button.setEnabled(True)
            print(f"Coordinates stored: selected_x={self.selected_x}, selected_y={self.selected_y}")
            
            # Auto-accept the dialog since coordinates were successfully picked
            print("Auto-accepting dialog with coordinates")
            self.accept()
        
        def on_picking_cancelled(self):
            """Handle coordinate picking being cancelled."""
            self.picking = False
            self.coord_timer.stop()
            
            self.show()
            self.coord_label.setText("Coordinate picking cancelled")
            self.pick_button.setText("Start Picking")
            self.pick_button.setEnabled(True)
        
        def get_coordinates(self):
            """Get the selected coordinates."""
            print(f"get_coordinates returning: x={self.selected_x}, y={self.selected_y}")
            return self.selected_x, self.selected_y
        
        def closeEvent(self, event):
            """Clean up when dialog is closed."""
            if hasattr(self, 'picker_worker'):
                self.picker_worker.cancel()
            event.accept()

    class TaskEditDialog(QDialog):
        """Dialog for editing task configuration."""
        
        def __init__(self, task=None, parent=None):
            super().__init__(parent)
            self.setWindowTitle("Add/Edit Task")
            self.setModal(True)
            self.resize(500, 400)
            
            layout = QVBoxLayout()
            
            # Form layout for task configuration
            form_layout = QFormLayout()
            
            self.keyword_edit = QLineEdit()
            if task:
                self.keyword_edit.setText(task.get('keyword', ''))
            form_layout.addRow("Keyword:", self.keyword_edit)
            
            self.interval_spin = QDoubleSpinBox()
            self.interval_spin.setRange(0.1, 3600.0)
            self.interval_spin.setValue(task.get('interval', 1.0) if task else 1.0)
            self.interval_spin.setSuffix(" seconds")
            form_layout.addRow("Interval:", self.interval_spin)
            
            self.count_spin = QSpinBox()
            self.count_spin.setRange(0, 99999)
            self.count_spin.setValue(task.get('count', 0) if task and task.get('count') else 0)
            self.count_spin.setSpecialValueText("Unlimited")
            form_layout.addRow("Count:", self.count_spin)
            
            self.delay_spin = QDoubleSpinBox()
            self.delay_spin.setRange(0.0, 3600.0)
            self.delay_spin.setValue(task.get('delay_before_start', 0.0) if task else 0.0)
            self.delay_spin.setSuffix(" seconds")
            form_layout.addRow("Delay Before Start:", self.delay_spin)
            
            # Key combination field
            self.key_combo_edit = QLineEdit()
            if task:
                self.key_combo_edit.setText(task.get('key_combination', ''))
            self.key_combo_edit.setPlaceholderText("e.g., enter, ctrl+c, alt+tab (optional)")
            form_layout.addRow("Key Combination:", self.key_combo_edit)
            
            layout.addLayout(form_layout)
            
            # Mouse coordinates section
            coord_group = QGroupBox("Mouse Coordinates (Optional)")
            coord_layout = QVBoxLayout()
            
            self.use_coords_check = QCheckBox("Click at specific coordinates")
            coord_layout.addWidget(self.use_coords_check)
            
            coord_form = QFormLayout()
            
            self.x_spin = QSpinBox()
            self.x_spin.setRange(0, 9999)
            self.x_spin.setValue(task.get('x', 0) if task and task.get('x') else 0)
            self.x_spin.setEnabled(False)
            coord_form.addRow("X:", self.x_spin)
            
            self.y_spin = QSpinBox()
            self.y_spin.setRange(0, 9999)
            self.y_spin.setValue(task.get('y', 0) if task and task.get('y') else 0)
            self.y_spin.setEnabled(False)
            coord_form.addRow("Y:", self.y_spin)
            
            coord_layout.addLayout(coord_form)
            
            self.pick_coords_button = QPushButton("Pick Coordinates Interactively")
            self.pick_coords_button.clicked.connect(self.pick_coordinates)
            self.pick_coords_button.setEnabled(False)
            coord_layout.addWidget(self.pick_coords_button)
            
            coord_group.setLayout(coord_layout)
            layout.addWidget(coord_group)
            
            # Connect checkbox to enable/disable coordinate inputs
            self.use_coords_check.toggled.connect(self.x_spin.setEnabled)
            self.use_coords_check.toggled.connect(self.y_spin.setEnabled)
            self.use_coords_check.toggled.connect(self.pick_coords_button.setEnabled)
            
            # Set initial state from task
            if task and (task.get('x') is not None or task.get('y') is not None):
                self.use_coords_check.setChecked(True)
            
            # Buttons
            button_layout = QHBoxLayout()
            
            ok_button = QPushButton("OK")
            ok_button.clicked.connect(self.accept)
            button_layout.addWidget(ok_button)
            
            cancel_button = QPushButton("Cancel")
            cancel_button.clicked.connect(self.reject)
            button_layout.addWidget(cancel_button)
            
            layout.addLayout(button_layout)
            self.setLayout(layout)
        
        def pick_coordinates(self):
            """Open coordinate picker dialog."""
            # Create a simple dialog that directly updates this dialog
            dialog = SimpleCoordinatePickerDialog(self)
            dialog.exec()
        
        def get_task_data(self):
            """Get the task data from the dialog."""
            task_data = {
                'keyword': self.keyword_edit.text(),
                'interval': self.interval_spin.value(),
                'count': self.count_spin.value() if self.count_spin.value() > 0 else None,
                'delay_before_start': self.delay_spin.value()
            }
            
            # Add key combination if specified
            key_combo = self.key_combo_edit.text().strip()
            if key_combo:
                task_data['key_combination'] = key_combo
            
            print(f"get_task_data: use_coords_check.isChecked() = {self.use_coords_check.isChecked()}")
            print(f"get_task_data: x_spin.value() = {self.x_spin.value()}, y_spin.value() = {self.y_spin.value()}")
            print(f"get_task_data: key_combination = {task_data.get('key_combination', 'None')}")
            
            if self.use_coords_check.isChecked():
                task_data['x'] = self.x_spin.value()
                task_data['y'] = self.y_spin.value()
                print(f"get_task_data: Added coordinates to task_data: x={task_data['x']}, y={task_data['y']}")
            else:
                print("get_task_data: Coordinates not included (checkbox not checked)")
            
            print(f"get_task_data: Final task_data = {task_data}")
            return task_data

    class AutoTyperGUI(QMainWindow):
        """Main GUI application for Modern Autotyper."""
        
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Modern Autotyper")
            self.setGeometry(100, 100, 800, 600)
            
            self.autotyper = None
            self.running = False
            self.tasks = []
            
            self.init_ui()
            
            # Status update timer
            self.status_timer = QTimer()
            self.status_timer.timeout.connect(self.update_status)
        
        def init_ui(self):
            """Initialize the user interface."""
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            
            layout = QVBoxLayout()
            
            # Title
            title = QLabel("Modern Autotyper")
            title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
            title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(title)
            
            # Task management section
            task_group = QGroupBox("Tasks")
            task_layout = QVBoxLayout()
            
            # Task table
            self.task_table = QTableWidget()
            self.task_table.setColumnCount(7)
            self.task_table.setHorizontalHeaderLabels(["Keyword", "Interval", "Count", "Delay", "Key Combo", "Coordinates", "Status"])
            self.task_table.horizontalHeader().setStretchLastSection(True)
            task_layout.addWidget(self.task_table)
            
            # Task buttons
            task_button_layout = QHBoxLayout()
            
            add_task_button = QPushButton("Add Task")
            add_task_button.clicked.connect(self.add_task)
            task_button_layout.addWidget(add_task_button)
            
            edit_task_button = QPushButton("Edit Task")
            edit_task_button.clicked.connect(self.edit_task)
            task_button_layout.addWidget(edit_task_button)
            
            remove_task_button = QPushButton("Remove Task")
            remove_task_button.clicked.connect(self.remove_task)
            task_button_layout.addWidget(remove_task_button)
            
            clear_tasks_button = QPushButton("Clear All")
            clear_tasks_button.clicked.connect(self.clear_tasks)
            task_button_layout.addWidget(clear_tasks_button)
            
            task_layout.addLayout(task_button_layout)
            task_group.setLayout(task_layout)
            layout.addWidget(task_group)
            
            # Control section
            control_group = QGroupBox("Control")
            control_layout = QVBoxLayout()
            
            # Start/Stop buttons
            control_button_layout = QHBoxLayout()
            
            self.start_button = QPushButton("Start")
            self.start_button.clicked.connect(self.start_autotyper)
            control_button_layout.addWidget(self.start_button)
            
            self.stop_button = QPushButton("Stop")
            self.stop_button.clicked.connect(self.stop_autotyper)
            self.stop_button.setEnabled(False)
            control_button_layout.addWidget(self.stop_button)
            
            control_layout.addLayout(control_button_layout)
            
            # Configuration section
            config_layout = QHBoxLayout()
            
            load_config_button = QPushButton("Load Config")
            load_config_button.clicked.connect(self.load_config)
            config_layout.addWidget(load_config_button)
            
            save_config_button = QPushButton("Save Config")
            save_config_button.clicked.connect(self.save_config)
            config_layout.addWidget(save_config_button)
            
            control_layout.addLayout(config_layout)
            control_group.setLayout(control_layout)
            layout.addWidget(control_group)
            
            # Status section
            status_group = QGroupBox("Status")
            status_layout = QVBoxLayout()
            
            self.status_text = QTextEdit()
            self.status_text.setMaximumHeight(150)
            self.status_text.setReadOnly(True)
            status_layout.addWidget(self.status_text)
            
            status_group.setLayout(status_layout)
            layout.addWidget(status_group)
            
            central_widget.setLayout(layout)
            
            self.log_status("Modern Autotyper GUI ready")
        
        def log_status(self, message):
            """Add message to status log."""
            timestamp = time.strftime("%H:%M:%S")
            self.status_text.append(f"[{timestamp}] {message}")
        
        def update_task_table(self):
            """Update the task table display."""
            self.task_table.setRowCount(len(self.tasks))
            
            for i, task in enumerate(self.tasks):
                self.task_table.setItem(i, 0, QTableWidgetItem(task.get('keyword', '')))
                self.task_table.setItem(i, 1, QTableWidgetItem(f"{task.get('interval', 1.0):.1f}s"))
                count_str = str(task.get('count', 'Unlimited')) if task.get('count') else 'Unlimited'
                self.task_table.setItem(i, 2, QTableWidgetItem(count_str))
                self.task_table.setItem(i, 3, QTableWidgetItem(f"{task.get('delay_before_start', 0.0):.1f}s"))
                
                # Key combination
                key_combo_str = task.get('key_combination', 'None') or 'None'
                self.task_table.setItem(i, 4, QTableWidgetItem(key_combo_str))
                
                # Coordinates
                coords_str = "None"
                if task.get('x') is not None and task.get('y') is not None:
                    coords_str = f"({task.get('x')}, {task.get('y')})"
                self.task_table.setItem(i, 5, QTableWidgetItem(coords_str))
                
                # Status
                status_str = task.get('status', 'Ready')
                self.task_table.setItem(i, 6, QTableWidgetItem(status_str))
        
        def add_task(self):
            """Add a new task."""
            dialog = TaskEditDialog(parent=self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                task_data = dialog.get_task_data()
                if task_data['keyword']:
                    task_data['status'] = 'Ready'
                    self.tasks.append(task_data)
                    self.update_task_table()
                    self.log_status(f"Added task: {task_data['keyword']}")
        
        def edit_task(self):
            """Edit the selected task."""
            current_row = self.task_table.currentRow()
            if current_row >= 0 and current_row < len(self.tasks):
                task = self.tasks[current_row]
                dialog = TaskEditDialog(task, parent=self)
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    task_data = dialog.get_task_data()
                    if task_data['keyword']:
                        task_data['status'] = task.get('status', 'Ready')
                        self.tasks[current_row] = task_data
                        self.update_task_table()
                        self.log_status(f"Updated task: {task_data['keyword']}")
        
        def remove_task(self):
            """Remove the selected task."""
            current_row = self.task_table.currentRow()
            if current_row >= 0 and current_row < len(self.tasks):
                task = self.tasks.pop(current_row)
                self.update_task_table()
                self.log_status(f"Removed task: {task.get('keyword', 'Unknown')}")
        
        def clear_tasks(self):
            """Clear all tasks."""
            if self.tasks:
                reply = QMessageBox.question(
                    self, 'Clear Tasks', 
                    'Are you sure you want to clear all tasks?',
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    self.tasks.clear()
                    self.update_task_table()
                    self.log_status("Cleared all tasks")
        
        def start_autotyper(self):
            """Start the autotyper with current tasks."""
            if not self.tasks:
                QMessageBox.warning(self, "No Tasks", "Please add at least one task before starting.")
                return
            
            try:
                # Convert tasks to TypingTask objects
                typing_tasks = []
                for task in self.tasks:
                    # Set coordinates if they exist
                    click_x = task.get('x') if task.get('x') is not None else None
                    click_y = task.get('y') if task.get('y') is not None else None
                    
                    typing_task = TypingTask(
                        keyword=task['keyword'],
                        interval=task['interval'],
                        count=task.get('count'),
                        delay_before_start=task.get('delay_before_start', 0.0),
                        click_x=click_x,
                        click_y=click_y,
                        key_combination=task.get('key_combination')
                    )
                    typing_tasks.append(typing_task)
                
                # Create config
                config = AutoTyperConfig(tasks=typing_tasks)
                
                # Start autotyper
                self.autotyper = AutoTyper(config)
                self.autotyper.start()
                
                self.running = True
                self.start_button.setEnabled(False)
                self.stop_button.setEnabled(True)
                
                # Start status updates
                self.status_timer.start(1000)
                
                self.log_status("Started autotyper")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to start autotyper: {str(e)}")
                self.log_status(f"Error starting autotyper: {str(e)}")
        
        def stop_autotyper(self):
            """Stop the autotyper."""
            if self.autotyper:
                self.autotyper.stop()
                self.autotyper = None
            
            self.running = False
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            
            # Stop status updates
            self.status_timer.stop()
            
            # Reset task statuses
            for task in self.tasks:
                task['status'] = 'Ready'
            self.update_task_table()
            
            self.log_status("Stopped autotyper")
        
        def update_status(self):
            """Update task status display."""
            if self.autotyper and self.running:
                # Update task statuses based on autotyper state
                for i, task in enumerate(self.tasks):
                    if i < len(self.autotyper.config.tasks):
                        autotyper_task = self.autotyper.config.tasks[i]
                        # For now, just mark as running since we don't have detailed status
                        task['status'] = 'Running'
                
                self.update_task_table()
        
        def load_config(self):
            """Load configuration from file."""
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Load Configuration", "", "JSON Files (*.json)"
            )
            
            if file_path:
                try:
                    with open(file_path, 'r') as f:
                        config_data = json.load(f)
                    
                    if 'tasks' in config_data:
                        self.tasks = config_data['tasks']
                        for task in self.tasks:
                            task['status'] = 'Ready'
                        self.update_task_table()
                        self.log_status(f"Loaded configuration from {file_path}")
                    else:
                        QMessageBox.warning(self, "Invalid Config", "Configuration file does not contain tasks.")
                        
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to load configuration: {str(e)}")
                    self.log_status(f"Error loading config: {str(e)}")
        
        def save_config(self):
            """Save configuration to file."""
            if not self.tasks:
                QMessageBox.warning(self, "No Tasks", "No tasks to save.")
                return
            
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save Configuration", "", "JSON Files (*.json)"
            )
            
            if file_path:
                try:
                    # Remove status from tasks before saving
                    save_tasks = []
                    for task in self.tasks:
                        save_task = {k: v for k, v in task.items() if k != 'status'}
                        save_tasks.append(save_task)
                    
                    config_data = {
                        "tasks": save_tasks,
                        "stop_key": "esc",
                        "type_delay": 0.05
                    }
                    
                    with open(file_path, 'w') as f:
                        json.dump(config_data, f, indent=2)
                    
                    self.log_status(f"Saved configuration to {file_path}")
                    
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to save configuration: {str(e)}")
                    self.log_status(f"Error saving config: {str(e)}")
        
        def closeEvent(self, event):
            """Handle application close event."""
            if self.running:
                self.stop_autotyper()
            event.accept()

except ImportError as e:
    GUI_AVAILABLE = False
    _import_error = str(e)
    
    class CoordinatePickerWorker:
        pass
    
    class CoordinatePickerDialog:
        pass
    
    class TaskEditDialog:
        pass
    
    class AutoTyperGUI:
        pass


def main():
    """Main entry point for the GUI application."""
    if not GUI_AVAILABLE:
        print(f"GUI not available: {_import_error}")
        print("Install PyQt6: pip install PyQt6")
        return 1
    
    app = QApplication(sys.argv)
    window = AutoTyperGUI()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())