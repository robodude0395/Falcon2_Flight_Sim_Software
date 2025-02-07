import keyboard
import time
import socket
import struct
import select
import numpy as np

UDP_IP = "127.0.0.1"  # Change if needed
TELEMETRY_UDP_PORT = 5005
CMD_UDP_PORT = 6005
STATUS_UDP_PORT = 7005
POSE_DISPLAY_PORT = 8005
CYCLE_TIME = 1/100 #20 cycles per second

sock_telemetry = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock_telemetry.bind((UDP_IP, TELEMETRY_UDP_PORT))
sock_telemetry.setblocking(False)

sock_display = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

global user_command
user_command = ""

global user_gains
user_gains = []

global safe
safe = False

def send_udp_data(values):
        data = list(values) + [None]
        packed_data = struct.pack("6f?", *data)
        sock_display.sendto(packed_data, (UDP_IP, POSE_DISPLAY_PORT))

class UDPCommandListener:
    def __init__(self, ip=UDP_IP, port=CMD_UDP_PORT):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((ip, port))
        self.sock.setblocking(False)  # Non-blocking mode

    def listen_for_command(self):
        try:
            data, _ = self.sock.recvfrom(1024)  # Receive up to 1024 bytes
            decoded_data = data.decode().strip()  # Decode and remove extra spaces/newlines
            command, gains_str = decoded_data.split('|')
            gains =  [float(x) for x in gains_str.split(',')]
            return command, gains
        except BlockingIOError:
            return None, user_gains  # No command received

class State:
    def __init__(self):
        pass

    #This part defines what each state executes each cycle
    def execute(self, ready, values, safe):
        pass

class IDLE(State):
    def execute(self, ready, values, safe):
        super().execute(ready, values, safe)

        if(ready and safe):
                return "ready"
            

class READY(State):
    def execute(self, ready, values, safe):
        super().execute(ready, values, safe)
        if(safe == False):
            return "idle"
        elif(user_command == "manual"):
            return "manual"
        elif(user_command == "running"):
            return "running"

class RUNNING(State):
    def execute(self, ready, values, safe):
        super().execute(ready, values, safe)
        if(safe != True or user_command == "stop"):
            return "stop"
        else:
            send_udp_data(((np.array(values)*np.array(user_gains)[-6:])*user_gains[0]).tolist())


class STOP(State):
    def execute(self, ready, values, safe):
        super().execute(ready, values, safe)
        if(safe and user_command == "idle"):
            return "idle"

class MANUAL_CONTROL(State):
    def execute(self, ready, values, safe):
        if(user_command == "ready"):
            return "ready"

class StateMachine:
    def __init__(self):
        self.state = None
        self.ready = False
        self.values = [0,0,0,0,0,0]
        self.safe = True #Potential bug WARNING. When initialized to False, it will cause an alternating effect between idle and ready states!
    
    def listen_for_telemetry(self):
        self.ready, _, _ = select.select([sock_telemetry], [], [], 0)

        if self.ready:
            data, addr = sock_telemetry.recvfrom(1024)
            unpacked_values = struct.unpack("6f?", data)
            self.values = unpacked_values[:6]
            self.safe = unpacked_values[6]
            #print("Received: ", self.values)
        else:
            #print("No telemetry available")
            pass
    
    def set_state(self, state: State):
        self.state = state
        print(f"State changed to {self.state.__class__.__name__}")
    
    def execute(self):
        if self.state:
            #Execute current state
            transition = self.state.execute(self.ready, self.values, self.safe)
            self.listen_for_telemetry()

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
            
            self.send_udp_data(UDP_IP, STATUS_UDP_PORT, self.GetCurrentState(), self.safe)

        else:
            print("No state set")
        
    def GetCurrentState(self):
        return self.state.__class__.__name__
    def GetSafe(self):
        return self.sa

    def send_udp_data(self, host: str, port: int, message: str, flag: bool):
        """
        Sends a UDP packet with a string message and a boolean flag.

        :param host: Target IP address or hostname.
        :param port: Target UDP port.
        :param message: The string message to send.
        :param flag: Boolean flag (True/False).
        """
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Convert boolean to string and format message
        data = f"{message}|{int(flag)}"  # "message|1" for True, "message|0" for False

        # Send data
        udp_socket.sendto(data.encode(), (host, port))
        udp_socket.close()

# Example usage
if __name__ == "__main__":
    sm = StateMachine()
    sm.set_state(IDLE())

    target_time = time.time()

    command_listener = UDPCommandListener()

    #MAIN LOOP
    while not keyboard.is_pressed("q"):
        current_time = time.time()

        #Section limits state machine update cycle to 20 cycles per second.
        if current_time >= target_time:
            user_command, user_gains = command_listener.listen_for_command()
            sm.execute()
            target_time = current_time + CYCLE_TIME