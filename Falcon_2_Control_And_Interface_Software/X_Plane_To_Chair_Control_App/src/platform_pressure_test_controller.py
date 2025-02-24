import sys
import socket
import struct
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QSlider, QLabel, QPushButton
from PyQt5.QtCore import Qt, QTimer
from udp_tx_rx import UdpSend

# This is a dummy airplane app where each part of the plane's pose is controlled using a dedicated slider

UDP_IP = "127.0.0.1"

# Define telemetry port for sending status messages and airplane pose
TELEMETRY_UDP_PORT = 5005

class AirplaneControl(QWidget):
    def __init__(self):
        super().__init__()

        # Set window title and size
        self.setWindowTitle("Airplane Pose Control")
        self.setGeometry(100, 100, 300, 400)

        # Define layout to be vertical
        self.layout = QVBoxLayout()

        # Define pose keys and their respective limits
        self.pose_keys = ["x_pos", "y_pos", "z_pos", "roll", "pitch", "yaw"]
        self.limits = [[-100, 100], [-122, 122], [-140, 140], [-15, 15], [-20, 20], [-12, 12]]
        self.pose_values = {key: 0 for key in self.pose_keys}

        # Store slider and label widgets
        self.sliders = {}
        self.labels = {}

        # Create sliders and labels with appropriate limits
        for key, limit in zip(self.pose_keys, self.limits):
            min_val, max_val = limit

            label = QLabel(f"{key}: 0")
            slider = QSlider(Qt.Horizontal)
            slider.setMinimum(min_val)
            slider.setMaximum(max_val)
            slider.setValue(0)
            slider.setSingleStep(1)  # Increment/decrement by 1

            slider.valueChanged.connect(lambda value, k=key: self.update_pose(k, value))

            self.labels[key] = label
            self.sliders[key] = slider

            self.layout.addWidget(label)
            self.layout.addWidget(slider)

        # Add reset button to reset all sliders
        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset_sliders)
        self.layout.addWidget(self.reset_button)
        
        self.setLayout(self.layout)

        # UDP sender object
        self.udp_sender = UdpSend()

        # Define timer to send UDP messages every 100ms
        self.timer = QTimer()
        self.timer.timeout.connect(self.send_udp_data)
        self.timer.start(100)  # Send data every 100 ms

    # Method to update each pose value and label
    def update_pose(self, key, value):
        self.pose_values[key] = value
        self.labels[key].setText(f"{key}: {value}")

    # Reset all sliders to 0
    def reset_sliders(self):
        for key in self.pose_keys:
            self.sliders[key].setValue(0)

    # Send telemetry data over UDP
    def send_udp_data(self):
        data = self.pose_values.values()
        data_str = "xplane_telemetry, " + ",".join(map(str, data))
        self.udp_sender.send(data_str, (UDP_IP, TELEMETRY_UDP_PORT))

# Start the application
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AirplaneControl()
    window.show()
    sys.exit(app.exec_())