from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QSpinBox, QLineEdit, QComboBox, QPushButton, QFileDialog
import sys

class CalibrationApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # Window Setup
        self.setWindowTitle("Calibration Tool")
        self.setGeometry(100, 100, 800, 300)

        # Central Widget
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        # Layout
        layout = QVBoxLayout(self.central_widget)

        # Load input
        self.label_load = QLabel("Load (kg):", self)
        layout.addWidget(self.label_load)
        self.spinBox_load = QSpinBox(self)
        self.spinBox_load.setRange(0, 1000)  # Min 0, Max 1000
        layout.addWidget(self.spinBox_load)

        # Delay input
        self.label_delay = QLabel("Delay per step (ms):", self)
        layout.addWidget(self.label_delay)
        self.spinBox_delay = QSpinBox(self)
        self.spinBox_delay.setRange(0, 10000)  # Min 0, Max 10000
        layout.addWidget(self.spinBox_delay)

        # Step count input
        self.label_step_count = QLabel("Step count:", self)
        layout.addWidget(self.label_step_count)
        self.spinBox_step_count = QSpinBox(self)
        self.spinBox_step_count.setRange(1, 10000)  # Min 1, Max 10000
        layout.addWidget(self.spinBox_step_count)

        # Cycle count input
        self.label_cycle_count = QLabel("Cycle count:", self)
        layout.addWidget(self.label_cycle_count)
        self.spinBox_cycle_count = QSpinBox(self)
        self.spinBox_cycle_count.setRange(1, 100)  # Min 1, Max 100
        layout.addWidget(self.spinBox_cycle_count)

        # Output path input
        self.label_output_path = QLabel("Output Path:", self)
        layout.addWidget(self.label_output_path)
        self.lineEdit_output_path = QLineEdit(self)
        layout.addWidget(self.lineEdit_output_path)

        # COM Port Dropdown
        self.label_com_port = QLabel("COM Port:", self)
        layout.addWidget(self.label_com_port)
        self.comboBox_com_port = QComboBox(self)
        #self.comboBox_com_port.addItem("COM1")
        #self.comboBox_com_port.addItem("COM2")
        #self.comboBox_com_port.addItem("COM3")
        # Add more COM ports if necessary
        layout.addWidget(self.comboBox_com_port)

        # Browse button for output path
        self.button_browse = QPushButton("Browse", self)
        self.button_browse.clicked.connect(self.browse_file)
        layout.addWidget(self.button_browse)

        # Start button
        self.pushButton_start = QPushButton("Start", self)
        layout.addWidget(self.pushButton_start)

        # Refresh button
        self.pushButton_refresh = QPushButton("Refresh COM ports", self)
        layout.addWidget(self.pushButton_refresh)

    def browse_file(self):
        # Open folder dialog to select output folder
        folder_path = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder_path:
            self.lineEdit_output_path.setText(folder_path)  # Set the folder path to the input field

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CalibrationApp()
    window.show()
    sys.exit(app.exec_())