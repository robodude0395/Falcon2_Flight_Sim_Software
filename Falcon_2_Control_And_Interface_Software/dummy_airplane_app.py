import sys
import socket
import struct
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QSlider, QLabel, QCheckBox, QPushButton
from PyQt5.QtCore import Qt, QTimer

TELEMETRY_UDP_PORT = 5005

class AirplaneControl(QWidget):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Airplane Pose Control")
        self.setGeometry(100, 100, 300, 400)
        
        self.layout = QVBoxLayout()
        
        self.sliders = {}
        self.labels = {}
        self.pose_keys = ["xpos", "ypos", "zpos", "roll", "pitch", "yaw"]
        self.pose_values = {key: 0 for key in self.pose_keys}
        
        for key in self.pose_keys:
            label = QLabel(f"{key}: 0")
            slider = QSlider(Qt.Horizontal)
            slider.setMinimum(-180)
            slider.setMaximum(180)
            slider.setValue(0)
            slider.setSingleStep(1)  # Increment/decrement by 1 on arrow click
            slider.valueChanged.connect(lambda value, k=key: self.update_pose(k, value))
            
            self.labels[key] = label
            self.sliders[key] = slider
            
            self.layout.addWidget(label)
            self.layout.addWidget(slider)
        
        self.safe_state = QCheckBox("Safe State")
        self.safe_state.setChecked(True)
        self.layout.addWidget(self.safe_state)
        
        # Reset Button
        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset_sliders)
        self.layout.addWidget(self.reset_button)
        
        self.setLayout(self.layout)
        
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_target = ("127.0.0.1", TELEMETRY_UDP_PORT)  # Change to the target IP and port
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.send_udp_data)
        self.timer.start(100)  # Send data every 100 ms
        
    def update_pose(self, key, value):
        self.pose_values[key] = value
        self.labels[key].setText(f"{key}: {value}")
    
    def reset_sliders(self):
        """Resets all sliders to 0."""
        for key in self.pose_keys:
            self.sliders[key].setValue(0)  # This will trigger valueChanged and update labels
    
    def send_udp_data(self):
        data = list(self.pose_values.values()) + [int(self.safe_state.isChecked())]
        packed_data = struct.pack("6f?", *data)
        self.udp_socket.sendto(packed_data, self.udp_target)
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AirplaneControl()
    window.show()
    sys.exit(app.exec_())
