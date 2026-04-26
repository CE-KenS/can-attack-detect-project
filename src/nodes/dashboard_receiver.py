import can

# import can speed parameter from config file
from src.core.config import CAN_ID_SPEED

# Initalize CAN bus and socketcan interface
bus = can.interface.Bus(channel = 'vcan0', interface = 'socketcan')

# Let user know speed is being recived
print("Dashboard is up and reciving can signals...")

# While loop to look for mesage ids and display them on the console
while True:
    msg = bus.recv()

    if msg.arbitration_id == CAN_ID_SPEED:
        speed = msg.data[0]
        print("Speed:", speed)
