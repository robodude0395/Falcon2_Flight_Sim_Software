from sim_config import selected_sim, platform_config
from kinematics.kinematicsV2 import Kinematics
from kinematics.dynamics import Dynamics
import output.d_to_p as d_to_p
from output.muscle_output import MuscleOutput
from sims.TestSim import Sim as TestSim
import importlib
import time
from udp_tx_rx import UdpReceive, UdpSend
import math
from platform_kinematics_module import PoseToDistances
import numpy as np

class Platform():
    def __init__(self):
        self.DtoP = d_to_p.D_to_P(200)
        # platform configuration path (platform_config) is defined in sim_config.py
        self.pose_to_distances = PoseToDistances() 
        self.cfg = self.pose_to_distances.cfg
        self.DtoP.load(self.cfg.DISTANCE_TO_PRESSURE_TABLE)
        self.muscle = MuscleOutput(self.DtoP.distance_to_pressure, None, "192.168.0.10")

    def set_pose(self, values):
        #Limits are: (100, 122, 140, math.radians(15), math.radians(20), math.radians(12))
        ik_distances = self.pose_to_distances.move_platform(values)
        self.muscle.move_distance(ik_distances)
        

'''
UDP_IP = "127.0.0.1"  # Change if needed
TELEMETRY_UDP_PORT = 5005

CYCLE_TIME_MS = 50

target_time = 0

telemetry_listener = UdpReceive(TELEMETRY_UDP_PORT)

global values
values = [0,0,0,0,0,0]
'''


'''
platform = Platform()

while True:
    current_time = time.time()

    if(current_time >= target_time):
        #This way DOES NOT GET LATEST MESSAGE, might come back to bite in the rear later on (it did)
        temp_values = []
        while(telemetry_listener.available() > 0):
            temp_values = telemetry_listener.get()

        if(len(temp_values) != 0):
            values = temp_values[1].split(",", 1)[1] #remove first value which is "xplane_telemetry" (useless for software)
            values = [float(int(num)) for num in values.split(",")]
            # Convert RPY (last three elements) to radians
            values[3:] = np.radians(values[3:])

            platform.set_pose(values)

        target_time = current_time + CYCLE_TIME_MS/1000
'''