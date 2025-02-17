import socket
import struct
import select
from src.stewart_controller import Stewart_Platform
import matplotlib.pyplot as plt
import numpy as np
import time
import matplotlib.animation as animation
from udp_tx_rx import UdpReceive

#Define UDP port to listen in for pose data. This will be sent from the state_machine.py node
UDP_IP = "127.0.0.1"
TELEMETRY_UDP_PORT = 8005

# Set up UDP socket to listen for pose data (Non-blocking)
telemetry_listener = UdpReceive(TELEMETRY_UDP_PORT)

# Stewart Platform Setup. This is hardcoded and not obtained for a config file yet. Either way this is temporary means of displaying a how a similar
#platform moves until later when the proper display code is implemented and the chair is sufficiently built
platform = Stewart_Platform(132/2, 100/2, 30, 130, 0.2269, 0.82, 5*np.pi/6)

#Listen for incoming airplane telemetry and display it at a rate of 100ms. Inverse kinematics is done from a pre-made repo called "Stewart_Py".
#Later on the inverse kinematics calculations will be moved to state_machine.py node so that the chair only receives the desired muscle pressures.
def listen_for_telemetry():
    """Reads the latest UDP message, discarding old ones."""
    data = None

    while(telemetry_listener.available() > 0):
        data = telemetry_listener.get()

    if data is None:
        return [], []

    pose_data = data[1].split(",")
    pose_data = [int(float(r)) for r in pose_data]
    rotation = pose_data[5:9]

    #Flips roll and putch for debug's sake
    rotation[0], rotation[1] = -rotation[1], rotation[0]
    trans, rot = [0,0,0], rotation
    return trans, rot

# Initialize figure and axis for real-time plotting
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

#Define update method which displays stewart platform after applying the inverse kinematic values. The platform's pose matches the desired airplane pose.
def update(frame):
    """Update function for real-time plotting"""
    trans, rot = listen_for_telemetry()
    if trans and rot:  # If new data exists
        servo_angles = platform.calculate(np.array(trans), np.array(rot) * (np.pi / 180))
        platform.plot_platform(ax=ax)  # Update the 3D plot

# Start real-time animation
ani = animation.FuncAnimation(fig, update, interval=100)  # 100ms update rate

plt.show()