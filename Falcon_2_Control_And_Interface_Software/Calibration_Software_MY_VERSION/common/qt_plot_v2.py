import sys
import numpy as np
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
    def __init__(self, plot_widget, timewindow, buffsize, color):
        # Data stuff
        self.databuffer = deque([0.0] * buffsize,buffsize)
        self.x = np.linspace(-timewindow, 0.0, buffsize)
        self.y = np.zeros(buffsize, dtype=float)
        
        # PyQtGraph stuff
        plot_widget.addLegend()
        self.curve = plot_widget.plot(self.x, self.y, pen=(color))
  
    def update(self, data):
        self.databuffer.append(data)
        self.y[:] = self.databuffer
        self.curve.setData(self.x, self.y)
        
        
class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        self.cfg = plotConfig()
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(self.cfg.window_width, self.cfg.window_height)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        MainWindow.setCentralWidget(self.centralwidget)
        self.pause_key = QtWidgets.QShortcut(QKeySequence("P"), self)
        self.is_paused = False
        self.pause_key.activated.connect(self.pause_event)
        self.layout = QtWidgets.QVBoxLayout(self.centralwidget) 
  
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", '  '+self.cfg.title))
        self.init_plot_widgets(self.cfg.get_plot_title,self.cfg.minY,self.cfg. maxY)
        
        # QTimer
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_plots)
        self.timer.start(self.cfg.interval_ms)

    def init_plot_widgets(self, get_plot_title, minY, maxY):
        # todo add titles here
        self.plots = []
        try:
            nbr_plots = int(sys.argv[1])
            self.cfg.nbr_plots = nbr_plots # use cmd arg for nbr plots
            self.cfg.autorange = True   # always autorange if using cmd line
        except:    
            pass # use nbr plots and autorange defined in cfg
            
        for i in range(self.cfg.nbr_plots):
            plotWidget = PlotWidget(self.centralwidget)
            self.layout.addWidget(plotWidget) 
            
            # PyQtGraph stuff
            plotWidget.setTitle(get_plot_title(i))
            plotWidget.showGrid(x=True, y=True)
            if self.cfg.autorange or maxY[i] == 'auto' :
                plotWidget.enableAutoRange(axis=ViewBox.YAxis)
            else:    
                plotWidget.setYRange(minY[i], maxY[i])
            plotWidget.setBackground((16,16,16))
            # plotWidget.setLabel('bottom', 'Time', 's')
            plotters = []
            for j in range(self.cfg.max_nbr_traces):
                plotters.append(Plotter(plotWidget, self.cfg.timewindow, self.cfg.buffer_size, self.cfg.trace_colors[j]))
            self.plots.append(Plot(plotWidget, plotters))
            #print("init plot widget", i, "with", len(plotters), "plotters")
   
    def update_plots(self):
        if self.is_paused : return
        self.data = self.cfg.update()
        if self.data:
            nbr_traces = len(self.data)
            if  nbr_traces <= self.cfg.max_nbr_traces  and len(self.data[0]) == self.cfg.nbr_plots: 
                # print("data", self.data, "data[0]", self.data[0])
                for i in range(nbr_traces):     
                    for j in range(self.cfg.nbr_plots):
                        # print(i,j, self.data[i][j])
                        plotter = self.plots[j].plotters[i]
                        plotter.update(float(self.data[i][j]))
            else:
                print("data error (should be detected in config")
                print( len(self.data[0]) == self.cfg.nbr_plots, self.cfg.nbr_plots, len(self.data[0]) )

    # @pyqtSlot()
    def pause_event(self):
        self.is_paused = not self.is_paused
        # print("pause", self.is_paused)

class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent=parent)
        self.setupUi(self)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())
