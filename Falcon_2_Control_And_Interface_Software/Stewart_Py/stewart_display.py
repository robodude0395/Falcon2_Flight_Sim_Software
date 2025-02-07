import socket
import struct
import select
from src.stewart_controller import Stewart_Platform
import matplotlib.pyplot as plt
import numpy as np
import time
import matplotlib.animation as animation

# UDP Configuration
UDP_IP = "127.0.0.1"
TELEMETRY_UDP_PORT = 8005

# Set up UDP socket (Non-blocking)
sock_telemetry = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock_telemetry.bind((UDP_IP, TELEMETRY_UDP_PORT))
sock_telemetry.setblocking(False)  # Non-blocking mode to prevent delays

# Stewart Platform Setup
platform = Stewart_Platform(132/2, 100/2, 30, 130, 0.2269, 0.82, 5*np.pi/6)

# Global variables
values = []

def listen_for_telemetry():
    """Reads the latest UDP message, discarding old ones."""
    latest_data = None

    while True:
        # Check if data is available without blocking
        ready, _, _ = select.select([sock_telemetry], [], [], 0)  
        if not ready:
            break  # Exit if no more data

        try:
            data, addr = sock_telemetry.recvfrom(1024)  # Read all available data
            latest_data = data  # Keep only the latest message
        except BlockingIOError:
            break  # Exit if there's no data left

    if latest_data is None:
        return [], []

    # Unpack and return the latest values
    unpacked_values = struct.unpack("6f?", latest_data)
    print("Latest Data:", unpacked_values)
    
    trans, rot = unpacked_values[:3], unpacked_values[3:6]
    return trans, rot

# Initialize figure and axis for real-time plotting
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

def update(frame):
    """Update function for real-time plotting"""
    trans, rot = listen_for_telemetry()
    if trans and rot:  # If new data exists
        servo_angles = platform.calculate(np.array(trans), np.array(rot) * (np.pi / 180))
        platform.plot_platform(ax=ax)  # Update the 3D plot

# Start real-time animation
ani = animation.FuncAnimation(fig, update, interval=100)  # 100ms update rate

plt.show()