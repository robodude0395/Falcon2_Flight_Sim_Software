import sys
import socket
import struct
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QSlider, QLabel, QCheckBox, QPushButton
from PyQt5.QtCore import Qt, QTimer
from udp_tx_rx import UdpSend, UdpReceive

#This is a dummy airplane app where each part of the plane's pose is controlled using a dedicated slider

UDP_IP = "127.0.0.1"

#Define telemetry port for which to send out the messages containing status (any of the safety sensors tripper) and airplane pose
TELEMETRY_UDP_PORT = 5005

#NOTE: Again, its worth noting that in this project acceleration and translation are used somewhat arbitrarily as the airplane's linear acceleration
#dictates the chair's translatation to create an ilusion of movement.

#Define main window widget containing 6 sliders for the airplane's 6D pose (xaccel, yaccel, zaccell, roll, pitch, yaw)
class AirplaneControl(QWidget):
    def __init__(self):
        super().__init__()
        
        #Set window title and size
        self.setWindowTitle("Airplane Pose Control")
        self.setGeometry(100, 100, 300, 400)
        
        #Define layout to be vertical so that added components are on top of each other
        self.layout = QVBoxLayout()
        
        #Iteratively add label and slider widgets to the main window layout
        self.sliders = {}
        self.labels = {}
        self.pose_keys = ["x_accel", "y_accel", "z_accel", "roll_rate", "pitch_rate", "yaw_rate", "bank_angle", "pitch_angle"]
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
        
        #Add reset button widget to main window layout which resets all the slider values to their default value
        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset_sliders)
        self.layout.addWidget(self.reset_button)
        self.setLayout(self.layout)
        
        #UDP sender object
        self.udp_sender = UdpSend()
        
        #Define timer which sends out UDP messages every 100ms
        self.timer = QTimer()
        self.timer.timeout.connect(self.send_udp_data)
        self.timer.start(100)  # Send data every 100 ms
    
    #Method which updates each element of the self.pose list to each respective slider value. This also sets the label text to the appropiate value
    def update_pose(self, key, value):
        self.pose_values[key] = value
        self.labels[key].setText(f"{key}: {value}")
    
    #This method resets all the sliders to 0
    def reset_sliders(self):
        """Resets all sliders to 0."""
        for key in self.pose_keys:
            self.sliders[key].setValue(0)  # This will trigger valueChanged and update labels
    
    #This method sends the required telemetry data as a list of 6 floats and one boolean. The 6 floats are the airplane's pose and the boolean
    #states whether the chair or airplane iss in it's safe state
    def send_udp_data(self):
        data = self.pose_values.values()
        #print(data)
        data_str = ("xplane_telemetry, "+",".join(map(str, data)))
        self.udp_sender.send(data_str, (UDP_IP, TELEMETRY_UDP_PORT))
        
#Start up the window once script is called
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AirplaneControl()
    window.show()
    sys.exit(app.exec_())
