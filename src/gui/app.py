import tkinter as tk
from tkinter import ttk

from src.core.controller import CANSystemController


class CANSecurityApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CAN Security Project")
        self.root.geometry("1000x700")

        self.controller = CANSystemController()
        self.controller.start()

        self._build_ui()
        self._refresh_ui()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build_ui(self):
        main = ttk.Frame(self.root, padding=12)
        main.pack(fill="both", expand=True)

        vehicle_frame = ttk.LabelFrame(main, text="Live Vehicle Data", padding=10)
        vehicle_frame.pack(fill="x", pady=6)

        self.speed_var = tk.StringVar(value="Speed: 0 mph")
        self.rpm_var = tk.StringVar(value="RPM: 0")
        self.brake_var = tk.StringVar(value="Brake: OFF")

        ttk.Label(vehicle_frame, textvariable=self.speed_var, font=("Arial", 14)).pack(anchor="w")
        ttk.Label(vehicle_frame, textvariable=self.rpm_var, font=("Arial", 14)).pack(anchor="w")
        ttk.Label(vehicle_frame, textvariable=self.brake_var, font=("Arial", 14)).pack(anchor="w")

        controls = ttk.Frame(main)
        controls.pack(fill="x", pady=6)

        attack_frame = ttk.LabelFrame(controls, text="Attack Controls", padding=10)
        attack_frame.pack(side="left", fill="both", expand=True, padx=4)

        detection_frame = ttk.LabelFrame(controls, text="Detection Controls", padding=10)
        detection_frame.pack(side="left", fill="both", expand=True, padx=4)

        mitigation_frame = ttk.LabelFrame(controls, text="Mitigation Controls", padding=10)
        mitigation_frame.pack(side="left", fill="both", expand=True, padx=4)

        self.flood_attack_var = tk.BooleanVar(value=False)
        self.spoof_attack_var = tk.BooleanVar(value=False)
        self.replay_attack_var = tk.BooleanVar(value=False)

        ttk.Checkbutton(
            attack_frame,
            text="Flood Attack (Speed)",
            variable=self.flood_attack_var,
            command=lambda: self.controller.set_flood_attack(self.flood_attack_var.get()),
        ).pack(anchor="w")

        ttk.Checkbutton(
            attack_frame,
            text="Spoof Attack (RPM)",
            variable=self.spoof_attack_var,
            command=lambda: self.controller.set_spoof_attack(self.spoof_attack_var.get()),
        ).pack(anchor="w")

        ttk.Checkbutton(
            attack_frame,
            text="Replay Attack (Brake)",
            variable=self.replay_attack_var,
            command=lambda: self.controller.set_replay_attack(self.replay_attack_var.get()),
        ).pack(anchor="w")

        ttk.Button(
            attack_frame,
            text="Stop All Attacks",
            command=self._stop_all_attacks,
        ).pack(anchor="w", pady=8)

        self.flood_detection_var = tk.BooleanVar(value=True)
        self.spoof_detection_var = tk.BooleanVar(value=True)
        self.replay_detection_var = tk.BooleanVar(value=True)

        ttk.Checkbutton(
            detection_frame,
            text="Flood Detection",
            variable=self.flood_detection_var,
            command=lambda: self.controller.set_flood_detection(self.flood_detection_var.get()),
        ).pack(anchor="w")

        ttk.Checkbutton(
            detection_frame,
            text="Spoof Detection",
            variable=self.spoof_detection_var,
            command=lambda: self.controller.set_spoof_detection(self.spoof_detection_var.get()),
        ).pack(anchor="w")

        ttk.Checkbutton(
            detection_frame,
            text="Replay Detection",
            variable=self.replay_detection_var,
            command=lambda: self.controller.set_replay_detection(self.replay_detection_var.get()),
        ).pack(anchor="w")

        self.speed_mit_var = tk.BooleanVar(value=True)
        self.rpm_mit_var = tk.BooleanVar(value=True)
        self.brake_mit_var = tk.BooleanVar(value=True)

        ttk.Checkbutton(
            mitigation_frame,
            text="Speed Mitigation",
            variable=self.speed_mit_var,
            command=lambda: self.controller.set_speed_mitigation(self.speed_mit_var.get()),
        ).pack(anchor="w")

        ttk.Checkbutton(
            mitigation_frame,
            text="RPM Mitigation",
            variable=self.rpm_mit_var,
            command=lambda: self.controller.set_rpm_mitigation(self.rpm_mit_var.get()),
        ).pack(anchor="w")

        ttk.Checkbutton(
            mitigation_frame,
            text="Brake Mitigation",
            variable=self.brake_mit_var,
            command=lambda: self.controller.set_brake_mitigation(self.brake_mit_var.get()),
        ).pack(anchor="w")

        log_frame = ttk.LabelFrame(main, text="Event Log", padding=10)
        log_frame.pack(fill="both", expand=True, pady=6)

        self.log_text = tk.Text(log_frame, height=20, state="disabled")
        self.log_text.pack(fill="both", expand=True)

    def _stop_all_attacks(self):
        self.controller.stop_all_attacks()
        self.flood_attack_var.set(False)
        self.spoof_attack_var.set(False)
        self.replay_attack_var.set(False)

    def _refresh_ui(self):
        state = self.controller.get_state()

        self.speed_var.set(f"Speed: {state['speed']} mph")
        self.rpm_var.set(f"RPM: {state['rpm']}")
        self.brake_var.set(f"Brake: {'ON' if state['brake'] else 'OFF'}")

        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", tk.END)
        self.log_text.insert(tk.END, "\n".join(state["event_log"]))
        self.log_text.configure(state="disabled")
        self.log_text.see(tk.END)

        self.root.after(250, self._refresh_ui)

    def on_close(self):
        self.controller.stop()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = CANSecurityApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()