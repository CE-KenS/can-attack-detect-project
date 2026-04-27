# Program Name: secure_receiver
# Author: Kenneth Sutter
# Date: 4/02/26
# Description: This code creates a secure CAN receiver that listens for 
# speed, RPM, and brake messages, detects flooding or suspicious signal behavior, 
# applies mitigation by holding last known good values, and prints the trusted dashboard output to the console

import can
import time

# Import global variables from config file
from src.core.config import (
    CAN_ID_SPEED,
    CAN_ID_RPM,
    CAN_ID_BRAKE,
    MAX_MSG_RATE,
    MAX_RPM_JUMP,
    MAX_RPM,
    MAX_SPEED
)

# Import mitigation logic for use in this file
from src.mitigations.mitigation_logic import (
    mitigate_speed,
    mitigate_rpm,
    mitigate_brake
)

# Connect to virtual CAN network
bus = can.interface.Bus(channel='vcan0', interface='socketcan')

print("Secure receiver online... Press Ctrl+C to stop.")

# Initialize current trusted dashboard values
latest_speed = 0
latest_rpm = 0
latest_brake = 0

# Initialize last known good value variables
last_good_speed = 0
last_good_rpm = 0
last_good_brake = 0

# Trrack speed for flood detection
msg_counts = {}
window_start = time.time()
flood_detected_speed = False

# Brake timing tracking
last_brake_change_time = None

try:
    while True:
        msg = bus.recv(timeout=0.1)
        current_time = time.time()

        # Count incoming messages by CAN ID
        if msg is not None:
            can_id = msg.arbitration_id

            if can_id not in msg_counts:
                msg_counts[can_id] = 0

            msg_counts[can_id] += 1

        # Check once per second for speed flooding
        if current_time - window_start >= 1.0:
            speed_count = msg_counts.get(CAN_ID_SPEED, 0)
            flood_detected_speed = speed_count > MAX_MSG_RATE

            if flood_detected_speed:
                print(f"ALERT! Flooding attack message rate too high for speed: {speed_count} msg/sec")
            
            msg_counts.clear()
            window_start = current_time

        # If no message was received, go to next loop
        if msg is None:
            continue

        # Handle speed messages
        if msg.arbitration_id == CAN_ID_SPEED:
            incoming_speed = msg.data[0]

            safe_speed = mitigate_speed(
                incoming_speed,
                flood_detected_speed,
                last_good_speed,
                MAX_SPEED
            )

            if safe_speed != incoming_speed:
                print(f"Mitigating flooded speed signals: holding {last_good_speed} value")
            else:
                last_good_speed = safe_speed

            latest_speed = safe_speed

        # Handle RPM messages
        elif msg.arbitration_id == CAN_ID_RPM:
            incoming_rpm = msg.data[0] | (msg.data[1] << 8)

            safe_rpm = mitigate_rpm(
                incoming_rpm,
                last_good_rpm,
                MAX_RPM_JUMP,
                MAX_RPM
            )

            if safe_rpm != incoming_rpm:
                print(f"Mitigating suspicious RPM signals {incoming_rpm}: holding {last_good_rpm} value")
            else:
                last_good_rpm = safe_rpm

            latest_rpm = safe_rpm

        # Handle brake messages
        elif msg.arbitration_id == CAN_ID_BRAKE:
            incoming_brake = msg.data[0]

            if last_brake_change_time is None:
                time_diff = 999.0
            else:
                time_diff = current_time - last_brake_change_time

            safe_brake = mitigate_brake(
                incoming_brake,
                last_good_brake,
                time_diff
            )

            if safe_brake != incoming_brake:
                print(f"Mitigating brake replay attack: holding {last_good_brake} value")
            else:
                if incoming_brake != last_good_brake:
                    last_brake_change_time = current_time
                last_good_brake = safe_brake

            latest_brake = safe_brake

        # Print secure dashboard values
        print(
            f"...SECURE DASHBOARD... "
            f"Speed: {latest_speed} mph | "
            f"RPM: {latest_rpm} | "
            f"Brake: {'ON' if latest_brake else 'OFF'}"
        )

# Import global variables from config file
except KeyboardInterrupt:
    print("\nSecure receiver stopped.")