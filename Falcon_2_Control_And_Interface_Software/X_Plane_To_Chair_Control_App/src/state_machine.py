import keyboard
import time
import socket
import struct
import select
import numpy as np
from udp_tx_rx import UdpReceive, UdpSend

#This code performs the bulk of the underlying logic within the software. It's mainly in charge of getting the airplane's telemetry as linear 
#acceleration and rotational pose values and working out the inverse kinematics for the mechanical chair to send to via UDP

#Define IP address and port numbers to receive and send data to other nodes in network
UDP_IP = "127.0.0.1"  # Change if needed
SAFE_STATE_UDP_PORT = 4005
TELEMETRY_UDP_PORT = 10022
CMD_UDP_PORT = 6005
STATUS_UDP_PORT = 7005
#POSE_DISPLAY_PORT = 8005
POSE_DISPLAY_PORT = 10020
MANUAL_POSE_UDP_PORT = 9005

#Define how frequently the state machine updates and performs operations. This includes rate at which pose commands are updated in machanical chair
CYCLE_TIME = 1/100 #20 cycles per second

#Define listener UDP objects
safe_state_listener = UdpReceive(SAFE_STATE_UDP_PORT)
telemetry_listener = UdpReceive(TELEMETRY_UDP_PORT)
manual_telemetry_listener = UdpReceive(MANUAL_POSE_UDP_PORT)
command_listener = UdpReceive(CMD_UDP_PORT)

#Define sender UDP objects
display_sender = UdpSend()
status_sender = UdpSend()


#Define global variables. Reason for global variables is to retain previous variable value if no udp messages are available
global values
values = "0,0,0,0,0,0,0,0"

global user_command
user_command = ""

global user_gains
user_gains = []

global safe_state
safe_state = False

#Blank class definition for a state which the state machine can have. The reason for other states inheriting from this class is to better improve
#maintainability within the system.
class State:
    def __init__(self):
        pass

    #This part defines what each state executes each cycle
    def execute(self):
        pass

#The IDLE state does nothing until the chais is in it's safe state and there's available airplane telemetry
class IDLE(State):
    def execute(self):
        global safe_state
        if(safe_state):
            return "ready"
            
#The READY state wait's until the user either commands to go to the manual or running state. If the chair is not it's safe state, it transitions
#back to the IDLE state
class READY(State):
    def execute(self):
        global safe_state
        global user_command
        if(safe_state == False):
            return "idle"
        elif(user_command == "manual"):
            return "manual"
        elif(user_command == "running"):
            return "running"

#The RUNNING state (for now) sends the pose values from the airplane telemetry port to the stewart display. NOTE: In future versions the code will 
#work out the chair's inverse kinematics and send them instead of the target pose values after multiplying them by their gains.
#In this state, the machine will transition to the stop state if either the operator commands to transition to the idle state or the chair is not
#on it's safe state
class RUNNING(State):
    def execute(self):
        global safe_state
        global user_command
        global values
        if(safe_state != True or user_command == "stop"):
            return "stop"
        else:
            #display_sender.send("request, 0,0,0,0.17,-0.17,0", (UDP_IP, POSE_DISPLAY_PORT))
            display_sender.send(values, (UDP_IP, POSE_DISPLAY_PORT))

#The STOP state waits until the operator commands it to go back to the idle state and the chair is in it's safe state
class STOP(State):
    def execute(self):
        global safe_state
        global user_command
        if(safe_state and user_command == "idle"):
            return "idle"

#In this state the machine sends udp data from the operators's manual input to the chair instead. This allows the operator to manually control 
#the chair. The operator can transition back to the ready state is requested.
class MANUAL_CONTROL(State):
    def execute(self):
        global user_command
        if(user_command == "ready"):
            return "ready"
        else:
            pass
            #send_udp_data(values)

#Class definition for the state machine. This machine will execute one state at a time and may transition between states when the current state 
#returns a desired transition as a string variable.
class StateMachine:
    def __init__(self):
        self.state = None
    
    #Sets current state of machine to passed state
    def set_state(self, state: State):
        self.state = state
        print(f"State changed to {self.GetCurrentState()}")
    
    #This executes the machine's current state and checks for transitions to go to depending if a state returned a given transition
    def execute(self):
        if self.state:
            #Execute current state
            transition = self.state.execute()

            #Handle state transitions
            if(transition == "idle"):
                self.set_state(IDLE())
            if(transition == "ready"):
                self.set_state(READY())
            if(transition == "running"):
                self.set_state(RUNNING())
            if(transition == "stop"):
                self.set_state(STOP())
            if(transition == "manual"):
                self.set_state(MANUAL_CONTROL())

        else:
            print("No state set")

    #Returns function name of current state    
    def GetCurrentState(self):
        return self.state.__class__.__name__

#Initialize the state machine and run it until the user pressed "q".
if __name__ == "__main__":
    sm = StateMachine()
    sm.set_state(IDLE())

    #Define current time as target time
    target_time = time.time()

    #MAIN LOOP
    while not keyboard.is_pressed("q"):
        current_time = time.time()

        #Section limits state machine update cycle to 20 cycles per second. Ensures execution only happens every "CYCLE_TIME" seconds by comparing
        #times instead of using time.sleep(CYCLE_TIME). Reason for this approach is because this allows any other processes within this node to
        #be executed.
        if current_time >= target_time:
            #current_airplane telemetry = ["x_accel", "y_accel", "z_accel", "roll_rate", "pitch_rate", "yaw_rate", "bank_angle", "pitch_angle"]

            #This way DOES NOT GET LATEST MESSAGE, might come back to bite in the rear later on
            temp_values = telemetry_listener.get()
            if(temp_values != None):
                values = temp_values[1].split(",", 1)[1] #remove first value which is "xplane_telemetry" (useless for software)

            temp_safe_state = safe_state_listener.get()
            if(temp_safe_state != None):
                safe_state = int(temp_safe_state[1])

            cmd_message = command_listener.get()

            if(cmd_message != None):
                user_command, user_gains = cmd_message[1].split("|")
                user_gains = user_gains.split(",")

            else:
                user_command = None
            
            status = (str(sm.GetCurrentState())+"|"+str(safe_state))
            status_sender.send(status, (UDP_IP, STATUS_UDP_PORT))

            sm.execute()
            target_time = current_time + CYCLE_TIME