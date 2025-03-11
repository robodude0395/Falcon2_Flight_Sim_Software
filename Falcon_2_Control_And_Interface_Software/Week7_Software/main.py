""" main.py
siminterface folder structure (tbd)
├── main.py
├── sim_interface_core.py
├── sim_interface_ui.py
├── SimpleSims/
│   ├── available_sims.py
│   └── ...
├── kinematics/
│   ├── kinematicsV2.py
│   ├── dynamics.py
│   ├── cfg_SlidingActuators.py
│   └── ...
├── output/
│   ├── d_to_p.py
│   ├── muscle_output.py
│   └── ...
├── common/
│   ├── gui_utils.py
│   └── ...
├── SimpleSims/SimInterface_H.ui
└── ...





"""
import sys
import logging as log

from PyQt5 import QtWidgets, QtCore
from siminterface_core import SimInterfaceCore
from siminterface_ui import MainWindow

def start_logging():
    log.basicConfig(
        level=log.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S"
    )

if __name__ == "__main__":
    start_logging()
    log.info("Starting SimInterface with separated UI and Core")

    app = QtWidgets.QApplication(sys.argv)

    core = SimInterfaceCore()
    window = MainWindow(core)
    window.show()

    sys.exit(app.exec_())
