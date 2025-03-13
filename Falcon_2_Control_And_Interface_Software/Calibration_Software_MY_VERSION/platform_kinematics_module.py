import os
import sys
import math
import traceback
import logging
import importlib

from sim_config import selected_sim, platform_config
from kinematics.kinematicsV2 import Kinematics
from kinematics.dynamics import Dynamics
import output.d_to_p as d_to_p
from output.muscle_output import MuscleOutput
from sims.TestSim import Sim as TestSim

#Applies IK of chair to get muscle distances
#Additionally applies can apply gains to input telemetry
class PoseToDistances:
    def __init__(self):
        #Define kinematics module
        self.k = Kinematics()
        
        #Get platform configuration
        self.cfg = importlib.import_module(platform_config).PlatformConfig()
        self.cfg.calculate_coords()

        self.k.set_geometry(self.cfg.BASE_POS, self.cfg.PLATFORM_POS)

        # Default transforms
        self.transform = [0, 0, -1, 0, 0, 0]
        self.prev_distances = [0]*6

        self.k.set_platform_params(
                self.cfg.MIN_ACTUATOR_LEN,
                self.cfg.MAX_ACTUATOR_LEN,
                self.cfg.FIXED_LEN)
        
        self.invert_axis = self.cfg.INVERT_AXIS
        self.swap_roll_pitch = self.cfg.SWAP_ROLL_PITCH

        self.dynam = Dynamics()
        self.dynam.begin(self.cfg.limits_1dof, "shape.cfg")

        self.gains = [1.0]*6
        self.master_gain = 1.0

    def move_platform(self, transform):
        """
        Convert transform to muscle moves.
        """
        # apply inversion
        transform = [inv * axis for inv, axis in zip(self.invert_axis, transform)]

        distances = self.k.actuator_lengths(transform)

        return distances

        # Optionally echo or broadcast:
        # self.echo(request, distances, self.k.get_pose())

    def apply_gains(self, transform):
        """
        Periodically called to read from sim and move platform if enabled.
        """

        for idx in range(6): 
            gain = self.gains[idx] * self.master_gain
            transform[idx] = transform[idx] * gain

        return transform

pose_distance_converter = PoseToDistances()

#NOTE TO SELF: Use normalized values instead of raw values

#How to apply pose_distance_converted gains
#pose_distance_converter.master_gain = 2
#pose_distance_converter.gains = [0.3,1,1,1,1,1]

#telemetry = pose_distance_converter.apply_gains([100,0,0,0,0,0])
#print("Input Telemetry: ", telemetry)

#print("Muscle Distances: ",pose_distance_converter.move_platform(telemetry))