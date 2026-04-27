# Program Name: replay_detector
# Author: Kenneth Sutter
# Date: 4/03/26
# Description: Code to detect replay attacks on CAN network vcan0

import can
import time

# Import global variables from config file
from src.core.config import CAN_ID_BRAKE

# Connect to virtual CAN network
bus = can.interface.Bus(channel='vcan0', interface='socketcan')

print("Brake replay detector online... Press Ctrl+C to stop.")

# Initialize variable to store last brake signal
last_brake = None
last_change_time = None

try:
    while True:
        # Wait and check if CAN message was recived
        msg = bus.recv(timeout=0.1)

        # Ensure brake signal was sent and store if brake was sent
        if msg is not None and msg.arbitration_id == CAN_ID_BRAKE:
            brake = msg.data[0]
            current_time = time.time()

            # Ensure we have the last brake signal to compare against
            if last_brake is not None:
                if brake != last_brake:
                    
                    # Measure the time between changes
                    time_diff = current_time - last_change_time

                    # Detect abnormal timing on CAN bus
                    if time_diff < 0.1:
                        print(f"ALERT: Rapid brake toggling detected ({time_diff:.3f}s)")

                    # Update time change
                    last_change_time = current_time
            # Update state foor next loop
            else:
                last_change_time = current_time
            last_brake = brake

# If interupt sent stop sneding messages and print
except KeyboardInterrupt:
    print("\nReplay detector stopped.")