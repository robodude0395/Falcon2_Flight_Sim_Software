from common.serialProcess import SerialProcess  # Assuming your code is in a file called serialProcess.py
from fluidic_muscle import FluidicMuscle
import csv
import pandas as pd
import sys
from PyQt5.QtWidgets import QApplication
from GUI import CalibrationApp  # Assuming your GUI script is named 'calibration_tool.py'
import os
from platform_pose import Platform
import time

class NewCalibrationApp(CalibrationApp):
    def __init__(self):
        # Call the parent class constructor to inherit all properties
        super().__init__()

        self.LOAD = 10
        self.STEP_COUNT = 30
        self.CYCLE_COUNT = 1
        self.CURRENT_CYCLE = 0
        self.DELAY_PER_STEP_MS = 500

        self.MAX_PRESSURE_MBAR = 6000
        self.PRESSURE_INCREMENT = self.MAX_PRESSURE_MBAR/self.STEP_COUNT
        self.CURRENT_PRESSURE = self.PRESSURE_INCREMENT

        self.encoder = SerialProcess()
        self.platform = Platform()

        self.P_to_D_up_curve_table = pd.DataFrame(columns=["Pressure (mbar)", "Distance (cm)", "Load(kg)"])

        self.P_to_D_down_curve_table = pd.DataFrame(columns=["Pressure (mbar)", "Distance (cm)", "Load(kg)"])

        # Modify the Start button to have custom functionality
        self.pushButton_start.setText("Begin Calibration")
        self.pushButton_start.clicked.connect(self.on_start_button_clicked)

        self.refresh_COM_ports()
        self.pushButton_refresh.clicked.connect(self.refresh_COM_ports)
        
        #self.spinBox_load.setValue(self.LOAD)
        self.spinBox_step_count.setValue(self.STEP_COUNT)
        self.spinBox_cycle_count.setValue(self.CYCLE_COUNT)
        self.spinBox_delay.setValue(self.DELAY_PER_STEP_MS)

        # Connect spinboxes to their respective methods to update self. variables
        #self.spinBox_load.valueChanged.connect(self.update_load)
        self.spinBox_step_count.valueChanged.connect(self.update_step_count)
        self.spinBox_cycle_count.valueChanged.connect(self.update_cycle_count)
        self.spinBox_delay.valueChanged.connect(self.update_delay)

        self.lineEdit_output_path.setText(os.getcwd())
    
    def update_load(self):
        """Updates the self.LOAD variable when the spinbox value changes."""
        self.LOAD = self.spinBox_load.value()
        #print(f"LOAD updated: {self.LOAD}")

    def update_step_count(self):
        """Updates the self.STEP_COUNT variable when the spinbox value changes."""
        self.STEP_COUNT = self.spinBox_step_count.value()
        self.PRESSURE_INCREMENT = self.MAX_PRESSURE_MBAR/self.STEP_COUNT
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
        print(f"Step Count: {self.STEP_COUNT}")
        print(f"Cycle Count: {self.CYCLE_COUNT}")
        print(f"New Setting: {self.lineEdit_output_path}")

        # Add any new functionality or logic here
        # For example, validate the inputs, start a task, or update the UI
        self.label_output_path.setText("Processing...")  # Just an example

        port = self.comboBox_com_port.currentText()
        if(port != None):
            print(port)
            self.encoder.open_port(port, 115200)
            time.sleep(0.1) #Wait a little bit for queue to fill up
            self.encoder.write("R".encode())
            _, load = self.GetDistanceAndLoad()
            self.LOAD = round(load)
            print(load)

        self.Calibrate()

    def refresh_COM_ports(self):
        self.comboBox_com_port.clear()
        ports = self.encoder.list_ports()
        for p in ports:
            self.comboBox_com_port.addItem(str(p.device))

    def Calibrate(self):
        # Run multiple cycles
        for cycle in range(self.CYCLE_COUNT):
            self.CURRENT_PRESSURE = self.PRESSURE_INCREMENT
            time.sleep(self.DELAY_PER_STEP_MS/1000)

            print(f"Cycle {cycle + 1}/{self.CYCLE_COUNT}")

            # Increasing pressure phase
            while self.CURRENT_PRESSURE <= self.MAX_PRESSURE_MBAR:
                time.sleep(self.DELAY_PER_STEP_MS/1000)
                extension, load = self.GetDistanceAndLoad()

                # Add pressure-extension pair to the table
                pressure_extension_pair = {"Pressure (mbar)": self.CURRENT_PRESSURE, "Distance (cm)": extension, "Load(kg)": load}
                self.P_to_D_up_curve_table = pd.concat([self.P_to_D_up_curve_table, pd.DataFrame([pressure_extension_pair])], ignore_index=True)
                self.platform.muscle.send_pressures([int(self.CURRENT_PRESSURE),0,0,0,0,0])

                print(load, " ", extension)

                self.CURRENT_PRESSURE += self.PRESSURE_INCREMENT
            
            # Decreasing pressure phase
            self.CURRENT_PRESSURE -= self.PRESSURE_INCREMENT  # Avoid duplicate max pressure reading
            while self.CURRENT_PRESSURE >= self.PRESSURE_INCREMENT:
                time.sleep(self.DELAY_PER_STEP_MS/1000)
                extension, load = self.GetDistanceAndLoad()

                # Add pressure-extension pair to the table
                pressure_extension_pair = {"Pressure (mbar)": self.CURRENT_PRESSURE, "Distance (cm)": extension, "Load(kg)": load}
                self.P_to_D_down_curve_table = pd.concat([self.P_to_D_down_curve_table, pd.DataFrame([pressure_extension_pair])], ignore_index=True)
                self.platform.muscle.send_pressures([int(self.CURRENT_PRESSURE),0,0,0,0,0])

                print(load, " ", extension)

                self.CURRENT_PRESSURE -= self.PRESSURE_INCREMENT

        print(self.P_to_D_down_curve_table)

        # Average the values by dividing by CYCLE_COUNT
        P_to_D_up_curve_table_avg = self.P_to_D_up_curve_table.groupby("Pressure (mbar)").agg({"Distance (cm)": "mean", "Load(kg)": "mean"}).reset_index()
        P_to_D_down_curve_table_avg = self.P_to_D_down_curve_table.groupby("Pressure (mbar)").agg({"Distance (cm)": "mean", "Load(kg)": "mean"}).reset_index()

        # Save the averaged results to CSV
        P_to_D_up_curve_table_avg.to_csv(f"{self.lineEdit_output_path.text()}/{self.LOAD}kg_up_curve.csv", index=False)
        P_to_D_down_curve_table_avg.to_csv(f"{self.lineEdit_output_path.text()}/{self.LOAD}kg_down_curve.csv", index=False)

    def GetDistanceAndLoad(self):
        data = self.encoder.read()
        if(data == None):
            return None
        array = data.split(",")  # Convert string to a list

        # Extract 2nd and 5th values as integers (index 1 and 4)
        result = (-float(array[1]), float(array[3])/9.81)

        return result

if __name__ == "__main__":
    app = QApplication([])
    window = NewCalibrationApp()
    window.show()
    app.exec_()