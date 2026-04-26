import can
import time

# Import global variables from config file
from src.core.config import MAX_MSG_RATE

# Connect to virtual CAN network
bus = can.interface.Bus(channel='vcan0', interface='socketcan')

print("Flood detector online... Press Ctrl+C to stop.")

# Count messages per CAN ID
msg_counts = {}

# Start 1-second window
window_start = time.time()

try:
    while True:
        msg = bus.recv(timeout = 0.1)
        current_time = time.time()
        
        # Count messages if recived
        if msg is not None:
            can_id = msg.arbitration_id

            if can_id not in msg_counts:
                msg_counts[can_id] = 0
            msg_counts[can_id] += 1

        # Every 1 second, print rate report
        if current_time - window_start >= 1.0:
            print("\n--- Message Rate Report ---")

            for can_id, count in msg_counts.items():
                print(f"CAN ID {hex(can_id)} -> {count} msg/sec")

                if count > MAX_MSG_RATE:
                    print(f"ALERT: Flood suspected on CAN ID {hex(can_id)}")

            # Reset for next window
            msg_counts.clear()
            window_start = current_time

# If interupt sent stop sneding messages and print
except KeyboardInterrupt:
    print("\nFlood detector stopped.")