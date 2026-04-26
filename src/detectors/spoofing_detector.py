import can

# Import global variables from config file
from src.core.config import (
    CAN_ID_RPM,
    MAX_RPM_JUMP,
    MAX_RPM
)

# Connect to virtual CAN network
bus = can.interface.Bus(channel='vcan0', interface='socketcan')

print("RPM plausibility detector online... Press Ctrl+C to stop.")

# Initialize latest RPM variable
last_rpm = None

try:
    while True:
        msg = bus.recv(timeout=0.1)

        # Check if CAN message is there then decode the CAN frame
        if msg is not None and msg.arbitration_id == CAN_ID_RPM:
            rpm = msg.data[0] | (msg.data[1] << 8)

            # Check for out of range RPM
            if rpm > MAX_RPM:
                print(f"ALERT: RPM out of range: {rpm}")

            # Check for unrealistic RPM jumps
            if last_rpm is not None:
                jump = abs(rpm - last_rpm)

                if jump > MAX_RPM_JUMP:
                    print(f"ALERT: RPM jump detected: {last_rpm} -> {rpm}")

            # Save current RPM for next comparison
            last_rpm = rpm

# If interupt sent stop sneding messages and print
except KeyboardInterrupt:
    print("\nRPM spoofing detector stopped.")