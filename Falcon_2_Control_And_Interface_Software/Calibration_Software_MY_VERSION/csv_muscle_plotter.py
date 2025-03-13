import sys
import os
import pandas as pd
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QLabel

class CSVPlotter(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        
        self.label = QLabel("Select a CSV file or folder")
        layout.addWidget(self.label)
        
        self.btn_browse = QPushButton("Browse", self)
        self.btn_browse.clicked.connect(self.browse)
        layout.addWidget(self.btn_browse)
        
        self.btn_plot = QPushButton("Plot", self)
        self.btn_plot.clicked.connect(self.plot_data)
        layout.addWidget(self.btn_plot)
        
        self.setLayout(layout)
        self.setWindowTitle("CSV Data Plotter")
        self.setGeometry(200, 200, 400, 200)
        
        self.file_paths = []  # Stores selected file(s)

    def browse(self):
        options = QFileDialog.Options()
        path = QFileDialog.getExistingDirectory(self, "Select Folder", "", options=options)
        
        if path:  # If a folder is selected
            self.file_paths = self.find_csv_files(path)
            self.label.setText(f"Selected Folder: {path}")
        else:  # If a file is selected
            file_path, _ = QFileDialog.getOpenFileName(self, "Select CSV File", "", "CSV Files (*.csv)", options=options)
            if file_path:
                self.file_paths = self.find_csv_pairs(file_path)
                self.label.setText(f"Selected File: {file_path}")

    def find_csv_files(self, folder_path):
        """Find all valid CSV files in the folder."""
        csv_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith(".csv")]
        return csv_files

    def find_csv_pairs(self, file_path):
        """Find the corresponding up/down curve pair if a single file is selected."""
        base_name = os.path.basename(file_path)
        folder = os.path.dirname(file_path)
        
        if "up_curve" in base_name:
            paired_file = base_name.replace("up_curve", "down_curve")
        elif "down_curve" in base_name:
            paired_file = base_name.replace("down_curve", "up_curve")
        else:
            return [file_path]
        
        paired_path = os.path.join(folder, paired_file)
        return [file_path, paired_path] if os.path.exists(paired_path) else [file_path]

    def plot_data(self):
        if not self.file_paths:
            self.label.setText("No valid CSV files selected!")
            return
        
        plt.figure()

        # Create figure and axis for the plot
        fig, ax1 = plt.subplots(figsize=(10, 6))

        # Loop through selected files (up_curve and down_curve pairs)
        for file in self.file_paths:
            try:
                df = pd.read_csv(file)
                
                # Plot Pressure vs Distance (up and down curves) on the left y-axis
                ax1.set_xlabel("Pressure (mbar)")
                ax1.set_ylabel("Distance (cm)", color="tab:blue")
                ax1.plot(df["Pressure (mbar)"], df["Distance (cm)"], label=f"Distance - {os.path.basename(file)}", marker="o", linestyle="-" if "up_curve" in os.path.basename(file) else "--", color="tab:blue")
                ax1.tick_params(axis="y", labelcolor="tab:blue")

                # Create the second y-axis for Load (kg)
                ax2 = ax1.twinx()
                ax2.set_ylabel("Load (kg)", color="tab:red")
                ax2.plot(df["Pressure (mbar)"], df["Load(kg)"], label=f"Load - {os.path.basename(file)}", marker="x", linestyle="-" if "up_curve" in os.path.basename(file) else "--", color="tab:red")
                ax2.tick_params(axis="y", labelcolor="tab:red")

            except Exception as e:
                print(f"Error reading {file}: {e}")

        # Add title and legends
        ax1.set_title("Pressure vs Distance and Load (Up and Down Curves)")
        ax1.legend(loc="upper left")
        ax2.legend(loc="upper right")

        # Show grid for better readability
        ax1.grid(True)

        # Show the plot
        plt.tight_layout()  # Adjust layout to prevent overlap
        plt.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CSVPlotter()
    window.show()
    sys.exit(app.exec_())
