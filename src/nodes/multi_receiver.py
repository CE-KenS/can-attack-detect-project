# Program Name: multi_receiver
# Author: Kenneth Sutter
# Date: 4/01/26
# Description: This code creates a CAN dashboard receiver that listens on vcan0, reads speed, RPM, and brake CAN messages, 
# decodes their values, and continuously prints the latest vehicle state to the console.

import can

from src.core.config import (
    CAN_ID_SPEED,
    CAN_ID_RPM,
    CAN_ID_BRAKE
)

# Connect to virtual CAN network
bus  = can.interface.Bus(channel = 'vcan0', interface = 'socketcan')

print("Dashboard is online...")

# Store latest values
latest_speed = 0
latest_rpm = 0
latest_brake = 0

try:
    while True:
        
        # Look for next can frame
        msg = bus.recv()

        # Speed message
        if msg.arbitration_id == CAN_ID_SPEED:
            latest_speed = msg.data[0]
        
        # RPM message this is 2 bytes
        elif msg.arbitration_id == CAN_ID_RPM:
            latest_rpm = msg.data[0] | (msg.data[1] << 8)

        # Brake message
        elif msg.arbitration_id == CAN_ID_BRAKE:
            latest_brake = msg.data[0]

        # Print current state
        print(
            f"Dashboard Readout: "
            f"Speed: {latest_speed} mph | "
            f"RPM: {latest_rpm} | "
            f"Brake: {'ON' if latest_brake else 'OFF'}"
        )

# If interupt sent stop sneding messages and print
except KeyboardInterrupt:
    print("\nReceiver stopped.")
