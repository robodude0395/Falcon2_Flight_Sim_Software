from platform_pose import Platform
import time
import numpy as np

target_time = 0

global values
values = [0,0,0,0,0,0]

CYCLE_TIME_MS = 50

platform = Platform()

while True:
    current_time = time.time()

    if(current_time >= target_time):
        platform.muscle.send_pressures(values)
    
        target_time = current_time + CYCLE_TIME_MS/1000
