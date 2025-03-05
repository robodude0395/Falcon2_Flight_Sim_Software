# list of sim name and paths for SimInterface platform controller
# sim module is the name of the python module defining the desired Sim class
# a jpg file with the same name as the module will be displayed when selected 

import os

default_sim = 6 # combo box will be set the this value at startup

# Desktop = r"C:/Users/memar/Desktop/Vr/" # location of startup icons (usually C:/Users/name/Desktop/ )
# Desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop') + '/Vr/'
Desktop = 'Sim Loading not supporteed in this version '
print(Desktop)

available_sims = [ #display name, itf module, image, full path to execute to load sim
                    ["MS FS2020", "fs2020", "fs2020.jpg", "Tools/fsdevmodelauncher.exe"],
                    ["X-Plane 11", "xplane_nasa", "xplane11.jpg", Desktop + "X-Plane11.lnk"],
                    ["X-Plane 12", "xplane", "xplane12.jpg", Desktop + "X-Plane12.lnk"] ,                     
                    ["Space Coaster", "spacecoaster", "spacecoaster.jpg", Desktop + "SpaceCoaster.lnk"],
                    ["NoLimits2 Coaster", "nolimits2", "nolimits2.jpg", Desktop + "NoLimits 2.lnk"],
                    ["DCS", "dcs", "dcs.jpg", Desktop + "DCS World.lnk"],
                    ["Test Sim", "TestSim", "test sim.jpg",  None]
                    # add another sim here
                    ]