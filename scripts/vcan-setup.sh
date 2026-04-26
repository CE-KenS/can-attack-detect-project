#!/bin/bash

echo "Setting up virtual CAN..."

# Load module
sudo modprobe vcan

# Remove existing interface if it exists
sudo ip link delete vcan0 2>/dev/null

# Create interface
sudo ip link add dev vcan0 type vcan

# Bring it up
sudo ip link set up vcan0

echo "vcan0 is ready"