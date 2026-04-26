# Import librarys
import can
import time

# Read from config and import values
from src.core.config import CAN_ID_SPEED, SPEED_SEND_PERIOD, DEFAULT_SPEED

# Send to vcan0 with socketcan
bus = can.interface.Bus(channel = 'vcan0', interface = 'socketcan')

print("Speed ECU is now operational...")

# While loop to send can frames over bus
while True:
    msg = can.Message(
        arbitration_id = CAN_ID_SPEED,
        data = [DEFAULT_SPEED],
        is_extended_id = False
    )
    try:
        bus.send(msg)
        print("Speed sent:", DEFAULT_SPEED)
    except:
        print("Error sending CAN message on network!")
    
    # Sleep timer to produce sending period
    time.sleep(SPEED_SEND_PERIOD)