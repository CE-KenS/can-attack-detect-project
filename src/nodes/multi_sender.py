import can
import time

# Import global variables from config file
from src.core.config import (
    CAN_ID_SPEED,
    CAN_ID_RPM,
    CAN_ID_BRAKE,
    SEND_INTERVAL
)

# Connect to virtual CAN network
bus = can.interface.Bus(channel = 'vcan0', interface = 'socketcan')

print("Vehicle CAN network online...")

# Initialize driving variables
speed = 0
rpm = 800
brake = 0

try:
    while True:
        # Vehicle signals for driving
        if brake == 0:
            speed += 2
            rpm += 150
        else:
            speed -= 4
            rpm -= 300

        # Set min and max values for each parameter
        speed = max(0, min(speed, 180))
        rpm = max(300, min(rpm, 8000))

        # Braking behavior
        if speed >= 70:
            brake = 1
        elif speed <= 20:
            brake = 0

        # Speed behavior
        msg_speed = can.Message(
            arbitration_id = CAN_ID_SPEED,
            data = [speed],
            is_extended_id = False
        )
        bus.send(msg_speed)

        # RPM message this is in 2 bytes
        rpm_low = rpm & 0xFF
        rpm_high = (rpm >> 8) & 0xFF
        msg_rpm = can.Message(
            arbitration_id = CAN_ID_RPM,
            data = [rpm_low, rpm_high],
            is_extended_id = False
        )
        bus.send(msg_rpm)

        # Brake message
        msg_brake = can.Message(
            arbitration_id = CAN_ID_BRAKE,
            data = [brake],
            is_extended_id = False
        )
        bus.send(msg_brake)

        print(f"Message sent: Speed: {speed} mph | RPM: {rpm} | Brake: {brake}")

        # Setting signal frequency
        time.sleep(SEND_INTERVAL)

# Import global variables from config file
except KeyboardInterrupt:
    print("\n Sender has stopped sending messages")
