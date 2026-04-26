import threading
import time
import can
from collections import defaultdict

from src.core.config import (
    CAN_ID_SPEED,
    CAN_ID_RPM,
    CAN_ID_BRAKE,
    MAX_MSG_RATE,
    MAX_SPEED,
    MAX_RPM,
    MAX_RPM_JUMP,
)

from src.mitigations.mitigation_logic import (
    mitigate_speed,
    mitigate_rpm,
    mitigate_brake,
)


class CANSystemController:
    def __init__(self):
        self.lock = threading.Lock()
        self.running = False
        self.thread = None
        
        #CAN bus interface
        self.bus = can.interface.Bus(channel='vcan0', interface='socketcan')

        # Attack toggles
        self.flood_attack_enabled = False     # speed
        self.spoof_attack_enabled = False     # rpm
        self.replay_attack_enabled = False    # brake

        # Detection toggles
        self.flood_detection_enabled = True
        self.spoof_detection_enabled = True
        self.replay_detection_enabled = True

        # Mitigation toggles
        self.speed_mitigation_enabled = True
        self.rpm_mitigation_enabled = True
        self.brake_mitigation_enabled = True

        # Raw simulated vehicle state
        self.raw_speed = 0
        self.raw_rpm = 800
        self.raw_brake = 0

        # Trusted dashboard state
        self.speed = 0
        self.rpm = 800
        self.brake = 0

        # Last known good values
        self.last_good_speed = 0
        self.last_good_rpm = 800
        self.last_good_brake = 0

        # Detection state
        self.msg_counts = defaultdict(int)
        self.window_start = time.time()
        self.flood_detected_speed = False

        self.last_seen_rpm = None
        self.last_seen_brake = None

        # Replay detection timing
        self.last_detected_brake_change_time = None

        # Trusted brake timing for mitigation
        self.last_trusted_brake_change_time = None

        # Replay support
        self.replay_pattern = [0, 1, 0, 1, 1, 0]
        self.replay_pattern_index = 0
        self.replay_last_send_time = 0.0

        # Event log
        self.event_log = []
        self.max_log_entries = 200

    def log_event(self, message: str):
        timestamp = time.strftime("%H:%M:%S")
        entry = f"[{timestamp}] {message}"
        with self.lock:
            self.event_log.append(entry)
            if len(self.event_log) > self.max_log_entries:
                self.event_log.pop(0)

    def get_state(self):
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
        with self.lock:
            self.flood_attack_enabled = value
        self.log_event(f"Flood attack {'enabled' if value else 'disabled'}")

    def set_spoof_attack(self, value: bool):
        with self.lock:
            self.spoof_attack_enabled = value
        self.log_event(f"RPM spoof attack {'enabled' if value else 'disabled'}")

    def set_replay_attack(self, value: bool):
        with self.lock:
            self.replay_attack_enabled = value
        self.log_event(f"Brake replay attack {'enabled' if value else 'disabled'}")

    def set_flood_detection(self, value: bool):
        with self.lock:
            self.flood_detection_enabled = value
        self.log_event(f"Flood detection {'enabled' if value else 'disabled'}")

    def set_spoof_detection(self, value: bool):
        with self.lock:
            self.spoof_detection_enabled = value
        self.log_event(f"Spoof detection {'enabled' if value else 'disabled'}")

    def set_replay_detection(self, value: bool):
        with self.lock:
            self.replay_detection_enabled = value
        self.log_event(f"Replay detection {'enabled' if value else 'disabled'}")

    def set_speed_mitigation(self, value: bool):
        with self.lock:
            self.speed_mitigation_enabled = value
        self.log_event(f"Speed mitigation {'enabled' if value else 'disabled'}")

    def set_rpm_mitigation(self, value: bool):
        with self.lock:
            self.rpm_mitigation_enabled = value
        self.log_event(f"RPM mitigation {'enabled' if value else 'disabled'}")

    def set_brake_mitigation(self, value: bool):
        with self.lock:
            self.brake_mitigation_enabled = value
        self.log_event(f"Brake mitigation {'enabled' if value else 'disabled'}")

    def stop_all_attacks(self):
        with self.lock:
            self.flood_attack_enabled = False
            self.spoof_attack_enabled = False
            self.replay_attack_enabled = False
        self.log_event("All attacks disabled")

    def start(self):
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        self.log_event("Controller started")

    def stop(self):
        self.running = False
        if self.thread is not None:
            self.thread.join(timeout=1.0)
        self.bus.shutdown()
        self.log_event("Controller stopped")

    def _send_speed_frame(self, speed):
        msg = can.Message(
            arbitration_id=CAN_ID_SPEED,
            data=[speed],
            is_extended_id=False
        )
        self.bus.send(msg)


    def _send_rpm_frame(self, rpm):
        rpm_low = rpm & 0xFF
        rpm_high = (rpm >> 8) & 0xFF

        msg = can.Message(
            arbitration_id=CAN_ID_RPM,
            data=[rpm_low, rpm_high],
            is_extended_id=False
        )
        self.bus.send(msg)


    def _send_brake_frame(self, brake):
        msg = can.Message(
            arbitration_id=CAN_ID_BRAKE,
            data=[brake],
            is_extended_id=False
        )
        self.bus.send(msg)

    def _run_loop(self):
        while self.running:
            current_time = time.time()

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
            if self.raw_brake == 0:
                self.raw_speed += 2
                self.raw_rpm += 150
            else:
                self.raw_speed -= 4
                self.raw_rpm -= 300

            self.raw_speed = max(0, min(self.raw_speed, 180))
            self.raw_rpm = max(300, min(self.raw_rpm, 8000))

            if self.raw_speed >= 70:
                self.raw_brake = 1
            elif self.raw_speed <= 20:
                self.raw_brake = 0

            # Incoming values
            incoming_speed = self.raw_speed
            incoming_rpm = self.raw_rpm
            incoming_brake = self.raw_brake

            # Flood attack on speed
            if flood_attack:
                incoming_speed = 255
                self.msg_counts["speed"] += 20
            else:
                self.msg_counts["speed"] += 1

            # Spoof attack on RPM
            if spoof_attack:
                incoming_rpm = 7000

            self.msg_counts["rpm"] += 1

            # Replay attack on brake
            if replay_attack:
                if current_time - self.replay_last_send_time >= 0.05:
                    incoming_brake = self.replay_pattern[self.replay_pattern_index]
                    self.replay_pattern_index = (self.replay_pattern_index + 1) % len(self.replay_pattern)
                    self.replay_last_send_time = current_time
            else:
                incoming_brake = self.raw_brake

            
            self.msg_counts["brake"] += 1
            self._send_speed_frame(incoming_speed)
            self._send_rpm_frame(incoming_rpm)
            self._send_brake_frame(incoming_brake)
            
            # Flood detection
            if current_time - self.window_start >= 1.0:
                speed_rate = self.msg_counts["speed"]
                self.flood_detected_speed = False

                if flood_detection and speed_rate > MAX_MSG_RATE:
                    self.flood_detected_speed = True
                    self.log_event(f"[ALERT][FLOOD][SPEED] Rate too high: {speed_rate} msg/sec")

                self.msg_counts.clear()
                self.window_start = current_time

            # Spoof detection for RPM
            if spoof_detection and self.last_seen_rpm is not None:
                rpm_jump = abs(incoming_rpm - self.last_seen_rpm)

                if incoming_rpm > MAX_RPM:
                    self.log_event(f"[ALERT][SPOOF][RPM] Out of range: {incoming_rpm}")
                elif rpm_jump > MAX_RPM_JUMP:
                    self.log_event(f"[ALERT][SPOOF][RPM] Jump detected: {self.last_seen_rpm} -> {incoming_rpm}")

            # Replay detection for brake
            if replay_detection:
                if self.last_seen_brake is None:
                    self.last_detected_brake_change_time = current_time
                elif incoming_brake != self.last_seen_brake:
                    time_diff = current_time - self.last_detected_brake_change_time
                    if time_diff < 0.1:
                        self.log_event(f"[ALERT][REPLAY][BRAKE] Rapid toggle detected ({time_diff:.3f}s)")
                    self.last_detected_brake_change_time = current_time

            # Save seen values
            self.last_seen_rpm = incoming_rpm
            self.last_seen_brake = incoming_brake

            # Speed mitigation
            if speed_mitigation:
                safe_speed = mitigate_speed(
                    incoming_speed,
                    self.flood_detected_speed,
                    self.last_good_speed,
                    MAX_SPEED,
                )
            else:
                safe_speed = incoming_speed

            if safe_speed != incoming_speed:
                self.log_event(f"[MITIGATION][SPEED] Holding {self.last_good_speed} instead of {incoming_speed}")
            else:
                self.last_good_speed = safe_speed

            # RPM mitigation
            if rpm_mitigation:
                safe_rpm = mitigate_rpm(
                    incoming_rpm,
                    self.last_good_rpm,
                    MAX_RPM_JUMP,
                    MAX_RPM,
                )
            else:
                safe_rpm = incoming_rpm

            rpm_is_valid = True

            if incoming_rpm > MAX_RPM:
                rpm_is_valid = False

            if self.last_good_rpm is not None:
                if abs(incoming_rpm - self.last_good_rpm) > MAX_RPM_JUMP:
                    rpm_is_valid = False

            if safe_rpm != incoming_rpm:
                self.log_event(f"[MITIGATION][RPM] Holding {self.last_good_rpm} instead of {incoming_rpm}")

            if rpm_is_valid:
                self.last_good_rpm = incoming_rpm

            # Brake mitigation
            if self.last_trusted_brake_change_time is None:
                brake_time_diff = 999.0
            else:
                brake_time_diff = current_time - self.last_trusted_brake_change_time

            if brake_mitigation:
                safe_brake = mitigate_brake(
                    incoming_brake,
                    self.last_good_brake,
                    brake_time_diff,
                )
            else:
                safe_brake = incoming_brake

            if safe_brake != incoming_brake:
                self.log_event(f"[MITIGATION][BRAKE] Holding {self.last_good_brake} instead of {incoming_brake}")
            else:
                if incoming_brake != self.last_good_brake:
                    self.last_trusted_brake_change_time = current_time
                self.last_good_brake = safe_brake

            # Publish trusted state
            with self.lock:
                self.speed = safe_speed
                self.rpm = safe_rpm
                self.brake = safe_brake

            # Faster loop for responsive replay / GUI
            time.sleep(0.05)