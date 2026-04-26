# CAN Bus Attack Detection & Mitigation Simulator

## Overview
This project simulates a vehicle CAN bus system and demonstrates how common CAN attacks work, how they can be detected, and how they can be mitigated in real time.

The system models three vehicle signals:
- Speed
- RPM
- Brake

Each signal is targeted by a different type of attack:
- Flooding (Speed)
- Spoofing (RPM)
- Replay (Brake)

Detection and mitigation logic are applied to maintain safe system behavior.

---

## Features
- Simulated ECU signal generation
- Real-time CAN bus communication using SocketCAN (`vcan0`)
- Attack simulation: Flood, Spoof, Replay
- Detection logic: rate, value, and timing checks
- Mitigation logic: reject invalid values and hold safe state
- GUI dashboard for visualization and control
- Live CAN traffic monitoring with `candump`

---

## Environment
- Ubuntu (VM or Linux)
- Python 3
- SocketCAN (`vcan0`)
- python-can library

---

## Setup Instructions

### 1. Clone the repository
git clone https://github.com/CE-KenS/can-attack-detect-project.git  
cd can-attack-detect-project  

### 2. Set up virtual environment (optional but recommended)
python3 -m venv venv  
source venv/bin/activate  

### 3. Install dependencies
pip install python-can  

### 4. Set up virtual CAN interface
Run this every time you start the VM:
sudo modprobe vcan  
sudo ip link add dev vcan0 type vcan 
sudo ip link set up vcan0  

---

## Running the Project

### Start the GUI system
python3 -m src.gui.app  

### Monitor CAN bus traffic in a separate terminal
candump vcan0  

## Notes
- The GUI publishes CAN messages directly to `vcan0`  
- `candump` shows raw attacked bus traffic  
- GUI displays mitigated trusted system output  

---

## Author
Kenneth Sutter  
4/25/2026