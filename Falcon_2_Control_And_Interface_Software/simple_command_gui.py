import sys
import socket
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLineEdit, QLabel

class UDPCommandSender(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()

        # Set up UDP socket
        self.udp_ip = "127.0.0.1"  # Same as the UDP listener
        self.udp_port = 6005  # Must match the listener's port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def initUI(self):
        self.setWindowTitle("UDP Command Sender")
        self.setGeometry(100, 100, 300, 150)

        self.layout = QVBoxLayout()

        self.label = QLabel("Enter Command:")
        self.layout.addWidget(self.label)

        self.command_input = QLineEdit()
        self.layout.addWidget(self.command_input)

        self.send_button = QPushButton("Send Command")
        self.send_button.clicked.connect(self.send_command)
        self.layout.addWidget(self.send_button)

        self.command_input.returnPressed.connect(self.send_command)

        self.setLayout(self.layout)

    def send_command(self):
        command = self.command_input.text().strip()
        if command:
            self.sock.sendto(command.encode(), (self.udp_ip, self.udp_port))
            self.command_input.clear()  # Clear the input field

if __name__ == "__main__":
    app = QApplication(sys.argv)
    sender = UDPCommandSender()
    sender.show()
    sys.exit(app.exec_())