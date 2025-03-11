""" 
PlatformCalibration.py

captured csv data format:
weight
label,time,distances X6,pressures X6,pressure deltas X6,angles
"""

import sys,os
import time
import glob

import logging as log
import logging.handlers
import argparse
import csv
import operator  # for map sub
import traceback

from PyQt5 import QtWidgets, uic, QtCore, QtGui
from PyQt5.QtWidgets import QMessageBox

RUNTIME_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(RUNTIME_DIR))

from common.serialSensors import SerialContainer, Encoder, IMU, Scale, ServoModel

import common.serial_defaults as serial_defaults

from kinematics.dynamics import Dynamics
from kinematics.kinematicsV2 import Kinematics
# from kinematics.cfg_SlidingActuators import *
from kinematics.cfg_SuspendedChair import *

from calibration_graph import CalibrationGraph

import d_to_p_prep
import output.d_to_p as d_to_p
from output.muscle_output import MuscleOutput

DATA_PERIOD = 10  # ms between samples
MINUTES = 10  # size of buffer in mins 
SAMPLES = (1000/DATA_PERIOD) * MINUTES * 60

DUMMY_DISTANCE_DATA = True

SCALE__PERIOD = 250
D_TO_P_BASENAME = 'DtoP_'
P_TO_D_BASENAME = 'PtoD_'

qtcreator_file  = "Calibrate/calibration_gui.ui"
Ui_MainWindow, QtBaseClass = uic.loadUiType(qtcreator_file)

QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True) #enable highdpi scaling
QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True) #use highdpi icons


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, festo_ip):
        QtWidgets.QMainWindow.__init__(self)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        if festo_ip == '':
            # use this Festo ip not overridden on cmd line
            festo_ip = '192.168.0.10'  #  Festo Port is 995
        self.configure_kinematics()
        self.muscle_output = MuscleOutput(self.DtoP.distance_to_pressure, festo_ip)
        self.muscle_output.set_progress_callback(self.progress_callback)

        self.timer_data_update = None
        self.timer_scale_update = None
        self.distance = None # distance buffer
        self.curr_distance = 0 # most recent distance from serial 
        self.step_size = None # will be set to step size in calibrate method
        self.time = None
        self.is_capturing_data = False
        self.is_calibrating = False
        self.estopped = False
        self.time_interval = DATA_PERIOD / 1000.0
        self.activity_label = "idle"
        self.activity_labels = []  # describes what the platform is doing
        
        self.encoder_values = [self.ui.txt_pos_0,self.ui.txt_pos_1,self.ui.txt_pos_2,
            self.ui.txt_pos_3,self.ui.txt_pos_4, self.ui.txt_pos_5]   # displays encoder positions
        self.time = []  # time stamp
        self.distances = []  # encoder readings
        self.target_pressures = [] # pressures sent to festo
        self.pressure_deltas = []  # dif between commanded and actual pressure        
        self.imu_data = []  # roll, pitch, yaw
        self.graph = CalibrationGraph("title here")

        # configures
        self.configure_timers()
        self.configure_signals()
        self.configure_serial()
        self.configure_defaults()
        self.configure_button_groups()
        self.configure_festo_info()
        
        if DUMMY_DISTANCE_DATA:
            print("using DUMMY_DISTANCE_DATA")

    def configure_timers(self):
        self.timer_data_update = QtCore.QTimer(self) # timer services muscle pressures and data
        self.timer_data_update.timeout.connect(self.data_update)
        self.timer_data_update.start(DATA_PERIOD)
                               
        self.timer_scale_update = QtCore.QTimer(self) # timer to update scale readings
        self.timer_scale_update.timeout.connect(self.scale_update)
        
        self.delta_timer = QtCore.QTimer(self) # timer for distance deltas
        self.delta_timer.timeout.connect(self.distance_delta_update)

    def configure_signals(self):
        self.ui.btn_serial_connect.clicked.connect(self.connect)
        self.ui.btn_calibrate.clicked.connect(self.calibrate)
        self.ui.btn_start_capture.clicked.connect(self.start_capture)
        self.ui.btn_save_step_data.clicked.connect(self.save_step_data)
        self.ui.btn_save_raw.clicked.connect(self.save_raw_data)
        #  self.ui.btn_set_move.clicked.connect(self.move)
        self.ui.btn_estop.clicked.connect(self.estop)
        self.ui.tabWidget.currentChanged.connect(self.tab_changed)
        self.ui.btn_load_d_to_p.clicked.connect(self.load_d_to_p)
        self.ui.btn_run_lookup.clicked.connect(self.run_lookup)
        self.ui.chk_delta_capture.stateChanged.connect(self.delta_capture_state_changed)
        self.ui.btn_merge_d_to_p.clicked.connect(self.merge_d_to_p)
        self.ui.btn_encoder_update.clicked.connect(self.encoder_update)
        self.ui.btn_encoder_reset.clicked.connect(self.encoder_reset)
        self.ui.btn_move.clicked.connect(self.move)
        self.ui.btn_move_actuator.clicked.connect(self.move_actuator)
        self.ui.txt_weight.textChanged.connect(self.weight_edited)
        self.ui.lst_d_to_p.itemClicked.connect(self.list_clicked)

    def configure_serial(self):
        encoder_directions = [-1,1,1,1,1,1]
        log.info("encoder directions are: %s", str(encoder_directions))
        self.encoder = SerialContainer(Encoder(), self.ui.cmb_encoder_port, "encoder", self.ui.lbl_encoders, 115200)
        self.encoder.sp.set_direction(encoder_directions)
        self.imu = SerialContainer(IMU(), self.ui.cmb_imu_port, "imu", self.ui.lbl_imu, 57600)
        self.scale = SerialContainer(Scale(), self.ui.cmb_scale_port, "scale", self.ui.lbl_scale, 57600)
        self.model = SerialContainer(ServoModel(), self.ui.cmb_model_port, "model", self.ui.lbl_model, 57600)
        ports = self.encoder.sp.get_ports()
        ports.append("Ignore")
        self.open_ports = 0
        self.set_combo_default(self.encoder, ports)
        self.set_combo_default(self.imu, ports)
        self.set_combo_default(self.scale, ports)
        self.set_combo_default(self.model, ports)

    def set_combo_default(self, ser, ports):
        ser.combo.clear()
        ser.combo.addItems(ports)
        if ser.desc in serial_defaults.dict:
            port = serial_defaults.dict[ser.desc]
            log.info("%s default port is %s", ser.desc, port)
            index = ser.combo.findText(port, QtCore.Qt.MatchFixedString)
            if index >= 0:
                ser.combo.setCurrentIndex(index)
            else:
                ser.combo.setCurrentIndex(ser.combo.count() - 1)
        else:
            ser.combo.setCurrentIndex(ser.combo.count() - 1)

    def configure_festo_info(self):
        self.pressure_bars = [self.ui.muscle_0,self.ui.muscle_1,self.ui.muscle_2,self.ui.muscle_3,self.ui.muscle_4,self.ui.muscle_5]
        self.actual_bars = [self.ui.actual_0,self.ui.actual_1,self.ui.actual_2,self.ui.actual_3,self.ui.actual_4,self.ui.actual_5]
        self.txt_muscles = [self.ui.txt_muscle_0,self.ui.txt_muscle_1,self.ui.txt_muscle_2,self.ui.txt_muscle_3,self.ui.txt_muscle_4,self.ui.txt_muscle_5]
        for t in self.txt_muscles:
             t.setText('?')
        self.ui.chk_festo_actuals.stateChanged.connect(self.festo_check)

    def configure_defaults(self):
        self.ui.txt_step_delay_ms.setText("500")
        self.ui.txt_steps.setText("12")
        self.ui.txt_repeats.setText("3")
        self.ui.txt_weight.setText("waiting")
        self.ui.txt_weight_2.setText("waiting")
        self.ui.txt_p_to_d_fname.setText(P_TO_D_BASENAME + ".csv")
       
        self.ui.txt_merged_d_to_p_fname.setText("output\\DtoP.csv")
        self.ui.txt_d_to_p_fname.setText("output\\DtoP.csv")
        
        self.ui.txt_up_pressure.setText("3000")
        self.ui.txt_down_pressure.setText("2000")
        self.ui.txt_lookup_dur.setText("2")
        self.ui.txt_delta_fname.setText("distance_deltas.csv")
        self.ui.btn_save_step_data.setEnabled(False)
    
    def configure_button_groups(self):
        self.move_rbuttons = [self.ui.rb_X, self.ui.rb_Y, self.ui.rb_Z, self.ui.rb_Roll, self.ui.rb_Pitch, self.ui.rb_Yaw]
        self.move_btn_group = QtWidgets.QButtonGroup()
        for i in range(len(self.move_rbuttons)):
           self.move_btn_group.addButton(self.move_rbuttons[i], i)
        self.move_act_rbuttons = [self.ui.rb_A0, self.ui.rb_A1, self.ui.rb_A2, self.ui.rb_A3, self.ui.rb_A4, self.ui.rb_A5]
        self.move_btn_act_group = QtWidgets.QButtonGroup()
        for i in range(len(self.move_act_rbuttons)):
           self.move_btn_act_group.addButton(self.move_act_rbuttons[i], i)

    def configure_kinematics(self):
        self.k = Kinematics()
        cfg = PlatformConfig()

        cfg.calculate_coords()

        self.k.set_geometry( cfg.BASE_POS, cfg.PLATFORM_POS)
        if cfg.PLATFORM_TYPE == "SLIDER":
            self.k.set_slider_params(cfg.joint_min_offset, cfg.joint_max_offset, cfg.strut_length, cfg.slider_angles)
            self.is_slider = True
        else:
            self.is_slider = False
        self.cfg = cfg # only needed for plot
        
        self.DtoP = d_to_p.D_to_P(200) # argument is max distance 
        self.DtoP_prep = d_to_p_prep.D_to_P_prep(200) # argument is max distance
        self.dynam = Dynamics()
        self.dynam.begin(cfg.limits_1dof,"shape.cfg")

    def reset_buffers(self):
        self.distances = []
        self.target_pressures = []
        self.pressure_deltas = []
        self.imu_data = []
        self.time = []
        log.info("Buffers reset")

    def scale_update(self):
        if self.ui.chk_hold.isChecked() == False :
            weight = self.scale.sp.read()
            if weight != None:
                self.ui.txt_weight.setText(weight)
                self.ui.txt_weight.setText_2(weight)
                
    def weight_edited(self):
        try:
            w = "{:03d}".format(int(self.ui.txt_weight.text()))
            if len(w) == 3:
                self.ui.txt_p_to_d_fname.setText(P_TO_D_BASENAME + w + ".csv")
            else:
                log.error("Valid weight >= 0 and <= 999")
        except Exception as e:
            print(str(e))

    """
    def p_to_d_fname_edited(self):
        print(self.ui.txt_p_to_d_fname.text())
        file_exists = len(glob.glob(self.ui.txt_p_to_d_fname.text())) == 1
        if file_exists:
           lbl_text = "Create D to P from " + self.ui.txt_p_to_d_fname.text()
        else:     
            lbl_text = "Enter existing P to D file"
        self.ui.lbl_create_d_to_p.setText(lbl_text)
    """

    def list_clicked(self, item):    
        print( item.text())
        file = item.text().split('_')
        if file[0] == 'DtoP':
            PtoD = 'PtoD_' + file[1]
            print(PtoD)
            up,down, weight, pressure_step = self.DtoP_prep.munge_file(PtoD)
            # print(pressure_step, up)
            repeats, steps, actuators = np.shape(up)
            print( repeats, steps, actuators,  "up[0]=", up[0])
            title = "Actuator Movement over Pressure Range for {}kg load".format(round(weight))
            self.graph.begin(title, repeats, steps+1, 6, pressure_step) 
            # for r in range(repeats):
            repeat = 1
            for step in range(steps):
                print(up[repeat,step])
                self.graph.update( 0, repeat, step, up[repeat,step])
                self.graph.update( 0, repeat, step, down[repeat,step])

                    

            ##### d_to_p = self.DtoP_prep.process_p_to_d(up, down, weight, pressure_step)
        
    
    def echo_to_model(self, percents, distances):
        if self.model.sp.is_open():
            msg = 'm,' + ','.join(map(str, percents)) + '\n'
            self.model.sp.write( msg)
            log.debug("sending msg to servos: %s", msg)
            # while self.servo_model_sp.available():
            #     self.servo_model_sp.read()
                
    def tab_changed(self, tab_index):
        if tab_index  in [1,3,4]:
            self.ui.ProgressGroupBox.show()
        else:       
            self.ui.ProgressGroupBox.hide()
        if tab_index == 2:
            self.ui.lst_d_to_p.clear()
            self.ui.lst_d_to_p.addItems(glob.glob("DtoP_*.csv"))
            self.ui.lst_to_merge.clear()
            self.ui.lbl_merged.setText("")

    def delta_capture_state_changed(self, int):
        if self.ui.chk_delta_capture.isChecked():
            fname = str(self.ui.txt_delta_fname.text())
            self.delta_file =  open(fname, 'a')
            if  self.delta_file.closed:
                log.error("unable to open %s", fname)
            else:
                log.debug("opened %s", fname)
                encoder_data,timestamp = self.encoder_update()
                if encoder_data == None:
                    log.warning("no encoder data, has the port been started?")
                else:
                    if self.muscle_output.up_indices == None:
                        log.error("muscle curve files have not been loaded and calibrated")
                    else:
                        self.delta_timer.start(50)
        else:
            self.delta_timer.stop()
            self.delta_file.close()           

    def distance_delta_update(self):
        if  self.delta_file.closed:
            pass
        else:
           if self.muscle_output.distances:
                encoder_data,timestamp = self.encoder_update()
                if encoder_data:
                     # encoder_data = map(int, encoder_data)
                     delta = [e-d for e,d in zip(encoder_data, self.muscle_output.distances)]
                     data = ','.join(map(str, self.muscle_output.distances)) + ","  + ','.join(map(str, delta)) + "\n"
                     self.delta_file.write(data)
                else:
                    log.error("no encoder data")

    def connect(self):
        if self.open_ports > 0:
            self.close_port(self.encoder)
            self.close_port(self.imu)
            self.close_port(self.scale)
            self.timer_scale_update.stop()
            self.close_port(self.model)
            self.open_ports =0
            self.ui.btn_serial_connect.setText("    Connect    ")
        else:
            self.open_port(self.encoder)
            if self.encoder.sp.is_open():
                self.encoder.sp.reset()
                self.encoder.sp.set_precision(1)
                self.encoder.sp.set_interval(10)
            self.open_port(self.imu)
            self.open_port(self.scale)
            if self.scale.sp.is_open():
                  self.timer_scale_update.start(SCALE__PERIOD)
            self.open_port(self.model)
            if self.model.sp.is_open():
                self.muscle_output.set_echo_method(self.echo_to_model)
            if self.open_ports > 0:
                self.ui.btn_serial_connect.setText("  Disconnect  ")

    def open_port(self, ser): 
        if ser.sp.is_open():
            self.disconnect(ser.sp)
            ser.label.setStyleSheet('QLabel  {color: black;}')
        else:
            port = str(ser.combo.currentText())
            if 0 < len(port) and port != "Ignore":
                if ser.sp.open_port(port, ser.baud):
                    ser.label.setStyleSheet('QLabel  {color: green;}')
                    log.info("opened %s", ser.desc)
                    self.open_ports += 1
                else:
                    log.warning("%s port is not available", ser.desc)
            else:
                log.error("%s port was not opened",  ser.desc)

    def close_port(self, ser):
        ser.label.setStyleSheet('QLabel  {color: black;}')
        if ser.sp.is_open():
            ser.sp.close_port()


    def start_capture(self):
        if self.is_capturing_data:
            self.stop_capture() 
        else:
            log.info("Data Capture started")
            self.reset_buffers()
            self.ui.btn_start_capture.setText("Stop")
            self.ui.DataGroupBox.setStyleSheet('QGroupBox  {color: red;}')
            self.is_capturing_data = True

    def stop_capture(self):
        log.info("Data Capture stopped")
        self.ui.btn_start_capture.setText("Start")
        self.ui.DataGroupBox.setStyleSheet('QGroupBox  {color: black;}')
        self.is_capturing_data = False
        
    def estop(self):
        if self.estopped:
            self.estopped = False
            self.ui.btn_estop.setText("Emergency Stop")
        else:
            self.is_capturing_data = False
            self.estopped = True
            self.muscle_output.is_slow_moving = False # stop any running ride
            self.is_calibrating = False
            self.ui.btn_estop.setText("Press to Clear")
            log.warning("todo lower platform")

    def progress_callback(self, percent):
        self.ui.progressBar.setValue(percent)

    def calibrate(self):
        if self.is_calibrating:
            print("aborting calibration")
            self.ui.CalibrateGroupBox.setStyleSheet('QGroupBox  {color: black;}')
            self.is_calibrating = False
            self.stop_capture()
            self.activity_label = "idle"
        else:
            print(str(self.encoder.combo.currentText()))
            if self.encoder.sp.is_open() == False: #  and not 'Ignore' in str(self.encoder.combo.currentText()):
                QtWidgets.QMessageBox.warning(self, 'Encoder Comms!',
                                "Encoder comms must be connected before calibrating", QtWidgets.QMessageBox.Ok)
                return 
                
            try:
               weight =  float(self.ui.txt_weight.text())
               log.info("starting calibration using weight %.1f", weight)
            except ValueError:
                QtWidgets.QMessageBox.warning(self, 'Missing Weight!',
                                "A valid weight is needed in Data Capture 'Load kg' field", QtWidgets.QMessageBox.Ok)
                return 
                
            log.info("todo reset encoders to zero")
            self.ui.CalibrateGroupBox.setStyleSheet('QGroupBox  {color: red;}')
            self.ui.btn_calibrate.setText("Cancel")
            self.ui.lbl_create_d_to_p.setText("")
            end_step = 6000  # step pressure
            self.activity_label = "calibrate pressure"
            self.is_calibrating = True
            self.start_capture() # start capturing data
            steps = int(self.ui.txt_steps.text())
            repeats = int(self.ui.txt_repeats.text())
            # start_timeout = int(self.ui.txt_start_timeout.text())
            step_delay = float(self.ui.txt_step_delay_ms.text())*.001
            self.step_size = (end_step) / steps
            step_percent = (100.0 / (2*(steps+1))) / repeats
            completed = 0.0
            self.step_data = []
            if self.ui.chk_graph.isChecked():
                title = "Actuator Movement over Pressure Range for {}kg load".format(round(weight))
                self.graph.begin(title, repeats, steps+1, 6, self.step_size ) 
            print()
            print('Cycle Nbr, Step, up down, pressure, d0, d1, d2, d3, d4, d5')
            for r in range(repeats):
                # self.encoder_reset()
                for step in range(steps+1):
                    if self.is_calibrating == False:
                        self.ui.btn_calibrate.setText("Restart")
                        return 
                    # self.purge_messages(True)
                    completed += step_percent
                    if not self.step_platform(step*self.step_size, step_delay, step, 0, r):
                        log.error("aborting due to encoder error")
                        return
                    self.ui.progressBar.setValue(round(completed))  
                for step in range(steps+1):
                    if self.is_calibrating == False:
                        self.ui.btn_calibrate.setText("Restart")
                        return                       
                    completed += step_percent
                    if not self.step_platform((end_step-step*self.step_size), step_delay, step, 1, r):
                        log.error("aborting due to encoder error")
                        return
                    self.ui.progressBar.setValue(round(completed))

            self.ui.CalibrateGroupBox.setStyleSheet('QGrouBox  {color: black;}')
            self.ui.CalibrateGroupBox.setStyleSheet('QGroupBox  {color: black;}')
            self.is_calibrating = False
            self.ui.btn_calibrate.setText("Restart")
            self.stop_capture()  # stop capturing data
            self.activity_label = "idle"
            self.ui.btn_save_step_data.setEnabled(True)
            self.ui.lbl_create_d_to_p.setText("Press Save to create data files")

    def merge_d_to_p(self):
        weights = []
        up_d_to_p = []
        down_d_to_p = []
        infiles = []
        count = self.ui.lst_to_merge.count()
        for i in range(count):
             infiles.append(str(self.ui.lst_to_merge.item(i).text()))  
        outfname = str(self.ui.txt_merged_d_to_p_fname.text())
        try:
           self.DtoP_prep.merge_d_to_p(infiles, outfname)
           self.ui.lst_to_merge.clear()
           self.ui.lbl_merged.setText("{} files merged".format(count))
        except Exception as e:
            log.error(str(e))
   

    def merge_d_to_p_x(self):
        weights = []
        up_d_to_p = []
        down_d_to_p = []
        for index in range(self.ui.lst_to_merge.count()):
            fname = str(self.ui.lst_to_merge.item(index).text())
            with open(fname) as fp:
                header = fp.readline()
                if 'weight=' in header:
                    weights.append(int(header.split('=')[1]))
                    # print(weights)
                    up = fp.readline()
                    values = [int(round(float(i))) for i in up.split(',')]
                    up_d_to_p.append(values)
                    down = fp.readline()
                    values = [int(round(float(i))) for i in down.split(',')]
                    down_d_to_p.append(values)

        if len(weights) > 0:
            header = '# weights,' +  ','.join(str(n) for n in weights)
            combined_d_to_p= []
            for i in range (len(weights)):
                combined_d_to_p.append(up_d_to_p[i])
            for i in range (len(weights)):
                combined_d_to_p.append(down_d_to_p[i])
            outfname = str(self.ui.txt_merged_d_to_p_fname.text())
            with open(outfname, "w") as fp:
                fp.write(header + '\n')
                for i in range (len(weights)*2):  # write up then down
                    fp.write( ','.join(str(n) for n in combined_d_to_p[i] ) + '\n')
        else:
           log.error("no valid d to p files found")


    def load_d_to_p(self):
        # load distance to pressure curves from file
        fname = str(self.ui.txt_d_to_p_fname.text())
        if self.DtoP.load(fname):
            self.ui.txt_nbr_indices.setText(str(self.DtoP.rows))

    def run_lookup(self):
        # find closest curves for each muscle at the current load
        if self.ui.txt_nbr_indices.text() == '' or int(self.ui.txt_nbr_indices.text()) < 1:
            print("You must load D-to-P file before running lookup")
            return
        up_pressure = int(self.ui.txt_up_pressure.text())
        down_pressure = int(self.ui.txt_down_pressure.text())
        dur = int(self.ui.txt_lookup_dur.text())
        self.muscle_output.slow_pressure_move(0, up_pressure, dur)
        time.sleep(.5)
        encoder_data,timestamp = self.encoder_update()
        encoder_data = np.array(encoder_data )  #     [123,125,127,129,133,136])
        self.DtoP.set_index(up_pressure, encoder_data, 'up' )
        self.ui.txt_up_index.setText(', '.join(str(i) for i in self.DtoP.up_curve_idx)) 
        self.muscle_output.slow_pressure_move(up_pressure, down_pressure, dur/2)
        time.sleep(.5)
        encoder_data,timestamp = self.encoder_update()
        encoder_data = np.array(encoder_data)  # [98,100,102,104, 98,106])
        self.DtoP.set_index(down_pressure, encoder_data, 'down' )
        self.ui.txt_down_index.setText(', '.join(str(i) for i in self.DtoP.down_curve_idx))

    def step_platform(self, pressure, step_delay, step, updown, repeat):
        pressures = [int(pressure)]*6
        self.muscle_output.send_pressures(pressures)
        self.show_pressures(pressures)
        # print("Step:", pressure, step, updown, repeat, step_delay)
        start_time = time.time()
        if DUMMY_DISTANCE_DATA:
            if updown == 1 and pressure > 0 and pressure < 6000:
                self.distances = [round(pressure/90)] * 6  
            else:
                self.distances = [round(pressure/100)] * 6
        while len(self.distances) == 0 and time.time() - start_time < 0.1:
            app.processEvents()
        if len(self.distances) == 0:
            QtWidgets.QMessageBox.warning(self, 'Calibrate!', "Insufficient encoder data to start calibration",
                                           QtWidgets.QMessageBox.Ok)
            return False # this will abort the stepping loop
        distances = self.distances
        move_durations = [0.0]*6
        first_move_time = 0
        last_move_time =0
        move_dur = 0
        while  time.time() - start_time < step_delay:
            app.processEvents()
            for i in range(6):
                if self.distances[i] !=  distances[i]:
                    move_durations[i] = time.time() - start_time
                    distances[i] = self.distances[i]
        self.step_data.append([repeat, updown, step, pressure, self.distances, move_durations])
        if self.ui.chk_graph.isChecked():
            self.graph.update( updown, repeat, step, self.distances)
            
        print('{},{},{},{},{}'.format(repeat, step, updown, pressure, ','.join(str(d) for d in self.distances)))
        return True

    def move(self):
        if self.is_calibrating or self.estopped:
            print("Manual mode disabled while another activity is active")
        else:
            percent =  self.ui.sld_percent.value()
            idx = self.move_btn_group.checkedId() 
            request = [0]*6
            request[idx] = percent*.01
            request = self.dynam.regulate(request) # convert normalized to real values
            percents = self.k.actuator_percents(request)
            self.muscle_output.move_percent(percents)

    def move_actuator(self):
        if self.is_calibrating or self.estopped:
            print("Manual mode disabled while another activity is active")
        else:
            percent =  self.ui.sld_percent_actuator.value()
            idx = self.move_btn_act_group.checkedId() 
            percents = [0]*6
            percents[idx] = percent
            self.muscle_output.move_percent(percents)
            print("move percents:", percents)

    def encoder_update(self):
        encoder_data,timestamp = self.encoder.sp.read()
        # print(encoder_data, timestamp)
        if encoder_data and timestamp != 0:            
            for i in range(len(self.encoder_values)):
                # temp for testing
                #  if i > 0:
                #    encoder_data[i] = encoder_data[0] + i
                self.encoder_values[i].setText(str(encoder_data[i]))
            return encoder_data,timestamp
        return None, None

    def encoder_reset(self):
        self.encoder.sp.reset()

    def data_update(self):
        timestamp = 0
        self.prev_timestamp = 0
        try:
            encoder_data,timestamp = self.encoder_update()
            self.actual_pressures = self.muscle_output.get_pressures()            
            if encoder_data and timestamp != 0:
                if len(encoder_data) == 6:
                    self.distances = encoder_data
                    try:
                        for i in range(len(self.encoder_values)):
                            self.encoder_values[i].setText(format("%.1f" % (encoder_data[i])))
                    except IndexError:
                        print("index error, i = ", i, "values:", encoder_data)
                else:
                    print("bad encoder data ignored", encoder_data)
                if self.is_capturing_data:
                    self.time.append(timestamp)
                    if timestamp != 0 and self.prev_timestamp != 0:
                        # check for missing messages
                        if timestamp-self.prev_timestamp > 10:
                            print("missing message at timestamp", timestamp, "prev was", self.prev_timestamp, "diff=", timestamp-self.prev_timestamp)
                    self.activity_labels.append(self.activity_label)
    
                    out_pressures = self.muscle_output.festo.out_pressures
                    self.target_pressures.append(out_pressures)
                    delta = map(operator.sub, self.muscle_output.in_pressures , out_pressures)
                    self.pressure_deltas.append(delta)
                    if self.imu.sp.is_open():
                        self.imu_data.append(self.imu.sp.read())
                    #self.ui.txt_pressure_delta.setText(str(delta))
                    #self.ui.txt_measured_pos.setText(value[1]) # todo ??


        except Exception as e:
            s = traceback.format_exc()
            print("error reading serial data", e, s)

    def save_step_data(self):
        dtop_fname = self.ui.txt_p_to_d_fname.text()
        if dtop_fname == "":
            return 
        try:
            self.outfile = open(dtop_fname,"w")
            # self.outfile.write("data using weight: " +  self.ui.txt_weight.text()+"\n")
            self.outfile.write("WEIGHT," + self.ui.txt_weight.text()+"\n")
            self.outfile.write("STEPS," + self.ui.txt_steps.text()+"\n")
            if self.step_size != None:
                self.outfile.write("mb per step," + str(self.step_size) + "\n")
            self.outfile.write("CYCLES," + self.ui.txt_repeats.text()+"\n")
            self.outfile.write(",\n")
            self.outfile.write("cycle,dir,step,pressure,d0,d1,d2,d3,d4,d5,t0,t1,t2,t3,t4,t5\n")
            for step in self.step_data:
                data = step[:4] + step[4] + step[5]
                line = ','.join(str(n) for n in data)
                self.outfile.write(line + "\n")
            self.outfile.close()
            self.create_d_to_p(dtop_fname)
        except Exception as e:
            s = traceback.format_exc()
            log.error("Error saving data file, is it already open? %s %s", e, s)

    
    def form_dtop_fname(self, ptod_fname):
        try:
            t = ptod_fname.split('.')
            t1  = t[0].split('_')
            if t1[0] == P_TO_D_BASENAME[:-1]:
                return D_TO_P_BASENAME + t1[1] + '.csv'
        except Exception as e:
            print(str(e), traceback.format_exc())

        return None
        
    def create_d_to_p(self, infname):
        if infname == "":
            return 
        outfname = self.form_dtop_fname(infname)
        if outfname:
            log.info("D to P: creating %s from %s", infname, outfname)

            up,down, weight, pressure_step = self.DtoP_prep.munge_file(infname)

            d_to_p = self.DtoP_prep.process_p_to_d(up, down, weight, pressure_step)
            info = format("weight=%d" % weight)    
           
            np.savetxt(outfname, d_to_p, delimiter=',', fmt='%0.1f', header= info)
            self.ui.lbl_create_d_to_p.setText("Pressure to Distance file saved as " + outfname)
            
    def save_raw_data(self):
        try:
            self.outfile = open(self.ui.txt_raw_data_fname.text(),"w")
            self.outfile.write("Raw data using weight: " +  self.ui.txt_weight.text()+"\n")
            self.outfile.write("label,time,d0,d1,d2,d3,d4,d5,p0,p1,p2,p3,p4,p5,pd0,pd1,pd2,pd3,pd4,pd5,roll,pitch,yaw\n")
            for i in range(len(self.time)):
                if len(self.imu_data) > i:
                    imu_data = [self.imu_data[i]]
                else:
                    imu_data = [0,0,0]
                line = [self.activity_labels[i]] + [self.time[i]] + self.distances[i] + self.target_pressures[i] + self.pressure_deltas[i] + imu_data
                #print(','.join(str(n) for n in line))
                self.outfile.write(','.join(str(n) for n in line) +'\n')
            self.outfile.close()
            # if len(self.ui.txt_p_to_d_fname.text()) < 1:
            #     self.ui.txt_p_to_d_fname.setText(self.ui.txt_capture_fname.text())

        except Exception as e:
            s = traceback.format_exc()
            log.error("Error saving data file, is it already open? %s %s", e, s)
                    
    def show_pressures(self, pressures):
        for i in range(6):
            rect =  self.pressure_bars[i].rect()
            width = pressures[i] / 20
            if width < 1: width = 1
            rect.setWidth(round(width))
            self.pressure_bars[i].setFrameRect(rect)
            self.txt_muscles[i].setText(format("%d mb" % pressures[i])) #may  be overwritten with actuals 
        if self.ui.chk_festo_actuals.isChecked():
            # actuals = pressures # [100,200,500,700, 2000, 5000]
            self.show_actual_pressures(self.actual_pressures)

    def show_actual_pressures(self, actuals):
        for i in range(6):
            rect =  self.actual_bars[i].rect()
            width = actuals[i] / 20
            rect.setWidth(int(width))
            self.actual_bars[i].setFrameRect(rect)
            
    def festo_check(self, state):
        if state == QtCore.Qt.Checked:
            log.info("System will request Festo actual pressures")
            self.muscle_output.set_wait_ack(False)
            self.muscle_output.enable_poll_pressures(True)
        else:
            log.info("System will ignore Festo actual pressures")
            self.muscle_output.set_wait_ack(True)
            self.muscle_output.enable_poll_pressures(False)

def start_logging(level):
    log_format = log.Formatter('%(asctime)s,%(levelname)s: %(message)s')
    logger = log.getLogger()
    logger.setLevel(level)

    file_handler = logging.handlers.RotatingFileHandler("PlatformCalibration.log", maxBytes=(10240 * 5), backupCount=2)
    file_handler.setFormatter(log_format)
    logger.addHandler(file_handler)

    console_handler = log.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_format)
    logger.addHandler(console_handler)


def man():
    parser = argparse.ArgumentParser(description='PlatformCalibration\nA real time testing application')
    parser.add_argument("-l", "--log",
                        dest="logLevel",
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help="Set the logging level")
    parser.add_argument("-f", "--festo_ip",
                        dest="festoIP",
                        help="Set IP address of Festo controller")                        
    return parser


if __name__ == '__main__':
    # multiprocessing.freeze_support()
    args = man().parse_args()
    if args.logLevel:
        start_logging(args.logLevel)
    else:
        start_logging(log.INFO)

    log.info("Python: %s, qt version %s", sys.version[0:5], QtCore.QT_VERSION_STR)
    log.info("Starting PlatformCalibration")

    app = QtWidgets.QApplication(sys.argv)
    if args.festoIP:
        win = MainWindow(args.festoIP)
    else:
        win = MainWindow('')
    win.show()
    app.exec_() #mm added underscore
    
    log.info("Finishing PlatformCalibration\n")
    log.shutdown()
    win.close()
    app.exit()  
    sys.exit()
