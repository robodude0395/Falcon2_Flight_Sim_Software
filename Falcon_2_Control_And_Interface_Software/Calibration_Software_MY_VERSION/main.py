from common.serialProcess import SerialProcess  # Assuming your code is in a file called serialProcess.py
from fluidic_muscle import FluidicMuscle
import csv
import pandas as pd
import sys
from PyQt5.QtWidgets import QApplication
from GUI import CalibrationApp  # Assuming your GUI script is named 'calibration_tool.py'


class NewCalibrationApp(CalibrationApp):
    def __init__(self):
        # Call the parent class constructor to inherit all properties
        super().__init__()
        #Define variables
        self.ENCODER_PORT = "COM10"

        self.LOAD = 10
        self.STEP_COUNT = 30
        self.CYCLE_COUNT = 3
        self.CURRENT_CYCLE = 0
        self.DELAY_PER_STEP_MS = 10

        self.MAX_PRESSURE_MBAR = 6000
        self.PRESSURE_INCREMENT = self.MAX_PRESSURE_MBAR/self.STEP_COUNT
        self.CURRENT_PRESSURE = self.PRESSURE_INCREMENT

        self.encoder = SerialProcess()
        self.encoder.open_port(self.ENCODER_PORT)
        self.muscle = FluidicMuscle(min_extension=0, max_extension=250, load=self.LOAD, max_pressure=self.MAX_PRESSURE_MBAR)

        self.P_to_D_up_curve_table = pd.DataFrame(columns=["Pressure (mbar)", "Distance (cm)"])

        self.P_to_D_down_curve_table = pd.DataFrame(columns=["Pressure (mbar)", "Distance (cm)"])

        # Modify the Start button to have custom functionality
        self.pushButton_start.setText("Begin Calibration")
        self.pushButton_start.clicked.connect(self.on_start_button_clicked)

        self.pushButton_refresh.clicked.connect(self.refresh_COM_ports)
        
        self.spinBox_load.setValue(self.LOAD)
        self.spinBox_step_count.setValue(self.STEP_COUNT)
        self.spinBox_cycle_count.setValue(self.CYCLE_COUNT)
        self.spinBox_delay.setValue(self.DELAY_PER_STEP_MS)

        # Connect spinboxes to their respective methods to update self. variables
        self.spinBox_load.valueChanged.connect(self.update_load)
        self.spinBox_step_count.valueChanged.connect(self.update_step_count)
        self.spinBox_cycle_count.valueChanged.connect(self.update_cycle_count)
        self.spinBox_delay.valueChanged.connect(self.update_delay)
    
    def update_load(self):
        """Updates the self.LOAD variable when the spinbox value changes."""
        self.LOAD = self.spinBox_load.value()
        #print(f"LOAD updated: {self.LOAD}")

    def update_step_count(self):
        """Updates the self.STEP_COUNT variable when the spinbox value changes."""
        self.STEP_COUNT = self.spinBox_step_count.value()
        #print(f"STEP_COUNT updated: {self.STEP_COUNT}")

    def update_cycle_count(self):
        """Updates the self.CYCLE_COUNT variable when the spinbox value changes."""
        self.CYCLE_COUNT = self.spinBox_cycle_count.value()
        #print(f"CYCLE_COUNT updated: {self.CYCLE_COUNT}")

    def update_delay(self):
        """Updates the self.DELAY_PER_STEP_MS variable when the spinbox value changes."""
        self.DELAY_PER_STEP_MS = self.spinBox_delay.value()
        #print(f"DELAY_PER_STEP_MS updated: {self.DELAY_PER_STEP_MS}")

    def on_start_button_clicked(self):
        # Custom behavior for the Start button
        print("Start button pressed in new app!")

        # You can access and modify the inherited variables and methods
        print(f"Load: {self.LOAD} kg")
        print(f"Delay: {self.DELAY_PER_STEP_MS} ms")
        print(self.STEP_COUNT)
        print(f"Cycle Count: {self.CYCLE_COUNT}")
        print(f"New Setting: {self.lineEdit_output_path}")

        # Add any new functionality or logic here
        # For example, validate the inputs, start a task, or update the UI
        self.label_output_path.setText("Processing...")  # Just an example

    def refresh_COM_ports(self):
        self.comboBox_com_port.clear()
        ports = self.encoder.list_ports()
        for p in ports:
            self.comboBox_com_port.addItem(str(p.device))




    def Calibrate(self):
        #RESET PRESSURE
        #encoder.write("r")

        # Run multiple cycles
        for cycle in range(self.CYCLE_COUNT):
            print(f"Cycle {cycle + 1}/{self.CYCLE_COUNT}")

            # Increasing pressure phase
            while self.CURRENT_PRESSURE <= self.MAX_PRESSURE_MBAR:
                extension = self.muscle.apply_pressure(CURRENT_PRESSURE)

                # Add pressure-extension pair to the table
                pressure_extension_pair = {"Pressure (mbar)": CURRENT_PRESSURE, "Distance (cm)": extension}
                P_to_D_up_curve_table = pd.concat([P_to_D_up_curve_table, pd.DataFrame([pressure_extension_pair])], ignore_index=True)

                CURRENT_PRESSURE += self.PRESSURE_INCREMENT

            # Decreasing pressure phase
            self.CURRENT_PRESSURE -= self.PRESSURE_INCREMENT  # Avoid duplicate max pressure reading
            while self.CURRENT_PRESSURE > 0:
                extension = self.muscle.apply_pressure(self.CURRENT_PRESSURE)

                # Add pressure-extension pair to the table
                pressure_extension_pair = {"Pressure (mbar)": self.CURRENT_PRESSURE, "Distance (cm)": extension}
                P_to_D_down_curve_table = pd.concat([P_to_D_down_curve_table, pd.DataFrame([pressure_extension_pair])], ignore_index=True)

                self.CURRENT_PRESSURE -= self.PRESSURE_INCREMENT

        # Average the values by dividing by CYCLE_COUNT
        P_to_D_up_curve_table_avg = P_to_D_up_curve_table.groupby("Pressure (mbar)").agg({"Distance (cm)": "mean"}).reset_index()
        P_to_D_down_curve_table_avg = P_to_D_down_curve_table.groupby("Pressure (mbar)").agg({"Distance (cm)": "mean"}).reset_index()

        # Save the averaged results to CSV
        P_to_D_up_curve_table_avg.to_csv(f"{self.LOAD}kg_up_curve.csv", index=False)
        P_to_D_down_curve_table_avg.to_csv(f"{self.LOAD}kg_down_curve.csv", index=False)

if __name__ == "__main__":
    app = QApplication([])
    window = NewCalibrationApp()
    window.show()
    app.exec_()