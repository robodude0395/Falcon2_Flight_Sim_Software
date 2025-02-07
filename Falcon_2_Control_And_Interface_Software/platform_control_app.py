from PyQt5 import QtWidgets
from gui_class import Ui_MainWindow  # Import your generated UI class
from PyQt5.QtCore import QThread
import sys
import socket
import threading
import numpy as np

# Set up UDP socket
udp_ip = "127.0.0.1"  # Same as the UDP listener
udp_send_port = 6005  # Must match the listener's port
udp_listen_port = 7005
send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
send_sock.setblocking(False)

class UDPListenerThread(QThread):
    """
    A separate thread to listen for UDP messages without blocking the GUI.
    """
    def __init__(self, host, port, callback):
        super().__init__()
        self.host = host
        self.port = port
        self.callback = callback
        self.running = True

        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.bind((self.host, self.port))

    def run(self):

        print(f"Listening for UDP packets on {self.host}:{self.port}...")

        while self.running:
            try:
                data, _ = self.udp_socket.recvfrom(1024)  # Receive data (max 1024 bytes)
                message, flag = data.decode().split("|")  # Extract message and boolean
                self.callback(message, bool(int(flag)))  # Send data to UI
            except Exception as e:
                print(f"UDP Listener Error: {e}")

    def stop(self):
        self.running = False
        """Stops the UDP server safely"""
        self.running = False
        self.udp_socket.close()
        self.quit()  # Properly close QThread
        self.wait()  # Ensure the thread is fully stopped

class MainApp(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)  # Load the UI

        # Connect slider signal
        self.master.valueChanged.connect(lambda value, lbl=self.master_label: self.update_label(value, lbl))
        self.xaccel.valueChanged.connect(lambda value, lbl=self.xaccel_label: self.update_label(value, lbl))
        self.yaccel.valueChanged.connect(lambda value, lbl=self.yaccel_label: self.update_label(value, lbl))
        self.zaccel.valueChanged.connect(lambda value, lbl=self.zaccel_label: self.update_label(value, lbl))
        self.roll.valueChanged.connect(lambda value, lbl=self.roll_label: self.update_label(value, lbl))
        self.pitch.valueChanged.connect(lambda value, lbl=self.pitch_label: self.update_label(value, lbl))
        self.yaw.valueChanged.connect(lambda value, lbl=self.yaw_label: self.update_label(value, lbl))

        # Connect button click
        self.start.clicked.connect(lambda value, command="running": self.send_command(command))
        self.stop.clicked.connect(lambda value, command="stop": self.send_command(command))
        self.reset.clicked.connect(lambda value, command="idle": self.send_command(command))

        # Start UDP Listener in a Thread
        #self.udp_thread = UDPListenerThread(udp_ip, udp_listen_port, self.update_labels)
        #self.udp_thread.start()

        self.reset_gains.clicked.connect(self.reset_sliders)

    def update_label(self, value, label):
        label.setText(f"Gain: {value/5}")

    def send_command(self, state):
        # Generate a sample 1D array of 7 integers (replace with actual data)
        data_array = np.array([self.master.value(), self.xaccel.value(), self.yaccel.value(), self.zaccel.value(), self.roll.value(), self.pitch.value(), self.yaw.value()])
        data_array = data_array/5

        # Convert array to comma-separated string
        data_str = ",".join(map(str, data_array))
        # Format the message: "command|num1,num2,num3,num4,num5,num6,num7"
        message = f"{state}|{data_str}"
        send_command(message)

    def update_labels(self, message, flag):
        """
        Updates QLabel with the received message. Called from the UDP thread.
        """
        self.SM_STATUS.setText(f"Message: {message}, Boolean: {flag}")
        
        """
        Updates Qstart color based on the received boolean value.
        """
        if flag:
            self.start.setStyleSheet("QPushButton { background-color: green; }")
            self.start.setText("START SIMULATION")
        else:
            self.start.setStyleSheet("QPushButton { background-color: red; }")
            self.start.setText("CHECK SAFETY SENSORS")

    def closeEvent(self, event):
        """Stops the UDP listener thread when closing the app."""
        self.udp_thread.stop()
        event.accept()
    
    def reset_sliders(self):
        self.master.setValue(5)
        self.xaccel.setValue(5)
        self.yaccel.setValue(5)
        self.zaccel.setValue(5)
        self.roll.setValue(5)
        self.pitch.setValue(5)
        self.yaw.setValue(5)

def send_command(command):
    if command:
        send_sock.sendto(command.encode(), (udp_ip, udp_send_port))

def listen_udp():
    """
    Listens on the given UDP port and receives a message with a boolean flag.

    :param port: The UDP port to listen on.
    :param host: The host/IP to bind to (default: "0.0.0.0" for all interfaces).
    :return: A tuple (message: str, flag: bool)
    """
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind((udp_ip, udp_send_port))

    data, addr = udp_socket.recvfrom(1024)  # Receive data (max 1024 bytes)
    message, flag = data.decode().split("|")  # Split the received string
    return message, bool(int(flag))  # Convert "1"/"0" to True/False

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec_())