from PyQt5 import QtWidgets
from gui_class import Ui_MainWindow  # Import your generated UI class
import sys

class MainApp(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)  # Load the UI

        # Connect slider signal
        self.master.valueChanged.connect(self.on_slider_change)
        self.xaccel.valueChanged.connect(self.on_slider_change)
        self.yaccel.valueChanged.connect(self.on_slider_change)
        self.zaccel.valueChanged.connect(self.on_slider_change)
        self.roll.valueChanged.connect(self.on_slider_change)
        self.pitch.valueChanged.connect(self.on_slider_change)
        self.yaw.valueChanged.connect(self.on_slider_change)

        # Connect button click
        self.pushButton.clicked.connect(self.on_button_click)

    def on_slider_change(self, value):
        print(f"Slider Value: {value}")

    def on_button_click(self):
        print("Button Clicked!")

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec_())

