# Program Name: controler
# Author: Kenneth Sutter
# Date: 4/02/26
# Description: This code creates a CAN system controller that simulates normal vehicle signals, 
# injects optional CAN attacks, detects suspicious behavior, 
# applies mitigation logic, and publishes trusted speed, RPM, and brake values to the dashboard.
import threading
import time
import can
from collections import defaultdict

# Import CAN IDs and detection limits from the config file
from src.core.config import (
    CAN_ID_SPEED,
    CAN_ID_RPM,
    CAN_ID_BRAKE,
    MAX_MSG_RATE,
    MAX_SPEED,
    MAX_RPM,
    MAX_RPM_JUMP,
)

# Import mitigation functions used to filter unsafe values
from src.mitigations.mitigation_logic import (
    mitigate_speed,
    mitigate_rpm,
    mitigate_brake,
)


class CANSystemController:
    def __init__(self):
        # Lock protects shared data between the GUI/API thread and controller loop
        self.lock = threading.Lock()

        # Controls whether the main CAN simulation loop is running
        self.running = False
        self.thread = None
        
        # CAN bus interface
        # Uses virtual CAN interface vcan0 through SocketCAN
        self.bus = can.interface.Bus(channel='vcan0', interface='socketcan')

        # Attack toggles
        # These control whether each attack is active
        self.flood_attack_enabled = False     # speed
        self.spoof_attack_enabled = False     # rpm
        self.replay_attack_enabled = False    # brake

        # Detection toggles
        # These control whether alerts are generated for attacks
        self.flood_detection_enabled = True
        self.spoof_detection_enabled = True
        self.replay_detection_enabled = True

        # Mitigation toggles
        # These control whether unsafe values are blocked or replaced
        self.speed_mitigation_enabled = True
        self.rpm_mitigation_enabled = True
        self.brake_mitigation_enabled = True

        # Raw simulated vehicle state
        # These values represent what the simulated vehicle is producing
        self.raw_speed = 0
        self.raw_rpm = 800
        self.raw_brake = 0

        # Trusted dashboard state
        # These values are shown after detection and mitigation are applied
        self.speed = 0
        self.rpm = 800
        self.brake = 0

        # Last known good values
        # Used by mitigation to hold a safe value when an attack is detected
        self.last_good_speed = 0
        self.last_good_rpm = 800
        self.last_good_brake = 0

        # Detection state
        # Tracks message counts for flood detection
        self.msg_counts = defaultdict(int)
        self.window_start = time.time()
        self.flood_detected_speed = False

        # Stores previous signal values for jump and replay detection
        self.last_seen_rpm = None
        self.last_seen_brake = None

        # Replay detection timing
        # Used to detect if brake values toggle too quickly
        self.last_detected_brake_change_time = None

        # Trusted brake timing for mitigation
        # Used to decide if a brake change is realistic or suspicious
        self.last_trusted_brake_change_time = None

        # Replay support
        # Pattern used when the brake replay attack is enabled
        self.replay_pattern = [0, 1, 0, 1, 1, 0]
        self.replay_pattern_index = 0
        self.replay_last_send_time = 0.0

        # Event log
        # Stores recent alerts, attacks, and mitigation messages for the GUI
        self.event_log = []
        self.max_log_entries = 200

    def log_event(self, message: str):
        # Add a timestamp to each event message
        timestamp = time.strftime("%H:%M:%S")
        entry = f"[{timestamp}] {message}"

        # Add message to log safely using the lock
        with self.lock:
            self.event_log.append(entry)

            # Keep the log from growing forever
            if len(self.event_log) > self.max_log_entries:
                self.event_log.pop(0)

    def get_state(self):
        # Return the current trusted state and toggle values
        # This is mainly used by the GUI/dashboard
        with self.lock:
            return {
                "speed": self.speed,
                "rpm": self.rpm,
                "brake": self.brake,
                "flood_attack_enabled": self.flood_attack_enabled,
                "spoof_attack_enabled": self.spoof_attack_enabled,
                "replay_attack_enabled": self.replay_attack_enabled,
                "flood_detection_enabled": self.flood_detection_enabled,
                "spoof_detection_enabled": self.spoof_detection_enabled,
                "replay_detection_enabled": self.replay_detection_enabled,
                "speed_mitigation_enabled": self.speed_mitigation_enabled,
                "rpm_mitigation_enabled": self.rpm_mitigation_enabled,
                "brake_mitigation_enabled": self.brake_mitigation_enabled,
                "event_log": list(self.event_log),
            }

    def set_flood_attack(self, value: bool):
        # Enable or disable speed flood attack
        with self.lock:
            self.flood_attack_enabled = value
        self.log_event(f"Flood attack {'enabled' if value else 'disabled'}")

    def set_spoof_attack(self, value: bool):
        # Enable or disable RPM spoof attack
        with self.lock:
            self.spoof_attack_enabled = value
        self.log_event(f"RPM spoof attack {'enabled' if value else 'disabled'}")

    def set_replay_attack(self, value: bool):
        # Enable or disable brake replay attack
        with self.lock:
            self.replay_attack_enabled = value
        self.log_event(f"Brake replay attack {'enabled' if value else 'disabled'}")

    def set_flood_detection(self, value: bool):
        # Enable or disable flood detection
        with self.lock:
            self.flood_detection_enabled = value
        self.log_event(f"Flood detection {'enabled' if value else 'disabled'}")

    def set_spoof_detection(self, value: bool):
        # Enable or disable spoof detection
        with self.lock:
            self.spoof_detection_enabled = value
        self.log_event(f"Spoof detection {'enabled' if value else 'disabled'}")

    def set_replay_detection(self, value: bool):
        # Enable or disable replay detection
        with self.lock:
            self.replay_detection_enabled = value
        self.log_event(f"Replay detection {'enabled' if value else 'disabled'}")

    def set_speed_mitigation(self, value: bool):
        # Enable or disable speed mitigation
        with self.lock:
            self.speed_mitigation_enabled = value
        self.log_event(f"Speed mitigation {'enabled' if value else 'disabled'}")

    def set_rpm_mitigation(self, value: bool):
        # Enable or disable RPM mitigation
        with self.lock:
            self.rpm_mitigation_enabled = value
        self.log_event(f"RPM mitigation {'enabled' if value else 'disabled'}")

    def set_brake_mitigation(self, value: bool):
        # Enable or disable brake mitigation
        with self.lock:
            self.brake_mitigation_enabled = value
        self.log_event(f"Brake mitigation {'enabled' if value else 'disabled'}")

    def stop_all_attacks(self):
        # Turn off all attacks at the same time
        with self.lock:
            self.flood_attack_enabled = False
            self.spoof_attack_enabled = False
            self.replay_attack_enabled = False
        self.log_event("All attacks disabled")

    def start(self):
        # Do nothing if the controller is already running
        if self.running:
            return

        # Start the controller loop in a background thread
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        self.log_event("Controller started")

    def stop(self):
        # Stop the controller loop
        self.running = False

        # Wait briefly for the thread to finish
        if self.thread is not None:
            self.thread.join(timeout=1.0)

        # Shut down the CAN bus interface
        self.bus.shutdown()
        self.log_event("Controller stopped")

    def _send_speed_frame(self, speed):
        # Create a CAN frame for speed
        # Speed fits in one data byte
        msg = can.Message(
            arbitration_id=CAN_ID_SPEED,
            data=[speed],
            is_extended_id=False
        )

        # Send speed frame on vcan0
        self.bus.send(msg)

    def _send_rpm_frame(self, rpm):
        # Split RPM into two bytes because RPM can be larger than 255
        rpm_low = rpm & 0xFF
        rpm_high = (rpm >> 8) & 0xFF

        # Create a CAN frame for RPM
        msg = can.Message(
            arbitration_id=CAN_ID_RPM,
            data=[rpm_low, rpm_high],
            is_extended_id=False
        )

        # Send RPM frame on vcan0
        self.bus.send(msg)

    def _send_brake_frame(self, brake):
        # Create a CAN frame for brake status
        # Brake is binary: 0 = off, 1 = on
        msg = can.Message(
            arbitration_id=CAN_ID_BRAKE,
            data=[brake],
            is_extended_id=False
        )

        # Send brake frame on vcan0
        self.bus.send(msg)

    def _run_loop(self):
        # Main simulation loop
        # Runs until self.running is set to False
        while self.running:
            current_time = time.time()

            # Copy toggle states safely so the loop can use them
            with self.lock:
                flood_attack = self.flood_attack_enabled
                spoof_attack = self.spoof_attack_enabled
                replay_attack = self.replay_attack_enabled

                flood_detection = self.flood_detection_enabled
                spoof_detection = self.spoof_detection_enabled
                replay_detection = self.replay_detection_enabled

                speed_mitigation = self.speed_mitigation_enabled
                rpm_mitigation = self.rpm_mitigation_enabled
                brake_mitigation = self.brake_mitigation_enabled

            # Normal vehicle behavior
            # If brake is off, vehicle speeds up
            if self.raw_brake == 0:
                self.raw_speed += 2
                self.raw_rpm += 150

            # If brake is on, vehicle slows down
            else:
                self.raw_speed -= 4
                self.raw_rpm -= 300

            # Keep raw values inside realistic simulation limits
            self.raw_speed = max(0, min(self.raw_speed, 180))
            self.raw_rpm = max(300, min(self.raw_rpm, 8000))

            # Automatically apply brake when speed gets high
            if self.raw_speed >= 70:
                self.raw_brake = 1

            # Automatically release brake when speed gets low
            elif self.raw_speed <= 20:
                self.raw_brake = 0

            # Incoming values
            # These start as normal raw values before attacks modify them
            incoming_speed = self.raw_speed
            incoming_rpm = self.raw_rpm
            incoming_brake = self.raw_brake

            # Flood attack on speed
            # Simulates too many speed messages arriving in one second
            if flood_attack:
                incoming_speed = 255
                self.msg_counts["speed"] += 20
            else:
                self.msg_counts["speed"] += 1

            # Spoof attack on RPM
            # Forces RPM to a fake high value
            if spoof_attack:
                incoming_rpm = 7000

            # Count RPM messages for tracking
            self.msg_counts["rpm"] += 1

            # Replay attack on brake
            # Sends a repeated brake pattern instead of the real brake value
            if replay_attack:
                if current_time - self.replay_last_send_time >= 0.05:
                    incoming_brake = self.replay_pattern[self.replay_pattern_index]
                    self.replay_pattern_index = (self.replay_pattern_index + 1) % len(self.replay_pattern)
                    self.replay_last_send_time = current_time

            # Normal brake behavior when replay attack is off
            else:
                incoming_brake = self.raw_brake

            # Count brake messages
            self.msg_counts["brake"] += 1

            # Send the incoming values onto the CAN bus
            self._send_speed_frame(incoming_speed)
            self._send_rpm_frame(incoming_rpm)
            self._send_brake_frame(incoming_brake)
            
            # Flood detection
            # Once per second, check how many speed messages were seen
            if current_time - self.window_start >= 1.0:
                speed_rate = self.msg_counts["speed"]
                self.flood_detected_speed = False

                # If speed message rate is too high, flag a flood attack
                if flood_detection and speed_rate > MAX_MSG_RATE:
                    self.flood_detected_speed = True
                    self.log_event(f"[ALERT][FLOOD][SPEED] Rate too high: {speed_rate} msg/sec")

                # Reset message count window
                self.msg_counts.clear()
                self.window_start = current_time

            # Spoof detection for RPM
            # Checks if RPM is out of range or jumps too fast
            if spoof_detection and self.last_seen_rpm is not None:
                rpm_jump = abs(incoming_rpm - self.last_seen_rpm)

                # Alert if RPM is above the allowed max
                if incoming_rpm > MAX_RPM:
                    self.log_event(f"[ALERT][SPOOF][RPM] Out of range: {incoming_rpm}")

                # Alert if RPM changes too quickly
                elif rpm_jump > MAX_RPM_JUMP:
                    self.log_event(f"[ALERT][SPOOF][RPM] Jump detected: {self.last_seen_rpm} -> {incoming_rpm}")

            # Replay detection for brake
            # Checks if brake is toggling faster than expected
            if replay_detection:
                if self.last_seen_brake is None:
                    self.last_detected_brake_change_time = current_time

                elif incoming_brake != self.last_seen_brake:
                    time_diff = current_time - self.last_detected_brake_change_time

                    # Very fast brake changes are treated as replay behavior
                    if time_diff < 0.1:
                        self.log_event(f"[ALERT][REPLAY][BRAKE] Rapid toggle detected ({time_diff:.3f}s)")

                    self.last_detected_brake_change_time = current_time

            # Save seen values
            # Used during the next loop for detection comparisons
            self.last_seen_rpm = incoming_rpm
            self.last_seen_brake = incoming_brake

            # Speed mitigation
            # If speed looks unsafe, hold the last good speed
            if speed_mitigation:
                safe_speed = mitigate_speed(
                    incoming_speed,
                    self.flood_detected_speed,
                    self.last_good_speed,
                    MAX_SPEED,
                )
            else:
                safe_speed = incoming_speed

            # Log when mitigation replaces the incoming speed
            if safe_speed != incoming_speed:
                self.log_event(f"[MITIGATION][SPEED] Holding {self.last_good_speed} instead of {incoming_speed}")

            # Update last good speed only when the value is trusted
            else:
                self.last_good_speed = safe_speed

            # RPM mitigation
            # If RPM jumps too much or exceeds max range, hold last good RPM
            if rpm_mitigation:
                safe_rpm = mitigate_rpm(
                    incoming_rpm,
                    self.last_good_rpm,
                    MAX_RPM_JUMP,
                    MAX_RPM,
                )
            else:
                safe_rpm = incoming_rpm

            # Track whether incoming RPM should update the last good value
            rpm_is_valid = True

            # RPM is invalid if it is above the max allowed value
            if incoming_rpm > MAX_RPM:
                rpm_is_valid = False

            # RPM is invalid if it jumps too far from the last trusted RPM
            if self.last_good_rpm is not None:
                if abs(incoming_rpm - self.last_good_rpm) > MAX_RPM_JUMP:
                    rpm_is_valid = False

            # Log when mitigation replaces the incoming RPM
            if safe_rpm != incoming_rpm:
                self.log_event(f"[MITIGATION][RPM] Holding {self.last_good_rpm} instead of {incoming_rpm}")

            # Update last good RPM only if the incoming RPM is valid
            if rpm_is_valid:
                self.last_good_rpm = incoming_rpm

            # Brake mitigation
            # Calculate how much time passed since the last trusted brake change
            if self.last_trusted_brake_change_time is None:
                brake_time_diff = 999.0
            else:
                brake_time_diff = current_time - self.last_trusted_brake_change_time

            # If brake changes too quickly, hold the last good brake value
            if brake_mitigation:
                safe_brake = mitigate_brake(
                    incoming_brake,
                    self.last_good_brake,
                    brake_time_diff,
                )
            else:
                safe_brake = incoming_brake

            # Log when mitigation replaces the incoming brake value
            if safe_brake != incoming_brake:
                self.log_event(f"[MITIGATION][BRAKE] Holding {self.last_good_brake} instead of {incoming_brake}")

            # If brake value is trusted, update last good brake state
            else:
                if incoming_brake != self.last_good_brake:
                    self.last_trusted_brake_change_time = current_time
                self.last_good_brake = safe_brake

            # Publish trusted state
            # These are the final values used by the dashboard
            with self.lock:
                self.speed = safe_speed
                self.rpm = safe_rpm
                self.brake = safe_brake

            # Faster loop for responsive replay / GUI
            time.sleep(0.05)