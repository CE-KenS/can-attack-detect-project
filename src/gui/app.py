# Program Name: app
# Author: Kenneth Sutter
# Date: 4/05/26
# Description: This code creates a Tkinter dashboard for the CAN security project that displays live vehicle data, lets the user enable or disable attacks, 
# detection, and mitigation, and shows system alerts in an event log.

import tkinter as tk
from tkinter import ttk

# Import the main CAN controller that handles simulation, attacks, detection, and mitigation
from src.core.controller import CANSystemController


class CANSecurityApp:
    def __init__(self, root):
        # Store the main Tkinter window
        self.root = root

        # Set the window title and size
        self.root.title("CAN Security Project")
        self.root.geometry("1000x700")

        # Create and start the CAN system controller
        # This runs the CAN simulation in the background
        self.controller = CANSystemController()
        self.controller.start()

        # Build the dashboard interface
        self._build_ui()

        # Start refreshing the dashboard values
        self._refresh_ui()

        # Make sure the controller stops safely when the window is closed
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build_ui(self):
        # Main container for the whole application
        main = ttk.Frame(self.root, padding=12)
        main.pack(fill="both", expand=True)

        # Live vehicle data section
        # Displays trusted speed, RPM, and brake values
        vehicle_frame = ttk.LabelFrame(main, text="Live Vehicle Data", padding=10)
        vehicle_frame.pack(fill="x", pady=6)

        # Text variables used to update live vehicle values on the screen
        self.speed_var = tk.StringVar(value="Speed: 0 mph")
        self.rpm_var = tk.StringVar(value="RPM: 0")
        self.brake_var = tk.StringVar(value="Brake: OFF")

        # Labels that show the current speed, RPM, and brake state
        ttk.Label(vehicle_frame, textvariable=self.speed_var, font=("Arial", 14)).pack(anchor="w")
        ttk.Label(vehicle_frame, textvariable=self.rpm_var, font=("Arial", 14)).pack(anchor="w")
        ttk.Label(vehicle_frame, textvariable=self.brake_var, font=("Arial", 14)).pack(anchor="w")

        # Control section container
        # Holds attack, detection, and mitigation controls
        controls = ttk.Frame(main)
        controls.pack(fill="x", pady=6)

        # Attack controls section
        attack_frame = ttk.LabelFrame(controls, text="Attack Controls", padding=10)
        attack_frame.pack(side="left", fill="both", expand=True, padx=4)

        # Detection controls section
        detection_frame = ttk.LabelFrame(controls, text="Detection Controls", padding=10)
        detection_frame.pack(side="left", fill="both", expand=True, padx=4)

        # Mitigation controls section
        mitigation_frame = ttk.LabelFrame(controls, text="Mitigation Controls", padding=10)
        mitigation_frame.pack(side="left", fill="both", expand=True, padx=4)

        # Attack toggle variables
        # These store whether each attack checkbox is on or off
        self.flood_attack_var = tk.BooleanVar(value=False)
        self.spoof_attack_var = tk.BooleanVar(value=False)
        self.replay_attack_var = tk.BooleanVar(value=False)

        # Flood attack checkbox
        # Turns the speed flood attack on or off
        ttk.Checkbutton(
            attack_frame,
            text="Flood Attack (Speed)",
            variable=self.flood_attack_var,
            command=lambda: self.controller.set_flood_attack(self.flood_attack_var.get()),
        ).pack(anchor="w")

        # Spoof attack checkbox
        # Turns the RPM spoof attack on or off
        ttk.Checkbutton(
            attack_frame,
            text="Spoof Attack (RPM)",
            variable=self.spoof_attack_var,
            command=lambda: self.controller.set_spoof_attack(self.spoof_attack_var.get()),
        ).pack(anchor="w")

        # Replay attack checkbox
        # Turns the brake replay attack on or off
        ttk.Checkbutton(
            attack_frame,
            text="Replay Attack (Brake)",
            variable=self.replay_attack_var,
            command=lambda: self.controller.set_replay_attack(self.replay_attack_var.get()),
        ).pack(anchor="w")

        # Button to disable all attacks at once
        ttk.Button(
            attack_frame,
            text="Stop All Attacks",
            command=self._stop_all_attacks,
        ).pack(anchor="w", pady=8)

        # Detection toggle variables
        # These store whether each detection method is enabled
        self.flood_detection_var = tk.BooleanVar(value=True)
        self.spoof_detection_var = tk.BooleanVar(value=True)
        self.replay_detection_var = tk.BooleanVar(value=True)

        # Flood detection checkbox
        # Enables or disables speed flood detection
        ttk.Checkbutton(
            detection_frame,
            text="Flood Detection",
            variable=self.flood_detection_var,
            command=lambda: self.controller.set_flood_detection(self.flood_detection_var.get()),
        ).pack(anchor="w")

        # Spoof detection checkbox
        # Enables or disables RPM spoof detection
        ttk.Checkbutton(
            detection_frame,
            text="Spoof Detection",
            variable=self.spoof_detection_var,
            command=lambda: self.controller.set_spoof_detection(self.spoof_detection_var.get()),
        ).pack(anchor="w")

        # Replay detection checkbox
        # Enables or disables brake replay detection
        ttk.Checkbutton(
            detection_frame,
            text="Replay Detection",
            variable=self.replay_detection_var,
            command=lambda: self.controller.set_replay_detection(self.replay_detection_var.get()),
        ).pack(anchor="w")

        # Mitigation toggle variables
        # These store whether each mitigation method is enabled
        self.speed_mit_var = tk.BooleanVar(value=True)
        self.rpm_mit_var = tk.BooleanVar(value=True)
        self.brake_mit_var = tk.BooleanVar(value=True)

        # Speed mitigation checkbox
        # Enables or disables filtering unsafe speed values
        ttk.Checkbutton(
            mitigation_frame,
            text="Speed Mitigation",
            variable=self.speed_mit_var,
            command=lambda: self.controller.set_speed_mitigation(self.speed_mit_var.get()),
        ).pack(anchor="w")

        # RPM mitigation checkbox
        # Enables or disables filtering unsafe RPM values
        ttk.Checkbutton(
            mitigation_frame,
            text="RPM Mitigation",
            variable=self.rpm_mit_var,
            command=lambda: self.controller.set_rpm_mitigation(self.rpm_mit_var.get()),
        ).pack(anchor="w")

        # Brake mitigation checkbox
        # Enables or disables filtering suspicious brake replay behavior
        ttk.Checkbutton(
            mitigation_frame,
            text="Brake Mitigation",
            variable=self.brake_mit_var,
            command=lambda: self.controller.set_brake_mitigation(self.brake_mit_var.get()),
        ).pack(anchor="w")

        # Event log section
        # Shows controller messages, alerts, and mitigation actions
        log_frame = ttk.LabelFrame(main, text="Event Log", padding=10)
        log_frame.pack(fill="both", expand=True, pady=6)

        # Text box used to display the event log
        # Disabled so the user cannot accidentally edit it
        self.log_text = tk.Text(log_frame, height=20, state="disabled")
        self.log_text.pack(fill="both", expand=True)

    def _stop_all_attacks(self):
        # Tell the controller to disable every attack
        self.controller.stop_all_attacks()

        # Update the GUI checkboxes so they match the controller state
        self.flood_attack_var.set(False)
        self.spoof_attack_var.set(False)
        self.replay_attack_var.set(False)

    def _refresh_ui(self):
        # Get the latest trusted state from the controller
        state = self.controller.get_state()

        # Update the live vehicle data labels
        self.speed_var.set(f"Speed: {state['speed']} mph")
        self.rpm_var.set(f"RPM: {state['rpm']}")
        self.brake_var.set(f"Brake: {'ON' if state['brake'] else 'OFF'}")

        # Enable the log box so it can be updated
        self.log_text.configure(state="normal")

        # Clear the old log text
        self.log_text.delete("1.0", tk.END)

        # Insert the newest event log messages
        self.log_text.insert(tk.END, "\n".join(state["event_log"]))

        # Disable the log box again so it is read-only
        self.log_text.configure(state="disabled")

        # Auto-scroll to the bottom of the log
        self.log_text.see(tk.END)

        # Refresh the GUI again every 250 milliseconds
        self.root.after(250, self._refresh_ui)

    def on_close(self):
        # Stop the CAN controller before closing the app
        self.controller.stop()

        # Destroy the Tkinter window
        self.root.destroy()


def main():
    # Create the main Tkinter window
    root = tk.Tk()

    # Create the CAN security dashboard application
    app = CANSecurityApp(root)

    # Start the Tkinter event loop
    root.mainloop()


# Run the app only when this file is executed directly
if __name__ == "__main__":
    main()