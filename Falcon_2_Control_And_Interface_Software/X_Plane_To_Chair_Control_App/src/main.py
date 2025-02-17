from PyQt5 import QtWidgets
from gui import Ui_MainWindow  # Import your generated UI class
from PyQt5.QtCore import QThread
import sys
import socket
import threading
import numpy as np
import struct
import time
from udp_tx_rx import UdpReceive, UdpSend

# Set up UDP ports to receive and send data
UDP_IP = "127.0.0.1"  # Same as the UDP listener
CMD_UDP_PORT = 6005 
STATUS_UDP_PORT = 7005
MANUAL_POSE_UDP_PORT = 9005

class SM_Status_QThread(QThread):
    def __init__(self, callback, udp_object):
        super().__init__()
        self.callback = callback  # Store the callback function
        self.isRunning = True  # Control flag
        self.UdpListener = udp_object

    def run(self):
        while(self.isRunning):
            self.callback(self.UdpListener.get())

    def stop(self):
        """Stop the thread"""
        self.isRunning = False
        self.quit()
        self.wait()

#This is the class definition for the main app. The GUI is designed in Qt designer and exported into gui.py. This class inherits from the gui.py class
#to add extra functionality and features required for the app to actually function as intended. Ui_MainWindow is imported from gui.py
class MainApp(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)  # Load the UI

        self.cmd_sender = UdpSend()
        self.manual_pose_sender = UdpSend()
        self.status_receiver = UdpReceive(STATUS_UDP_PORT, blocking=False)

        self.worker = None

        """Start worker thread with a callback"""
        if self.worker is None or not self.worker.isRunning:
            self.worker = SM_Status_QThread(self.update_status_label, self.status_receiver)  # Pass callback function
            self.worker.start()

        # Connect slider signals to labels
        self.master.valueChanged.connect(lambda value, lbl=self.master_label, mode="sim_gains": self.update_label(value, lbl, mode))
        self.xaccel.valueChanged.connect(lambda value, lbl=self.xaccel_label, mode="sim_gains": self.update_label(value, lbl, mode))
        self.yaccel.valueChanged.connect(lambda value, lbl=self.yaccel_label, mode="sim_gains": self.update_label(value, lbl, mode))
        self.zaccel.valueChanged.connect(lambda value, lbl=self.zaccel_label, mode="sim_gains": self.update_label(value, lbl, mode))
        self.roll.valueChanged.connect(lambda value, lbl=self.roll_label, mode="sim_gains": self.update_label(value, lbl, mode))
        self.pitch.valueChanged.connect(lambda value, lbl=self.pitch_label, mode="sim_gains": self.update_label(value, lbl, mode))
        self.yaw.valueChanged.connect(lambda value, lbl=self.yaw_label, mode="sim_gains": self.update_label(value, lbl, mode))

        self.xaccel_manual.valueChanged.connect(lambda value, lbl=self.xaccel_label_2, mode="manual_gains": self.update_label(value, lbl, mode))
        self.yaccel_manual.valueChanged.connect(lambda value, lbl=self.yaccel_label_2, mode="manual_gains": self.update_label(value, lbl, mode))
        self.zaccel_manual.valueChanged.connect(lambda value, lbl=self.zaccel_label_2, mode="manual_gains": self.update_label(value, lbl, mode))
        self.roll_manual.valueChanged.connect(lambda value, lbl=self.roll_label_2, mode="manual_gains": self.update_label(value, lbl, mode))
        self.pitch_manual.valueChanged.connect(lambda value, lbl=self.pitch_label_2, mode="manual_gains": self.update_label(value, lbl, mode))
        self.yaw_manual.valueChanged.connect(lambda value, lbl=self.yaw_label_2, mode="manual_gains": self.update_label(value, lbl, mode))

        # Connect button clicks to send out the desired commands to state_machine.py
        #start button request state_machine.py to transition to the RUNNING state
        self.start.clicked.connect(lambda value, command="running": self.send_control_command(command)) 

        #stop button request state_machine.py to transition to the stop state
        self.stop.clicked.connect(lambda value, command="stop": self.send_control_command(command))

        #reset button resets the gains to their default value
        self.reset.clicked.connect(lambda value, command="idle": self.send_control_command(command))

        #manual_mode button request state_machine.py to transition to the MANUAL_CONTROL state
        self.manual_mode_button.clicked.connect(lambda value, command="manual": self.send_control_command(command))

        #READY button request state_machine.py to transition to the READY state
        self.simulation_mode_button.clicked.connect(lambda value, command="ready": self.send_control_command(command))

        #Set up the reset_gains and reset_gain_manual button to reset all the sliders to their default values. All the sliders have a scale of 0 to 10
        self.reset_gains.clicked.connect(self.reset_sliders)
        self.reset_gain_manual.clicked.connect(self.reset_sliders)

        #Ensure the main tab is the first one which presents the operator with the main options. The second tab is for manual chair control
        self.tabWidget.setCurrentIndex(0)
        self.tabWidget.tabBar().hide()

    #This method updates a given label parameter to a vale parameter. The mode determines the scaling type since manual and simulation modes have
    #different scaling methods (these methods are completely arbitrary)
    def update_label(self, value, label, mode):
        if(mode == "sim_gains"):
            label.setText(f"Gain: {value/5}")

        if(mode == "manual_gains"):
            label.setText(f"Gain: {(value*20)-100}")

    
    #This method sends a control command. A control command is an array compossed of desired transition and individual gain parameters
    def send_control_command(self, state):
        # Generate a sample 1D array of 7 integers (replace with actual data)
        data_array = np.array([self.master.value(), self.xaccel.value(), self.yaccel.value(), self.zaccel.value(), 
                               self.roll.value(), self.pitch.value(), self.yaw.value()])
        data_array = data_array/5

        # Convert array to comma-separated string
        data_str = ",".join(map(str, data_array))
        # Format the message: "command|num1,num2,num3,num4,num5,num6,num7"
        message = f"{state}|{data_str}"
        print(message)
        self.cmd_sender.send(message, (UDP_IP, CMD_UDP_PORT))

    #This method updates a status label to inform the operator which state the state_machine.py node is in and whether the state_machine.py is safe.
    #This method also changes the text of the start button based on state_machine.py's safe state and handles GUI transition to manual control tab
    #based on state_machine.py's current state
    def update_status_label(self, data):
        if(data == None):
            return 1
        
        message, flag = data[1].split("|")

        self.SM_STATUS.setText(f"Message: {message}, Boolean: {flag}")

        """
        Updates Qstart color based on the received boolean value.
        """
        if flag:
            #self.start.setStyleSheet("QPushButton { background-color: green; }")
            self.start.setText("START SIMULATION")
        else:
            #self.start.setStyleSheet("QPushButton { background-color: red; }")
            self.start.setText("CHECK SAFETY SENSORS")

        if(message == "MANUAL_CONTROL"):
            self.tabWidget.setCurrentIndex(1)
        else:
            self.tabWidget.setCurrentIndex(0)
        
    #When the window is closed, it'll stop all the started up threads.
    def closeEvent(self, event):
        """Stops the UDP listener thread when closing the app."""
        #No shid atm
        pass
    
    #Reset all the sliders to their default "middle" values. 5 is the middle value in a slider of 0 to 10
    def reset_sliders(self):
        self.master.setValue(5)
        self.xaccel.setValue(5)
        self.yaccel.setValue(5)
        self.zaccel.setValue(5)
        self.roll.setValue(5)
        self.pitch.setValue(5)
        self.yaw.setValue(5)

        self.xaccel_manual.setValue(5)
        self.yaccel_manual.setValue(5)
        self.zaccel_manual.setValue(5)
        self.roll_manual.setValue(5)
        self.pitch_manual.setValue(5)
        self.yaw_manual.setValue(5)

#Initialize node when called in terminal
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec_())