# Program Name: dashboard_receiver
# Author: Kenneth Sutter
# Date: 4/01/26
# Description: This code starts a simple CAN dashboard that listens on the vcan0 interface, receives speed messages using 
# the configured CAN speed ID, and prints the decoded speed value to the console.

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
