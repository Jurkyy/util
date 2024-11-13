import sys
import json
import time
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QListWidget,
    QLabel,
    QStatusBar,
    QAction,
    QGroupBox,
    QRadioButton,
    QMessageBox,
    QDialog,
    QLineEdit,
    QCheckBox,
    QSpinBox,
    QDoubleSpinBox,
    QFrame,
    QToolTip,
    QMenu,
    QDialogButtonBox,
    QComboBox,
)
from PyQt5.QtCore import Qt, QRectF, QTimer, QThread, pyqtSignal, QPointF
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen
from pynput import mouse, keyboard
import os

# Import MacroRecorder from the local file
from macro_recorder import MacroRecorder


class TimelineWidget(QFrame):
    eventEdited = pyqtSignal(int, dict)  # Signal emitted when an event is edited
    eventRemoved = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(100)
        self.setFrameStyle(QFrame.Box | QFrame.Plain)
        self.setMouseTracking(True)  # Enable mouse tracking for hover effects

        self.events = []
        self.current_time = 0
        self.total_duration = 0
        self.margin = 20
        self.dragging = False
        self.dragged_event_index = None
        self.hovered_event_index = None
        self.tooltip = None

        # Colors
        self.colors = {
            "mouse": QColor(52, 152, 219),  # Blue
            "keyboard": QColor(46, 204, 113),  # Green
            "delay": QColor(149, 165, 166),  # Gray
            "timeline": QColor(189, 195, 199),  # Light gray
            "current_position": QColor(231, 76, 60),  # Red
            "hover": QColor(241, 196, 15),  # Yellow
        }

        # Context menu setup
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            event_index = self.get_event_at_position(event.pos())
            if event_index is not None:
                self.dragging = True
                self.dragged_event_index = event_index
                self.setCursor(Qt.SizeHorCursor)

    def mouseReleaseEvent(self, event):
        if self.dragging and self.dragged_event_index is not None:
            # Calculate new time based on x position
            width = self.width() - 2 * self.margin
            x = event.pos().x() - self.margin
            new_time = (x / width) * self.total_duration
            new_time = max(0, min(new_time, self.total_duration))

            # Update event timing
            event_data = self.events[self.dragged_event_index].copy()
            event_data["time"] = new_time
            self.eventEdited.emit(self.dragged_event_index, event_data)

        self.dragging = False
        self.dragged_event_index = None
        self.setCursor(Qt.ArrowCursor)
        self.update()

    def mouseMoveEvent(self, event):
        if self.dragging and self.dragged_event_index is not None:
            self.update()  # Redraw to show event at new position
        else:
            # Update hover state
            prev_hovered = self.hovered_event_index
            self.hovered_event_index = self.get_event_at_position(event.pos())
            if prev_hovered != self.hovered_event_index:
                self.update()

            # Show tooltip if hovering over an event
            if self.hovered_event_index is not None:
                event_data = self.events[self.hovered_event_index]
                tooltip_text = self.get_event_tooltip(event_data)
                QToolTip.showText(event.globalPos(), tooltip_text)
            else:
                QToolTip.hideText()

    def get_event_tooltip(self, event):
        """Generate tooltip text for an event"""
        if event["type"] == "mouse":
            return f"Mouse Click\nButton: {event['button']}\nPosition: ({event['x']}, {event['y']})\nTime: {event['time']:.2f}s"
        elif event["type"] == "keyboard":
            return f"Keyboard {event['action'].title()}\nKey: {event['key']}\nTime: {event['time']:.2f}s"
        else:  # delay
            return f"Delay\nDuration: {event['time']:.2f}s"

    def show_context_menu(self, position):
        event_index = self.get_event_at_position(position)
        if event_index is None:
            return

        event = self.events[event_index]
        menu = QMenu(self)

        # Add remove action first
        remove_action = QAction("Remove Event", self)
        remove_action.triggered.connect(lambda: self.remove_event(event_index))
        menu.addAction(remove_action)

        menu.addSeparator()  # Add separator between remove and edit options

        if event["type"] == "mouse":
            edit_pos_action = QAction("Edit Position", self)
            edit_pos_action.triggered.connect(
                lambda: self.edit_mouse_position(event_index)
            )
            menu.addAction(edit_pos_action)

        elif event["type"] == "keyboard":
            edit_key_action = QAction("Edit Key", self)
            edit_key_action.triggered.connect(lambda: self.edit_key(event_index))
            menu.addAction(edit_key_action)

        elif event["type"] == "delay":
            edit_delay_action = QAction("Edit Delay", self)
            edit_delay_action.triggered.connect(lambda: self.edit_delay(event_index))
            menu.addAction(edit_delay_action)

        edit_time_action = QAction("Edit Timing", self)
        edit_time_action.triggered.connect(lambda: self.edit_timing(event_index))
        menu.addAction(edit_time_action)

        menu.exec_(self.mapToGlobal(position))

    def remove_event(self, event_index):
        """Remove an event and emit signal"""
        if 0 <= event_index < len(self.events):
            self.eventRemoved.emit(event_index)

    def edit_mouse_position(self, event_index):
        event = self.events[event_index]
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Mouse Position")
        layout = QVBoxLayout()

        # X position
        x_layout = QHBoxLayout()
        x_layout.addWidget(QLabel("X:"))
        x_spin = QSpinBox()
        x_spin.setRange(0, 9999)
        x_spin.setValue(event["x"])
        x_layout.addWidget(x_spin)

        # Y position
        y_layout = QHBoxLayout()
        y_layout.addWidget(QLabel("Y:"))
        y_spin = QSpinBox()
        y_spin.setRange(0, 9999)
        y_spin.setValue(event["y"])
        y_layout.addWidget(y_spin)

        layout.addLayout(x_layout)
        layout.addLayout(y_layout)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, dialog
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        dialog.setLayout(layout)

        if dialog.exec_() == QDialog.Accepted:
            new_event = event.copy()
            new_event["x"] = x_spin.value()
            new_event["y"] = y_spin.value()
            self.eventEdited.emit(event_index, new_event)

    def edit_key(self, event_index):
        event = self.events[event_index]
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Key")
        layout = QVBoxLayout()

        # Key input
        key_layout = QHBoxLayout()
        key_layout.addWidget(QLabel("Key:"))
        key_input = QLineEdit(event["key"])
        key_layout.addWidget(key_input)

        layout.addLayout(key_layout)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, dialog
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        dialog.setLayout(layout)

        if dialog.exec_() == QDialog.Accepted:
            new_event = event.copy()
            new_event["key"] = key_input.text()
            self.eventEdited.emit(event_index, new_event)

    def edit_delay(self, event_index):
        event = self.events[event_index]
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Delay")
        layout = QVBoxLayout()

        # Delay input
        delay_layout = QHBoxLayout()
        delay_layout.addWidget(QLabel("Delay (seconds):"))
        delay_spin = QDoubleSpinBox()
        delay_spin.setRange(0, 60)
        delay_spin.setValue(event["time"])
        delay_spin.setDecimals(2)
        delay_layout.addWidget(delay_spin)

        layout.addLayout(delay_layout)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, dialog
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        dialog.setLayout(layout)

        if dialog.exec_() == QDialog.Accepted:
            new_event = event.copy()
            new_event["time"] = delay_spin.value()
            self.eventEdited.emit(event_index, new_event)

    def edit_timing(self, event_index):
        event = self.events[event_index]
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Timing")
        layout = QVBoxLayout()

        # Time input
        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("Time (seconds):"))
        time_spin = QDoubleSpinBox()
        time_spin.setRange(0, max(60, self.total_duration))
        time_spin.setValue(event["time"])
        time_spin.setDecimals(2)
        time_layout.addWidget(time_spin)

        layout.addLayout(time_layout)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, dialog
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        dialog.setLayout(layout)

        if dialog.exec_() == QDialog.Accepted:
            new_event = event.copy()
            new_event["time"] = time_spin.value()
            self.eventEdited.emit(event_index, new_event)

    def get_event_at_position(self, pos):
        """Return the index of the event at the given position, or None if none found"""
        if not self.events:
            return None

        width = self.width() - 2 * self.margin
        x = pos.x() - self.margin
        y = pos.y()
        timeline_y = self.height() - self.margin
        event_height = 20

        # Check each event
        for i, event in enumerate(self.events):
            event_x = width * (event["time"] / self.total_duration)
            event_y = timeline_y - event_height

            # Check if position is within event marker bounds
            if abs(x - event_x) < 5 and abs(y - event_y) < 10:
                return i

        return None

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self.events:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width() - 2 * self.margin
        height = self.height() - 2 * self.margin

        # Draw timeline
        painter.setPen(QPen(self.colors["timeline"], 2))
        timeline_y = self.height() - self.margin
        painter.drawLine(self.margin, timeline_y, width + self.margin, timeline_y)

        # Draw events with hover and drag effects
        event_height = 20
        for i, event in enumerate(self.events):
            # Calculate x position (adjusted if being dragged)
            if i == self.dragged_event_index and self.dragging:
                mouse_x = self.mapFromGlobal(self.cursor().pos()).x() - self.margin
                x = mouse_x
            else:
                x = self.margin + (width * (event["time"] / self.total_duration))

            y = timeline_y - event_height

            # Choose color based on hover/drag state
            if i == self.hovered_event_index or i == self.dragged_event_index:
                color = self.colors["hover"]
            else:
                color = self.colors[event["type"]]

            painter.setBrush(QBrush(color))
            painter.setPen(QPen(color.darker(120), 1))

            # Draw event marker
            if event["type"] == "mouse":
                painter.drawEllipse(QRectF(x - 4, y - 4, 8, 8))
            elif event["type"] == "keyboard":
                painter.drawRect(QRectF(x - 4, y - 4, 8, 8))
            elif event["type"] == "delay":
                points = [
                    QPointF(x - 4, y),
                    QPointF(x + 4, y - 4),
                    QPointF(x + 4, y + 4),
                ]
                painter.drawPolygon(points)

        # Draw current position marker
        if 0 <= self.current_time <= self.total_duration:
            x = self.margin + (width * (self.current_time / self.total_duration))
            painter.setPen(QPen(self.colors["current_position"], 2))
            painter.drawLine(int(x), self.margin, int(x), height + self.margin)

    def set_events(self, events):
        if not events:
            self.events = []
            self.total_duration = 0
        else:
            self.events = events
            self.total_duration = max(event["time"] for event in events)
        self.update()

    def set_current_time(self, time):
        self.current_time = time
        self.update()


class SaveMacroDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Save Macro")
        self.setModal(True)

        layout = QVBoxLayout()

        # Add filename input
        self.filename_input = QLineEdit()
        layout.addWidget(QLabel("Enter macro name:"))
        layout.addWidget(self.filename_input)

        # Add buttons
        buttons_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        cancel_button = QPushButton("Cancel")

        save_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)

        buttons_layout.addWidget(save_button)
        buttons_layout.addWidget(cancel_button)
        layout.addLayout(buttons_layout)

        self.setLayout(layout)

    def get_filename(self):
        return self.filename_input.text()


class PlaybackThread(QThread):
    finished = pyqtSignal()
    progress = pyqtSignal(float)  # New signal for current time

    def __init__(self, macro_recorder, macro_events, loop):
        super().__init__()
        self.macro_recorder = macro_recorder
        self.macro_events = macro_events
        self.loop = loop

        # Add progress tracking to the macro_recorder
        self.macro_recorder.on_event_executed = self.event_executed

    def event_executed(self, event_time):
        """Called by macro_recorder when an event is executed"""
        self.progress.emit(event_time)

    def run(self):
        self.macro_recorder.play_events(self.macro_events, self.loop)
        self.finished.emit()


class MacroRecorderGUI(QMainWindow):
    def __init__(self, macro_recorder):
        super().__init__()
        self.macro_recorder = macro_recorder
        self.macro_recorder.on_recording_stopped = self.handle_recording_stopped
        self.playback_thread = None
        self.current_macro_events = None  # Track current macro events
        self.current_macro_name = None  # Track current macro name
        self.init_ui()

        # Timer for updating status
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(100)  # Update every 100ms
        self.timeline.eventRemoved.connect(self.handle_event_removal)

        # Timer for recording timeline updates
        self.recording_timer = QTimer()
        self.recording_timer.timeout.connect(self.update_recording_timeline)
        self.recording_timer.setInterval(100)  # Update every 100ms
        self.has_unsaved_changes = False

        self.unsaved_macro_name = None  # Track the name of unsaved macro

    def update_recording_timeline(self):
        """Update the timeline with current recording events"""
        if self.macro_recorder.state == "recording":
            self.timeline.set_events(self.macro_recorder.events)
            self.timeline.set_current_time(time.time() - self.macro_recorder.start_time)

    def handle_recording_stopped(self):
        """Handle recording stopped event from any source"""
        self.recording_timer.stop()
        self.handle_unsaved_recording()  # Create the unsaved macro
        self.update_button_states()

    def handle_unsaved_recording(self):
        """Create a temporary file for the unsaved recording and add it to the list"""
        if self.macro_recorder.events:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            self.unsaved_macro_name = f"unsaved_{timestamp}.json"

            # Save to temporary file
            filepath = os.path.join(
                self.macro_recorder.MACRO_DIR, self.unsaved_macro_name
            )
            try:
                with open(filepath, "w") as file:
                    json.dump(self.macro_recorder.events, file, indent=4)

                # Refresh list and select the unsaved macro
                self.refresh_macro_list()
                items = self.macro_list.findItems(
                    self.unsaved_macro_name, Qt.MatchExactly
                )
                if items:
                    self.macro_list.setCurrentItem(items[0])

                self.status_bar.showMessage("Recording saved as temporary macro")
            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Failed to save temporary macro: {str(e)}"
                )

    def update_window_title(self):
        """Update window title to show save status"""
        base_title = "Macro Recorder"
        if self.has_unsaved_changes:
            self.setWindowTitle(f"{base_title} *")
        else:
            self.setWindowTitle(base_title)

    def mark_unsaved_changes(self):
        """Mark that there are unsaved changes"""
        self.has_unsaved_changes = True
        self.update_window_title()

    def clear_unsaved_changes(self):
        """Clear the unsaved changes flag"""
        self.has_unsaved_changes = False
        self.update_window_title()

    def handle_event_edit(self, event_index, new_event):
        """Handle edited events from the timeline widget"""
        if not self.current_macro_events or not self.current_macro_name:
            QMessageBox.warning(self, "Warning", "No macro is currently selected!")
            return

        # Update the event in memory
        self.current_macro_events[event_index] = new_event

        # Sort events by time to maintain chronological order
        self.current_macro_events.sort(key=lambda x: x["time"])

        # Save changes
        self.save_current_macro()

        # Update timeline display
        self.timeline.set_events(self.current_macro_events)
        self.status_bar.showMessage(f"Updated event in {self.current_macro_name}")

    def load_macro_for_editing(self, macro_name):
        """Load a macro into memory for editing"""
        macros = self.macro_recorder.load_all_macros()
        if macro_name in macros:
            self.current_macro_events = macros[macro_name]
            self.current_macro_name = macro_name
            self.timeline.set_events(self.current_macro_events)

            # Enable the timeline for editing
            self.timeline.setEnabled(True)
            self.status_bar.showMessage(f"Loaded {macro_name} for editing")
        else:
            self.current_macro_events = None
            self.current_macro_name = None
            self.timeline.set_events([])
            self.timeline.setEnabled(False)

    def play_macro(self, loop=False):
        selected_items = self.macro_list.selectedItems()
        if not selected_items:
            self.status_bar.showMessage("Please select a macro to play")
            return

        macro_name = selected_items[0].text()
        self.load_macro_for_editing(macro_name)  # Load the macro for potential editing

        if self.current_macro_events:
            # Initialize pause state and start playback
            current_time = time.time()
            self.macro_recorder.pause_state.update(
                {
                    "enabled": False,
                    "current_index": 0,
                    "macro_name": macro_name,
                    "selected_macro": self.current_macro_events,
                    "iteration": 1,
                    "loop": loop,
                    "total_start_time": current_time,
                    "iteration_start_time": current_time,
                    "last_event_time": current_time,
                }
            )
            self.macro_recorder.state = "playing"
            self.update_button_states()

            # Create and start playback thread
            self.playback_thread = PlaybackThread(
                self.macro_recorder, self.current_macro_events, loop
            )
            self.playback_thread.finished.connect(self.on_playback_finished)
            self.playback_thread.progress.connect(self.timeline.set_current_time)
            self.playback_thread.start()

    def on_playback_finished(self):
        self.macro_recorder.state = "idle"
        self.update_button_states()
        self.timeline.set_current_time(0)
        self.status_bar.showMessage("Ready")

    def stop_macro(self):
        if self.macro_recorder.state == "recording":
            self.macro_recorder.stop_recording()  # This will trigger the callback
        elif self.macro_recorder.state in ["playing", "paused"]:
            self.macro_recorder.stop_playing()
            if self.playback_thread and self.playback_thread.isRunning():
                self.playback_thread.wait()
        self.update_button_states()

    def closeEvent(self, event):
        """Handle cleanup when the window is closed"""
        if self.cleanup_unsaved_cb.isChecked():
            self.cleanup_unsaved_macros()
        self.macro_recorder.stop_playing()
        if self.playback_thread and self.playback_thread.isRunning():
            self.playback_thread.wait()
        event.accept()

    def init_ui(self):
        self.setWindowTitle("Macro Recorder")
        self.setGeometry(100, 100, 800, 600)

        # Create a vertical layout for the entire window
        main_layout = QVBoxLayout()

        # Create and add the top panel (existing panels)
        top_panel = QWidget()
        top_layout = QHBoxLayout(top_panel)

        # Set up timeline
        timeline_panel = QGroupBox("Playback Timeline")
        timeline_layout = QVBoxLayout()

        # Add timeline widget with enhanced tooltip support
        self.timeline = TimelineWidget()
        self.timeline.eventEdited.connect(self.handle_event_edit)
        self.timeline.setEnabled(False)  # Disabled until a macro is loaded
        timeline_layout.addWidget(self.timeline)

        # Add legend
        legend_layout = QHBoxLayout()
        for event_type, color in self.timeline.colors.items():
            if event_type != "timeline" and event_type != "current_position":
                label = QLabel(f"● {event_type.capitalize()}")
                label.setStyleSheet(f"color: {color.name()}")
                legend_layout.addWidget(label)
        timeline_layout.addLayout(legend_layout)

        timeline_panel.setLayout(timeline_layout)

        # Add panels to main layout
        main_layout.addWidget(top_panel, 2)
        main_layout.addWidget(timeline_panel, 1)

        # Set the central widget's layout
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # Left panel - Macro List
        left_panel = QGroupBox("Saved Macros")
        left_layout = QVBoxLayout()

        self.macro_list = QListWidget()
        self.refresh_macro_list()

        left_layout.addWidget(self.macro_list)
        left_panel.setLayout(left_layout)

        # Center panel - Controls
        center_panel = QGroupBox("Controls")
        center_layout = QVBoxLayout()

        # Center panel - Controls
        center_panel = QGroupBox("Controls")
        center_layout = QVBoxLayout()

        # Create a widget for main controls
        main_controls = QWidget()
        main_controls_layout = QVBoxLayout(main_controls)

        # Control buttons with hotkey information
        self.record_button = QPushButton("Record (ESC to stop)")
        self.play_button = QPushButton("Play Once")
        self.play_loop_button = QPushButton("Play Loop")
        self.pause_button = QPushButton("Pause (SPACE)")
        self.stop_button = QPushButton("Stop (ESC)")

        # Add buttons to main controls layout
        main_controls_layout.addWidget(self.record_button)
        main_controls_layout.addWidget(self.play_button)
        main_controls_layout.addWidget(self.play_loop_button)
        main_controls_layout.addWidget(self.pause_button)
        main_controls_layout.addWidget(self.stop_button)
        main_controls_layout.addStretch()

        # Add event creation buttons
        event_creation_group = QGroupBox("Add Events")
        event_creation_layout = QVBoxLayout()

        self.add_mouse_button = QPushButton("Add Mouse Click")
        self.add_keyboard_button = QPushButton("Add Keyboard Event")

        event_creation_layout.addWidget(self.add_mouse_button)
        event_creation_layout.addWidget(self.add_keyboard_button)
        event_creation_group.setLayout(event_creation_layout)

        # Delete button with red background
        self.delete_button = QPushButton("Delete Selected")
        self.delete_button.setStyleSheet("background-color: #ffcccc;")

        # Add all components to center layout with spacing
        center_layout.addWidget(main_controls)
        center_layout.addWidget(event_creation_group)
        center_layout.addStretch()  # This pushes the delete button to the bottom
        center_layout.addWidget(self.delete_button)

        center_panel.setLayout(center_layout)

        # Connect buttons
        self.delete_button.clicked.connect(self.delete_selected_macro)
        self.record_button.clicked.connect(self.start_recording)
        self.play_button.clicked.connect(lambda: self.play_macro(loop=False))
        self.play_loop_button.clicked.connect(lambda: self.play_macro(loop=True))
        self.pause_button.clicked.connect(self.toggle_pause)
        self.stop_button.clicked.connect(self.stop_macro)
        self.add_mouse_button.clicked.connect(self.add_mouse_event)
        self.add_keyboard_button.clicked.connect(self.add_keyboard_event)

        # Right panel - Settings
        right_panel = QGroupBox("Settings")
        right_layout = QVBoxLayout()

        # Randomization settings group
        rand_group = QGroupBox("Randomization")
        rand_layout = QVBoxLayout()

        # Enable/Disable randomization
        self.rand_enabled_cb = QCheckBox("Enable Randomization")
        self.rand_enabled_cb.setChecked(self.macro_recorder.randomization["enabled"])
        self.rand_enabled_cb.stateChanged.connect(self.update_randomization)

        # Position jitter
        jitter_layout = QHBoxLayout()
        jitter_layout.addWidget(QLabel("Position Jitter (px):"))
        self.position_jitter = QSpinBox()
        self.position_jitter.setRange(0, 50)
        self.position_jitter.setValue(
            self.macro_recorder.randomization["position_jitter"]
        )
        self.position_jitter.valueChanged.connect(self.update_randomization)
        jitter_layout.addWidget(self.position_jitter)

        # Time jitter
        time_jitter_layout = QHBoxLayout()
        time_jitter_layout.addWidget(QLabel("Time Jitter (%):"))
        self.time_jitter = QSpinBox()
        self.time_jitter.setRange(0, 100)
        self.time_jitter.setValue(
            self.macro_recorder.randomization["time_jitter_percent"]
        )
        self.time_jitter.valueChanged.connect(self.update_randomization)
        time_jitter_layout.addWidget(self.time_jitter)

        # Max extra delay
        delay_layout = QHBoxLayout()
        delay_layout.addWidget(QLabel("Max Extra Delay (s):"))
        self.max_delay = QDoubleSpinBox()
        self.max_delay.setRange(0, 5)
        self.max_delay.setSingleStep(0.1)
        self.max_delay.setValue(self.macro_recorder.randomization["max_extra_delay"])
        self.max_delay.valueChanged.connect(self.update_randomization)
        delay_layout.addWidget(self.max_delay)

        # Add all randomization widgets to the group
        rand_layout.addWidget(self.rand_enabled_cb)
        rand_layout.addLayout(jitter_layout)
        rand_layout.addLayout(time_jitter_layout)
        rand_layout.addLayout(delay_layout)
        rand_group.setLayout(rand_layout)

        # Mouse movement settings group (existing code)
        mouse_group = QGroupBox("Mouse Movement")
        mouse_layout = QVBoxLayout()

        # Enable/Disable smooth mouse
        self.smooth_enabled_cb = QCheckBox("Enable Smooth Movement")
        self.smooth_enabled_cb.setChecked(self.macro_recorder.smooth_mouse["enabled"])
        self.smooth_enabled_cb.stateChanged.connect(self.update_mouse_settings)

        # Steps for smooth movement
        steps_layout = QHBoxLayout()
        steps_layout.addWidget(QLabel("Movement Steps:"))
        self.movement_steps = QSpinBox()
        self.movement_steps.setRange(10, 200)
        self.movement_steps.setValue(self.macro_recorder.smooth_mouse["steps"])
        self.movement_steps.valueChanged.connect(self.update_mouse_settings)
        steps_layout.addWidget(self.movement_steps)

        mouse_layout.addWidget(self.smooth_enabled_cb)
        mouse_layout.addLayout(steps_layout)
        mouse_group.setLayout(mouse_layout)

        # Cleanup settings group (existing code)
        cleanup_group = QGroupBox("Cleanup Settings")
        cleanup_layout = QVBoxLayout()
        self.cleanup_unsaved_cb = QCheckBox("Remove unsaved macros on exit")
        self.cleanup_unsaved_cb.setChecked(True)
        cleanup_layout.addWidget(self.cleanup_unsaved_cb)
        cleanup_group.setLayout(cleanup_layout)

        # Add all groups to the right panel
        right_layout.addWidget(rand_group)
        right_layout.addWidget(mouse_group)
        right_layout.addWidget(cleanup_group)
        right_layout.addStretch()

        right_panel.setLayout(right_layout)
        # Add existing panels to top layout
        top_layout.addWidget(left_panel, 1)
        top_layout.addWidget(center_panel, 2)
        top_layout.addWidget(right_panel, 1)

        self.macro_list.itemSelectionChanged.connect(self.handle_macro_selection)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

        # Menu bar
        self.create_menu_bar()

        self.show()

    def append_macro(self):
        """Append another macro to the currently selected macro"""
        # Check if a macro is selected
        selected_items = self.macro_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Warning", "Please select a macro to append to!")
            return

        target_macro_name = selected_items[0].text()

        # Create dialog for selecting macro to append
        dialog = QDialog(self)
        dialog.setWindowTitle("Append Macro")
        layout = QVBoxLayout()

        # Add explanation label
        layout.addWidget(QLabel(f"Select macro to append to '{target_macro_name}':"))

        # Create list widget for macro selection
        macro_list = QListWidget()
        macros = self.macro_recorder.load_all_macros()

        # Add all macros except the target macro
        for macro_name in macros.keys():
            if macro_name != target_macro_name:  # Don't include the target macro
                macro_list.addItem(macro_name)

        layout.addWidget(macro_list)

        # Add timing adjustment option
        timing_group = QGroupBox("Timing Adjustment")
        timing_layout = QVBoxLayout()

        # Radio buttons for timing options
        self.relative_timing = QRadioButton("Relative timing (maintain delays)")
        self.absolute_timing = QRadioButton(
            "Absolute timing (keep original timestamps)"
        )
        self.relative_timing.setChecked(True)  # Default to relative timing

        timing_layout.addWidget(self.relative_timing)
        timing_layout.addWidget(self.absolute_timing)

        # Add gap option
        gap_layout = QHBoxLayout()
        gap_layout.addWidget(QLabel("Gap between macros (seconds):"))
        gap_spin = QDoubleSpinBox()
        gap_spin.setRange(0, 10)
        gap_spin.setValue(0.5)
        gap_spin.setSingleStep(0.1)
        gap_layout.addWidget(gap_spin)
        timing_layout.addLayout(gap_layout)

        timing_group.setLayout(timing_layout)
        layout.addWidget(timing_group)

        # Add dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        dialog.setLayout(layout)

        # Show dialog and process result
        if dialog.exec_() == QDialog.Accepted and macro_list.currentItem():
            source_macro_name = macro_list.currentItem().text()

            try:
                # Get both macros' events
                target_events = self.current_macro_events.copy()
                source_events = macros[source_macro_name].copy()

                if not source_events:
                    raise ValueError("Source macro is empty")

                # Calculate base time for appending
                if target_events:
                    last_target_time = max(event["time"] for event in target_events)
                else:
                    last_target_time = 0

                # Add the specified gap
                base_time = last_target_time + gap_spin.value()

                # Adjust timing of source events
                if self.relative_timing.isChecked():
                    # Find the first event time in source macro
                    first_source_time = min(event["time"] for event in source_events)

                    # Adjust all events to maintain relative timing
                    for event in source_events:
                        event["time"] = base_time + (event["time"] - first_source_time)
                else:  # Absolute timing
                    # Simply add the base_time to all events
                    for event in source_events:
                        event["time"] += base_time

                # Combine events
                merged_events = target_events + source_events
                merged_events.sort(key=lambda x: x["time"])

                # Update the current macro
                self.current_macro_events = merged_events
                self.save_current_macro()

                # Update timeline
                self.timeline.set_events(merged_events)

                QMessageBox.information(
                    self,
                    "Success",
                    f"Successfully appended {source_macro_name} to {target_macro_name}",
                )

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to append macro: {str(e)}")

    def delete_selected_macro(self):
        """Delete the currently selected macro"""
        if not self.macro_list.selectedItems():
            QMessageBox.warning(self, "Warning", "No macro selected to delete!")
            return

        macro_name = self.macro_list.selectedItems()[0].text()

        # Confirm deletion
        msg = "Are you sure you want to delete this macro?"
        if macro_name.startswith("unsaved_"):
            msg = "Are you sure you want to delete this unsaved macro?"

        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            msg,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            try:
                filepath = os.path.join(self.macro_recorder.MACRO_DIR, macro_name)
                os.remove(filepath)
                self.refresh_macro_list()
                self.timeline.set_events([])  # Clear timeline
                self.status_bar.showMessage(f"Deleted macro: {macro_name}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete macro: {str(e)}")

    def cleanup_unsaved_macros(self):
        """Remove all unsaved macros from the directory"""
        try:
            for filename in os.listdir(self.macro_recorder.MACRO_DIR):
                if filename.startswith("unsaved_") and filename.endswith(".json"):
                    filepath = os.path.join(self.macro_recorder.MACRO_DIR, filename)
                    try:
                        os.remove(filepath)
                    except:
                        continue  # Skip if file can't be deleted
        except Exception as e:
            print(f"Error during cleanup: {str(e)}")

    def handle_event_removal(self, event_index):
        """Handle removal of an event from the timeline"""
        if not self.current_macro_events or not self.current_macro_name:
            return

        # Remove the event
        if 0 <= event_index < len(self.current_macro_events):
            del self.current_macro_events[event_index]

            # Save changes
            self.save_current_macro()

            # Update timeline display
            self.timeline.set_events(self.current_macro_events)
            self.status_bar.showMessage(f"Removed event from {self.current_macro_name}")

    def handle_macro_selection(self):
        """Load the timeline when a macro is selected"""
        selected_items = self.macro_list.selectedItems()
        if selected_items:
            macro_name = selected_items[0].text()
            self.load_macro_for_editing(macro_name)

    def update_button_states(self):
        """Update button states based on current recorder state"""
        is_recording = self.macro_recorder.state == "recording"
        is_playing = self.macro_recorder.state == "playing"
        is_paused = self.macro_recorder.state == "paused"

        # Recording button
        self.record_button.setEnabled(not (is_recording or is_playing or is_paused))

        # Playback buttons
        self.play_button.setEnabled(not (is_recording or is_playing or is_paused))
        self.play_loop_button.setEnabled(not (is_recording or is_playing or is_paused))

        # Pause button
        self.pause_button.setEnabled(is_playing or is_paused)
        if is_paused:
            self.pause_button.setText("Resume (SPACE)")
        else:
            self.pause_button.setText("Pause (SPACE)")

        # Stop button
        self.stop_button.setEnabled(is_recording or is_playing or is_paused)

    def toggle_pause(self):
        """Toggle between pause and resume"""
        if self.macro_recorder.state == "playing":
            self.macro_recorder.pause_playback()
        elif self.macro_recorder.state == "paused":
            self.macro_recorder.resume_playback()
        self.update_button_states()

    def update_randomization(self):
        """Update randomization settings when changed in GUI"""
        self.macro_recorder.randomization.update(
            {
                "enabled": self.rand_enabled_cb.isChecked(),
                "position_jitter": self.position_jitter.value(),
                "time_jitter_percent": self.time_jitter.value(),
                "max_extra_delay": self.max_delay.value(),
            }
        )

    def update_mouse_settings(self):
        """Update mouse movement settings when changed in GUI"""
        self.macro_recorder.smooth_mouse.update(
            {
                "enabled": self.smooth_enabled_cb.isChecked(),
                "steps": self.movement_steps.value(),
            }
        )

    def update_status(self):
        """Simplified update_status since timeline updates come from progress signal"""
        state = self.macro_recorder.state
        if state == "recording":
            elapsed = time.time() - self.macro_recorder.start_time
            self.status_bar.showMessage(f"Recording... ({elapsed:.1f}s)")
        elif state == "playing":
            self.status_bar.showMessage("Playing macro...")
        elif state == "paused":
            self.status_bar.showMessage("Paused")
        elif state == "idle":
            self.status_bar.showMessage("Ready")
        self.update_button_states()

    def create_menu_bar(self):
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")
        save_action = QAction("Save Macro", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_macro)
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(save_action)
        file_menu.addAction(exit_action)

        # Edit menu
        edit_menu = menubar.addMenu("Edit")
        normalize_action = QAction("Normalize Timing", self)
        normalize_action.triggered.connect(self.normalize_macro_timing)
        append_action = QAction("Append Macro", self)
        append_action.triggered.connect(self.append_macro)

        edit_menu.addAction(normalize_action)
        edit_menu.addAction(append_action)

    def normalize_macro_timing(self):
        """Normalize the timing of the current macro"""
        if not self.current_macro_events:
            QMessageBox.warning(self, "Warning", "No macro is currently loaded!")
            return

        self.current_macro_events = self.macro_recorder.normalize_macro(
            self.current_macro_events
        )
        self.save_current_macro()
        self.timeline.set_events(self.current_macro_events)
        self.status_bar.showMessage("Macro timing normalized")

    def refresh_macro_list(self):
        """Refresh the macro list and maintain selection"""
        current_selection = None
        if self.macro_list.selectedItems():
            current_selection = self.macro_list.selectedItems()[0].text()

        self.macro_list.clear()

        # Get all macro files
        macro_files = []
        for filename in os.listdir(self.macro_recorder.MACRO_DIR):
            if filename.endswith(".json"):
                macro_files.append(filename)

        # Sort unsaved macros to the top
        macro_files.sort(key=lambda x: (not x.startswith("unsaved_"), x))

        # Add to list widget
        for filename in macro_files:
            item = self.macro_list.addItem(filename)

            # Style unsaved macros differently
            if filename.startswith("unsaved_"):
                self.macro_list.item(self.macro_list.count() - 1).setForeground(
                    Qt.darkGray
                )

        # Restore previous selection if it still exists
        if current_selection:
            items = self.macro_list.findItems(current_selection, Qt.MatchExactly)
            if items:
                self.macro_list.setCurrentItem(items[0])

    def save_current_macro(self):
        """Save the currently loaded macro to disk with error handling"""
        if not self.current_macro_name or not self.current_macro_events:
            return

        filepath = os.path.join(self.macro_recorder.MACRO_DIR, self.current_macro_name)
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            # Save the file
            with open(filepath, "w") as file:
                json.dump(self.current_macro_events, file, indent=4)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save macro: {str(e)}")
            return False
        return True

    def start_recording(self):
        self.macro_recorder.start_recording()
        self.timeline.setEnabled(True)
        self.recording_timer.start()
        self.update_button_states()
        self.status_bar.showMessage("Recording...")

    def save_macro(self):
        """Save the macro with a permanent name"""
        # Determine which macro to save
        if self.macro_list.selectedItems():
            current_macro = self.macro_list.selectedItems()[0].text()
            is_unsaved = current_macro.startswith("unsaved_")
        else:
            QMessageBox.warning(self, "Warning", "No macro selected to save!")
            return

        dialog = SaveMacroDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            filename = dialog.get_filename()
            if filename:
                # Add .json extension if not present
                if not filename.endswith(".json"):
                    filename += ".json"

                # Load the current macro data
                current_filepath = os.path.join(
                    self.macro_recorder.MACRO_DIR, current_macro
                )
                try:
                    with open(current_filepath, "r") as file:
                        macro_data = json.load(file)

                    # Save with new name
                    new_filepath = os.path.join(self.macro_recorder.MACRO_DIR, filename)
                    with open(new_filepath, "w") as file:
                        json.dump(macro_data, file, indent=4)

                    # If saving an unsaved macro, remove the temporary file
                    if is_unsaved:
                        try:
                            os.remove(current_filepath)
                        except:
                            pass  # Ignore deletion errors

                    self.refresh_macro_list()

                    # Select the newly saved macro
                    items = self.macro_list.findItems(filename, Qt.MatchExactly)
                    if items:
                        self.macro_list.setCurrentItem(items[0])

                    self.status_bar.showMessage(f"Macro saved as {filename}")
                except Exception as e:
                    QMessageBox.critical(
                        self, "Error", f"Failed to save macro: {str(e)}"
                    )
            else:
                QMessageBox.warning(self, "Warning", "Please enter a valid filename!")

    def add_mouse_event(self):
        """Add a new mouse click event to the timeline"""
        if not self.current_macro_events:
            QMessageBox.warning(
                self, "Warning", "Please select or create a macro first!"
            )
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Add Mouse Click")
        layout = QVBoxLayout()

        # Time input
        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("Time (seconds):"))
        time_spin = QDoubleSpinBox()
        time_spin.setRange(0, max(60, self.timeline.total_duration))
        time_spin.setValue(0)
        time_spin.setDecimals(2)
        time_layout.addWidget(time_spin)

        # Position inputs
        pos_layout = QHBoxLayout()
        pos_layout.addWidget(QLabel("Position:"))
        x_spin = QSpinBox()
        x_spin.setRange(0, 9999)
        y_spin = QSpinBox()
        y_spin.setRange(0, 9999)
        pos_layout.addWidget(QLabel("X:"))
        pos_layout.addWidget(x_spin)
        pos_layout.addWidget(QLabel("Y:"))
        pos_layout.addWidget(y_spin)

        # Button selection
        button_layout = QHBoxLayout()
        button_layout.addWidget(QLabel("Button:"))
        button_combo = QComboBox()
        button_combo.addItems(["left", "right", "middle"])
        button_layout.addWidget(button_combo)

        # Add all layouts
        layout.addLayout(time_layout)
        layout.addLayout(pos_layout)
        layout.addLayout(button_layout)

        # Dialog buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, dialog
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        dialog.setLayout(layout)

        if dialog.exec_() == QDialog.Accepted:
            new_event = {
                "type": "mouse",
                "time": time_spin.value(),
                "x": x_spin.value(),
                "y": y_spin.value(),
                "button": button_combo.currentText(),
                "action": "pressed",  # Default to pressed action
            }

            # Add event and sort by time
            self.current_macro_events.append(new_event)
            self.current_macro_events.sort(key=lambda x: x["time"])

            # Update timeline
            self.timeline.set_events(self.current_macro_events)
            self.save_current_macro()

    def add_keyboard_event(self):
        """Add a new keyboard event to the timeline"""
        if not self.current_macro_events:
            QMessageBox.warning(
                self, "Warning", "Please select or create a macro first!"
            )
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Add Keyboard Event")
        layout = QVBoxLayout()

        # Time input
        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("Time (seconds):"))
        time_spin = QDoubleSpinBox()
        time_spin.setRange(0, max(60, self.timeline.total_duration))
        time_spin.setValue(0)
        time_spin.setDecimals(2)
        time_layout.addWidget(time_spin)

        # Key input
        key_layout = QHBoxLayout()
        key_layout.addWidget(QLabel("Key:"))
        key_input = QLineEdit()
        key_layout.addWidget(key_input)

        # Action selection
        action_layout = QHBoxLayout()
        action_layout.addWidget(QLabel("Action:"))
        action_combo = QComboBox()
        action_combo.addItems(["pressed", "released"])
        action_layout.addWidget(action_combo)

        # Add all layouts
        layout.addLayout(time_layout)
        layout.addLayout(key_layout)
        layout.addLayout(action_layout)

        # Dialog buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, dialog
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        dialog.setLayout(layout)

        if dialog.exec_() == QDialog.Accepted:
            new_event = {
                "type": "keyboard",
                "time": time_spin.value(),
                "key": key_input.text(),
                "action": action_combo.currentText(),
            }

            # Add event and sort by time
            self.current_macro_events.append(new_event)
            self.current_macro_events.sort(key=lambda x: x["time"])

            # Update timeline
            self.timeline.set_events(self.current_macro_events)
            self.save_current_macro()


def main():
    app = QApplication(sys.argv)

    # Create the macro recorder instance
    recorder = MacroRecorder()

    # Create and show the GUI
    gui = MacroRecorderGUI(recorder)
    gui.show()

    # Start listeners
    mouse_listener = mouse.Listener(on_click=recorder.record_click)
    mouse_listener.start()

    key_listener = keyboard.Listener(
        on_press=recorder.on_press, on_release=recorder.on_release
    )
    key_listener.start()

    # Start the application event loop
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
