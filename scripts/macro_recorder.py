from pynput import mouse, keyboard
from pynput.mouse import Button, Controller as MouseController
from pynput.keyboard import Key, Controller as KeyboardController
import time
import json
import os
import random


class MacroRecorder:
    def __init__(self):
        # Variables to store recorded events and timings
        self.events = []
        self.state = "idle"  # Can be "idle", "recording", or "playing"
        self.start_time = None
        self.last_recorded_time = None
        self.on_event_executed = None
        self.on_recording_stopped = None

        self.smooth_mouse = {
            "enabled": True,
            "steps": 100,  # Number of steps for smooth movement
            "delay": 0.001,  # Delay between steps in seconds
        }

        # Randomization settings
        self.randomization = {
            "enabled": True,
            "position_jitter": 5,  # pixels
            "time_jitter_percent": 8,  # percentage of original delay
            "max_extra_delay": 0.5,  # maximum additional random delay
        }

        self.pause_state = {
            "enabled": False,
            "current_index": 0,
            "macro_name": None,
            "selected_macro": None,
            "iteration": 1,
            "loop": False,
            "total_start_time": None,
            "last_event_time": None,  # Add this to track timing
            "iteration_start_time": None,  # Add this to track iteration timing
        }

        # Controllers
        self.mouse_controller = MouseController()
        self.keyboard_controller = KeyboardController()

        # Directory for macros
        self.MACRO_DIR = "macros"
        os.makedirs(self.MACRO_DIR, exist_ok=True)

        # Special keys mapping
        self.special_keys = {
            Key.enter: "enter",
            Key.space: "space",
            Key.backspace: "backspace",
            Key.delete: "delete",
            Key.tab: "tab",
            Key.shift: "shift",
            Key.ctrl: "ctrl",
            Key.alt: "alt",
            Key.caps_lock: "caps_lock",
            Key.esc: "esc",
            Key.up: "up",
            Key.down: "down",
            Key.left: "left",
            Key.right: "right",
        }
        self.special_keys_reverse = {v: k for k, v in self.special_keys.items()}

    def normalize_macro(self, events):
        """
        Normalize a macro so that the first action starts at time 0
        and all subsequent times are adjusted accordingly
        """
        if not events:
            return events

        # Find the time of the first action
        first_time = events[0]["time"]

        # Adjust all times by subtracting the first action time
        normalized_events = []
        for event in events:
            normalized_event = event.copy()
            normalized_event["time"] = event["time"] - first_time
            normalized_events.append(normalized_event)

        return normalized_events

    def validate_event(self, event):
        """
        Validate an event's structure and data
        """
        required_fields = {
            "mouse": ["type", "action", "x", "y", "button", "time"],
            "keyboard": ["type", "action", "key", "is_special", "time"],
            "delay": ["type", "time"],
        }

        if "type" not in event:
            return False

        event_type = event["type"]
        if event_type not in required_fields:
            return False

        return all(field in event for field in required_fields[event_type])

    def sort_events_by_time(self, events):
        """
        Sort events by their timestamp
        """
        return sorted(events, key=lambda x: x["time"])

    def edit_macro(self, macros):
        """Allow user to edit existing macros"""
        if not macros:
            print("No macros available!")
            return

        print("\nAvailable Macros:")
        for idx, macro_name in enumerate(macros.keys(), 1):
            print(f"{idx}. {macro_name}")

        choice = input("Enter the number of the macro to edit: ").strip()
        try:
            choice_idx = int(choice) - 1
            macro_name = list(macros.keys())[choice_idx]
            selected_macro = macros[macro_name]

            print("\nEdit Options:")
            print("1. Normalize timing (adjust all times so first action starts at 0)")
            print("2. Back to main menu")

            edit_choice = input("Enter your choice: ").strip()

            if edit_choice == "1":
                normalized_macro = self.normalize_macro(selected_macro)
                # Save the normalized macro
                filepath = os.path.join(self.MACRO_DIR, macro_name)
                with open(filepath, "w") as file:
                    json.dump(normalized_macro, file, indent=4)
                print(f"Macro normalized and saved to {filepath}")

        except (IndexError, ValueError):
            print("Invalid choice.")

    def configure_randomization(self):
        """Allow user to configure randomization settings"""
        print("\nRandomization Settings:")
        print(
            f"1. Enable/Disable (Currently: {'Enabled' if self.randomization['enabled'] else 'Disabled'})"
        )
        print(
            f"2. Position Jitter (Currently: ±{self.randomization['position_jitter']} pixels)"
        )
        print(
            f"3. Time Jitter (Currently: ±{self.randomization['time_jitter_percent']}%)"
        )
        print(
            f"4. Max Extra Delay (Currently: {self.randomization['max_extra_delay']}s)"
        )
        print(
            f"5. Smooth Mouse Movement (Currently: {'Enabled' if self.smooth_mouse['enabled'] else 'Disabled'})"
        )
        print(f"6. Mouse Movement Steps (Currently: {self.smooth_mouse['steps']})")
        print("7. Back to Main Menu")

        choice = input("Enter your choice: ").strip()

        if choice == "1":
            self.randomization["enabled"] = not self.randomization["enabled"]
            print(
                f"Randomization {'enabled' if self.randomization['enabled'] else 'disabled'}"
            )
        elif choice == "2":
            try:
                pixels = int(input("Enter maximum position jitter in pixels: "))
                if pixels >= 0:
                    self.randomization["position_jitter"] = pixels
            except ValueError:
                print("Invalid input. Please enter a number.")
        elif choice == "3":
            try:
                percent = float(input("Enter time jitter percentage (0-100): "))
                if 0 <= percent <= 100:
                    self.randomization["time_jitter_percent"] = percent
            except ValueError:
                print("Invalid input. Please enter a number.")
        elif choice == "4":
            try:
                delay = float(input("Enter maximum extra delay in seconds: "))
                if delay >= 0:
                    self.randomization["max_extra_delay"] = delay
            except ValueError:
                print("Invalid input. Please enter a number.")
        elif choice == "5":
            self.smooth_mouse["enabled"] = not self.smooth_mouse["enabled"]
            print(
                f"Smooth mouse movement {'enabled' if self.smooth_mouse['enabled'] else 'disabled'}"
            )
        elif choice == "6":
            try:
                steps = int(input("Enter number of steps for mouse movement (10-50): "))
                if 10 <= steps <= 50:
                    self.smooth_mouse["steps"] = steps
                else:
                    print("Steps must be between 10 and 50.")
            except ValueError:
                print("Invalid input. Please enter a number.")

    def move_mouse_smoothly(self, start_x, start_y, end_x, end_y):
        """Move mouse smoothly from start position to end position"""
        if not self.smooth_mouse["enabled"]:
            return

        steps = self.smooth_mouse["steps"]
        for i in range(steps + 1):
            t = i / steps
            current_x = int(start_x + (end_x - start_x) * t)
            current_y = int(start_y + (end_y - start_y) * t)
            self.mouse_controller.position = (current_x, current_y)
            time.sleep(self.smooth_mouse["delay"])

    def apply_position_jitter(self, x, y):
        """Apply random jitter to mouse position"""
        if not self.randomization["enabled"]:
            return x, y

        jitter = self.randomization["position_jitter"]
        jitter_x = random.uniform(-jitter, jitter)
        jitter_y = random.uniform(-jitter, jitter)
        return int(x + jitter_x), int(y + jitter_y)

    def apply_time_jitter(self, delay):
        """Apply random jitter to timing"""
        if not self.randomization["enabled"]:
            return delay

        jitter_range = delay * (self.randomization["time_jitter_percent"] / 100)
        jittered_delay = max(
            0, delay + random.uniform(-jitter_range, jitter_range) + (jitter_range / 10)
        )

        max_extra_delay = self.randomization["max_extra_delay"]

        return max(delay, min(max_extra_delay, jittered_delay))

    def load_all_macros(self):
        """Load all macros with improved error handling"""
        macros = {}
        try:
            for file in os.listdir(self.MACRO_DIR):
                if file.endswith(".json"):
                    filepath = os.path.join(self.MACRO_DIR, file)
                    try:
                        if os.path.getsize(filepath) > 0:  # Check if file is not empty
                            with open(filepath, "r") as f:
                                macro_data = json.load(f)
                                if isinstance(
                                    macro_data, list
                                ):  # Validate macro structure
                                    macros[file] = macro_data
                    except json.JSONDecodeError as e:
                        print(f"Error loading macro {file}: {e}")
                    except Exception as e:
                        print(f"Unexpected error loading macro {file}: {e}")
        except Exception as e:
            print(f"Error accessing macro directory: {e}")
        return macros

    def save_macro(self, filename):
        if self.events and self.state == "recording":
            self.add_final_timing()

        filepath = os.path.join(self.MACRO_DIR, filename)
        try:
            with open(filepath, "w") as file:
                json.dump(self.events, file, indent=4)
            print(f"Macro saved to {filepath}")
        except Exception as e:
            print(f"Error saving macro: {e}")

    def record_click(self, x, y, button, pressed):
        if self.state == "recording" and pressed:
            current_time = time.time()
            time_elapsed = current_time - self.start_time

            self.events.append(
                {
                    "type": "mouse",
                    "action": "click",
                    "x": x,
                    "y": y,
                    "button": button.name,
                    "time": time_elapsed,
                }
            )
            self.last_recorded_time = current_time
            print(
                f"Recorded mouse: {button.name} at ({x}, {y}) after {time_elapsed:.2f}s"
            )

    def record_key(self, key, pressed):
        if self.state != "recording":
            return

        if not isinstance(key, keyboard.Key) or (
            isinstance(key, keyboard.Key) and key != Key.esc
        ):
            current_time = time.time()
            time_elapsed = current_time - self.start_time

            # Ignore enter key release events in first second
            if (
                not pressed
                and isinstance(key, keyboard.Key)
                and key == Key.enter
                and time_elapsed < 0.5
            ):
                return

            if isinstance(key, keyboard.Key):
                key_name = self.special_keys.get(key, str(key))
                is_special = True
            else:
                try:
                    key_name = key.char
                    is_special = False
                except AttributeError:
                    return

            self.events.append(
                {
                    "type": "keyboard",
                    "action": "press" if pressed else "release",
                    "key": key_name,
                    "is_special": is_special,
                    "time": time_elapsed,
                }
            )
            self.last_recorded_time = current_time
            print(
                f"Recorded keyboard: {key_name} {'pressed' if pressed else 'released'} after {time_elapsed:.2f}s"
            )

    def add_final_timing(self):
        if self.last_recorded_time and self.start_time:
            final_time = time.time()
            total_duration = final_time - self.start_time
            if not self.events or total_duration - self.events[-1]["time"] > 0.1:
                self.events.append({"type": "delay", "time": total_duration})
                print(f"Added final timing: {total_duration:.2f}s")

    def play_macro(self, macros, loop=False):
        if not macros:
            print("No macros available!")
            return

        # If we're resuming from a pause, use the stored macro
        if self.pause_state["enabled"] and self.state == "paused":
            self.state = "playing"
            print("\nResuming macro playback...")
            return  # Let the existing play_events continue

        print("\nAvailable Macros:")
        for idx, macro_name in enumerate(macros.keys(), 1):
            print(f"{idx}. {macro_name}")
        choice = input("Enter the number of the macro to play: ").strip()
        try:
            choice_idx = int(choice) - 1
            macro_name = list(macros.keys())[choice_idx]
            selected_macro = macros[macro_name]

            # Initialize pause state
            self.state = "playing"
            current_time = time.time()
            self.pause_state.update(
                {
                    "enabled": False,  # Will be set to True when paused
                    "current_index": 0,
                    "macro_name": macro_name,
                    "selected_macro": selected_macro,
                    "iteration": 1,
                    "loop": loop,
                    "total_start_time": current_time,
                    "iteration_start_time": current_time,
                    "last_event_time": current_time,
                }
            )

            self.play_events(selected_macro, loop)
        except (IndexError, ValueError):
            print("Invalid choice.")

    def play_events(self, selected_macro, loop=False):
        """Play recorded events with precise timing and reliable pause/resume."""
        if not selected_macro:
            print("No events recorded!")
            return

        while True:
            iteration_start = time.time()
            events = selected_macro.copy()
            i = self.pause_state["current_index"]

            while i < len(events):
                event = events[i]
                target_time = event["time"]

                # Calculate when this event should occur relative to iteration start
                target_absolute_time = iteration_start + target_time

                # Wait and handle pause states
                while time.time() < target_absolute_time:
                    if self.state != "playing":
                        if self.state == "paused":
                            # Store the time we paused at
                            pause_time = time.time()
                            self.pause_state["enabled"] = True
                            self.pause_state["current_index"] = i

                            while self.state == "paused":
                                time.sleep(0.01)

                            if self.state != "playing":
                                return

                            # Adjust iteration_start by the duration we were paused
                            pause_duration = time.time() - pause_time
                            iteration_start += pause_duration
                            break  # Recalculate target_absolute_time
                        else:  # state is "idle" (stopped)
                            return
                    time.sleep(0.001)

                # Recalculate target time after potential pause
                target_absolute_time = iteration_start + target_time

                # Final state check before executing
                if self.state != "playing":
                    continue

                # Wait for any remaining time
                current_time = time.time()
                if current_time < target_absolute_time:
                    time.sleep(target_absolute_time - current_time)

                # Notify about current event time
                if self.on_event_executed:
                    self.on_event_executed(target_time)

                # Execute the event
                elapsed = time.time() - iteration_start
                if event["type"] == "mouse":
                    current_pos = self.mouse_controller.position
                    jittered_x, jittered_y = self.apply_position_jitter(
                        event["x"], event["y"]
                    )

                    if self.smooth_mouse["enabled"]:
                        self.move_mouse_smoothly(
                            current_pos[0], current_pos[1], jittered_x, jittered_y
                        )
                    else:
                        self.mouse_controller.position = (jittered_x, jittered_y)

                    button = Button.left if event["button"] == "left" else Button.right
                    print(
                        f"[{elapsed:.2f}s] Mouse click: {button.name} at ({jittered_x}, {jittered_y})"
                    )

                    self.mouse_controller.press(button)
                    self.mouse_controller.release(button)

                elif event["type"] == "keyboard":
                    if event["is_special"]:
                        key = self.special_keys_reverse.get(event["key"])
                    else:
                        key = event["key"]

                    if event["action"] == "press":
                        print(f"[{elapsed:.2f}s] Key press: {key}")
                        self.keyboard_controller.press(key)
                    else:
                        print(f"[{elapsed:.2f}s] Key release: {key}")
                        self.keyboard_controller.release(key)

                elif event["type"] == "delay":
                    print(f"[{elapsed:.2f}s] Delay")

                # Increment index after successful execution
                i += 1
                self.pause_state["current_index"] = i

            # End of iteration
            if not loop or self.state != "playing":
                break

            print("\nStarting next iteration...")
            self.pause_state.update(
                {
                    "current_index": 0,
                    "iteration": self.pause_state["iteration"] + 1,
                    "iteration_start_time": time.time(),
                }
            )

    def pause_playback(self):
        """Pause playback without executing any additional events."""
        if self.state == "playing":
            self.state = "paused"
            print("\nPlayback paused. Press SPACE to resume or ESC to stop.")

    def resume_playback(self):
        """Resume playback from exactly where it was paused."""
        if self.state == "paused":
            self.state = "playing"
            print("\nPlayback resumed...")

    def stop_playing(self):
        if self.state in ["playing", "paused"]:
            self.state = "idle"
            self.pause_state["enabled"] = False
            print("Playback stopped.")

    def start_recording(self):
        self.events.clear()
        self.start_time = time.time()
        self.last_recorded_time = None
        self.state = "recording"
        print("Recording started... Press ESC to stop.")

    def stop_recording(self):
        """Stop recording and notify listeners"""
        if self.state == "recording":
            self.add_final_timing()
            self.state = "idle"
            print("Recording stopped.")

            # Notify listeners if callback is set
            if self.on_recording_stopped:
                self.on_recording_stopped()

    def on_press(self, key):
        if self.state == "recording":
            self.record_key(key, True)

        if key == Key.esc:
            if self.state == "playing" or self.state == "paused":
                self.stop_playing()
            elif self.state == "recording":
                self.stop_recording()
        elif key == Key.space:
            if self.state == "playing":
                self.pause_playback()
            elif self.state == "paused":
                self.resume_playback()

    def on_release(self, key):
        if self.state == "recording":
            self.record_key(key, False)


def main():
    recorder = MacroRecorder()

    # Start mouse listener
    mouse_listener = mouse.Listener(on_click=recorder.record_click)
    mouse_listener.start()

    # Start keyboard listener
    key_listener = keyboard.Listener(
        on_press=recorder.on_press, on_release=recorder.on_release
    )
    key_listener.start()

    try:
        while True:
            state_msg = ""
            if recorder.state == "paused":
                state_msg = " (PAUSED)"

            print(
                f"\nOptions:{state_msg}\n1. Start Recording\n2. Play Once\n3. Play in Loop\n"
                "4. Save Macro\n5. Edit macro\n6. Configure Randomization\n7. Exit"
            )
            choice = input("Enter your choice: ").strip()

            if choice == "1":
                recorder.start_recording()
                while recorder.state == "recording":
                    time.sleep(0.1)
                continue

            elif choice == "2":
                macros = recorder.load_all_macros()
                recorder.play_macro(macros, loop=False)
            elif choice == "3":
                macros = recorder.load_all_macros()
                recorder.play_macro(macros, loop=True)
            elif choice == "4":
                filename = (
                    input("Enter filename for the macro (without extension): ").strip()
                    + ".json"
                )
                recorder.save_macro(filename)
            elif choice == "5":
                macros = recorder.load_all_macros()
                recorder.edit_macro(macros)
            elif choice == "6":
                recorder.configure_randomization()
            elif choice == "7":
                mouse_listener.stop()
                recorder.stop_playing()
                key_listener.stop()
                break
            else:
                print("Invalid choice!")
    except KeyboardInterrupt:
        recorder.stop_recording()
        recorder.stop_playing()
        mouse_listener.stop()
        key_listener.stop()


if __name__ == "__main__":
    main()
