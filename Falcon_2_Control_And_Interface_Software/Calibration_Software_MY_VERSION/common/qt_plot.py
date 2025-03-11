import sys
import numpy as np
import math 
import traceback
from collections import deque
import pyqtgraph as pg
from PyQt5 import QtCore, QtGui, QtWidgets
from pyqtgraph import PlotWidget, ViewBox
from PyQt5.QtGui import QKeySequence

from qt_plot_cfg import plotConfig # modify this to change plotting config
 
QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True) #enable highdpi scaling
QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True) #use highdpi icons

class Plot:
    # consists of one plot widget and one or more plotters
    def __init__(self, plot_widget, plotters):
        self.plot_widget = plot_widget
        self.plotters = plotters
        

class Plotter:
    # draws one line of a plot
    # todo add trace legend here
    def __init__(self, plot_widget, timewindow, buffsize, color, name):
        self.config_buffers(timewindow, buffsize)
        
        # PyQtGraph stuff
        plot_widget.addLegend()
        if len(name) > 0:
            self.curve = plot_widget.plot(self.x, self.y, pen=(color), name=name)
        else:
            self.curve = plot_widget.plot(self.x, self.y, pen=(color))
  
    def config_buffers(self, timewindow, buffsize):
        # Data stuff
        self.databuffer = deque([0.0] * buffsize, buffsize)
        self.x = np.linspace(-timewindow, 0.0, buffsize)
        self.y = np.zeros(buffsize, dtype=float)
        
    def update(self, data):
        self.databuffer.append(data)
        self.y[:] = self.databuffer
        self.curve.setData(self.x, self.y)
       
        
class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        self.MainWindow = MainWindow
        self.cfg = plotConfig()
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(self.cfg.window_width, self.cfg.window_height)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        MainWindow.setCentralWidget(self.centralwidget)
        self.pause_key = QtWidgets.QShortcut(QKeySequence("P"), self)
        self.is_paused = False
        self.pause_key.activated.connect(self.pause_event)
        # self.layout = QtWidgets.QVBoxLayout(self.centralwidget) 
        self.layout = QtWidgets.QGridLayout(self.centralwidget) 
     
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", '  '+self.cfg.main_title))
        
        
        self.wait_data_label = QtWidgets.QLabel('Waiting for data', self)
        self.wait_data_label.setAlignment(QtCore.Qt.AlignCenter)
        self.layout.addWidget(self.wait_data_label,0,0)
        self.wait_data_label.adjustSize()
        self.plotWidgets = []

        self.plots_initialized = False  # set True on first valid data message
        # self.init_plot_widgets(self.cfg.get_plot_title,self.cfg.minY,self.cfg. maxY)
        
        # QTimer
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_plots)
        self.timer.start(self.cfg.interval_ms)
        print("setupUI complete")

    def calc_rendered_shape(self, nbr_plots, max_plot_rows):
        cols = math.ceil(nbr_plots / max_plot_rows )
        rows = math.ceil(nbr_plots / cols )
        return rows, cols
    
    def init_plot_widgets(self):
        self.plots = [] # one per plot
        self.plotters = [] # list of one or more traces for each plot

        # nbr_rows, nbr_columns = self.calc_rendered_shape(self.cfg.nbr_plots, self.cfg.max_plot_rows)
        nbr_columns = math.ceil(self.cfg.nbr_plots / self.cfg.max_plot_rows )
        nbr_rows = math.ceil(self.cfg.nbr_plots/ nbr_columns )
        if self.cfg.layout_horizontal:
            nbr_rows,nbr_columns = nbr_columns, nbr_rows
        # print("Initializing {} plots: nbr rows = {} nbr_columns = {}".format(self.cfg.nbr_plots, nbr_rows, nbr_columns))
        # print("trace names:", self.cfg.trace_names)
        
        while self.layout.count():
            child = self.layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self.plotWidgets.clear()
            
        for i in range(self.cfg.nbr_plots):
            self.plotWidgets.append(PlotWidget())
            if self.cfg.layout_horizontal:
                row = int(i / nbr_columns)
                col =  i % nbr_columns 
            else:
                row = i % nbr_rows
                col = int( i / nbr_rows) 
            # self.plotWidgets[i].show()
            self.layout.addWidget(self.plotWidgets[i],row, col)
            
            # PyQtGraph stuff
            self.plotWidgets[i].setTitle(self.cfg.plot_names[i])
            self.plotWidgets[i].showGrid(x=True, y=True)
            # print("whamm", self.cfg.minmax)
            if self.cfg.minmax:
                minmax = self.cfg.minmax[i]
            if self.cfg.minmax  == None or minmax == 'A':
                self.plotWidgets[i].enableAutoRange(axis=ViewBox.YAxis)
            else:    
                self.plotWidgets[i].setYRange(minmax[0], minmax[1])
            #  print("using hard coded minmax 0,100")
            #  self.plotWidgets[i].setYRange(0, 100)            
            self.plotWidgets[i].setBackground((16,16,16))
            # self.plotWidgets[i].setLabel('bottom', 'Time', 's')
            plotters = []
            for j in range(self.cfg.data_shape[i]):
                try:
                    trace_name = self.cfg.trace_names[i][j]
                except:
                    trace_name = ''
                plotters.append(Plotter(self.plotWidgets[i], self.cfg.timewindow, self.cfg.buffer_size, self.cfg.trace_colors[j], trace_name))
            self.plots.append(Plot(self.plotWidgets[i], plotters))
            # print("init plot widget", i, "with", len(plotters), "plotters")
            # print("PLOT",i,  len(self.plots[i].plotters))

                
    def update_plots(self):
        if self.is_paused : return
        is_format_change, self.data = self.cfg.update()
        if self.data:
            # if not self.plots_initialized:
            if is_format_change:          
                self.init_plot_widgets()
                # self.wait_data_label.setVisible(False)
                self.plots_initialized = True
                self.MainWindow.setWindowTitle(self.cfg.main_title)     
            for i, plot in enumerate(self.plots):  
                for j,plotter in enumerate(plot.plotters):
                    plotter.update(float(self.data[i][j]))

    def pause_event(self):
        self.is_paused = not self.is_paused
        # print("pause", self.is_paused)

class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent=parent)
        self.setWindowIcon(QtGui.QIcon('plot_icon.png'))
        self.setupUi(self)

if __name__ == "__main__":
    print("Python:", sys.version[0:5], "qt version", QtCore.QT_VERSION_STR)
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())
