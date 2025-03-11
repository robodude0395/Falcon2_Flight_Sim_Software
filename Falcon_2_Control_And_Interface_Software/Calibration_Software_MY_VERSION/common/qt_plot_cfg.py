"""
qt_plot_cfg.py

class to confgure qt_plot
Set plot preferences here


Plotter will use input from serial port if opened
else data will be read from UDP

Data Protocol examples:
  one plot will contain one trace
    d1\n       <- di will be plotted, no title or legend
    text:d1/n  <- will show text as a legend for the trace
    title#text:d1/n  <- will display title on the plot, text as legend
  
  one plot will contain three traces   
    da,db,dc\n    <- three data values traced on one plot, no title or legend
    text1:da,text2:db,text3:dc/n  <- three traces with associated legends
    title#text1:da,text2:db,text3:dc/n   <- as above with title for the plot
 
   three plots, each with one trace
    d1;d2;d3\n  <-  the three values will be traced on three seperate plots  
    title1#da;title2#db;title3#dc/n  <- titles for each plot
    
    three plots, each with two traces
    t1,t2;t1,t2;t1,t2\n  <-  the three values will be traced on three seperate plots  

   
note: plot titles are seperated with #
      trace legends are seperated with :
      titles and legends are optional  

fixme optional title1:min1;max1:title2:min2;max2 # 
  or           title1:A
  where min/max or auto persist (and perhaps title) if absent 
 
messages consist of an optional msg prefix seperated from data with '#'
the prefix contains a plot prefix for each plot seperated by a ':'
  each plot prefix can consist of a plot title  and an optional min/max value 
    seperated by a ':'
    the min/max vlaue consists of two floting point string seperated by ';'
    if no min/max value is give then this plot will autorange

Punctuation summary for title preamble
    # seperates preamble from data
    ; seperates title from minmax

Punctuation summary for plot data    
    ; seperates each plot 
    : seperates trace name from data value
    , seperates traces
 
 currently the max number of traces per plot is six (limited by size of trace color list)
   there is no software limit on the number of plots but more than 6 may be hard to read.

Note: ensure the setting for nbr_plots matches the data sent.
The software autodetects the number of traces by parsing the incoming data

   
Copyright Michael Margolis 2022 
MIT license 

"""
import sys
import socket
import threading
from queue import Queue
try:
   import serial
   import time
except:
    print("pip install pyserial or comment out the import if serial not used")

    
class plotConfig():
    main_title = 'Real time Plotter - Waiting for data (see plot_itf.py for details)'
    
    timewindow = 5 # seconds to display
    interval_ms = 50 # sample acquisition interval in milliseconds
    layout_horizontal = True # if true, rows filled before columns, esle cols before rows 
    max_plot_rows = 3 # plots will be stacked in columns if necessary     
    max_nbr_traces = 6 # max nbr of lines in each plot
    MAX_NBR_PLOTS = 12 # this many plot widgets will be created
    trace_colors = ['r', 'g', 'y', 'w', 'm', 'c', 'b' ] # last color not used
    
    buffer_size =  int(timewindow * (1000/interval_ms))
    
    serial_port = None # 'COM12'  # set to None of not using serial port
    serial_baud = 115200    
    UDP_port = 10029

    window_width = 1000
    window_height = 800

    def __init__(self):
        self.ser = None 
        self.udp = None
        if self.serial_port:
            self.ser = MySerial()
            self.ser.open_port(self.serial_port, self.serial_baud)      
            print("reading data from serial:", self.serial_port)
        elif self.UDP_port:
             self.udp = UdpReceive(self.UDP_port)    
             print("reading data from UDP port", self.UDP_port)
        self.data_shape = None
        self.titles = None
        self.trace_names = None
        self.minmax = None


    def parse_preamble(self, preamble):
        # extracts optional main title, plot titles and min/max values
        plots = preamble.split(',')
        if 'MAIN_TITLE=' in plots[0]:
            self.main_title = plots[0].split('=')[1]
            plots.pop(0) # remove main title            
        titles = []
        minmax = []
        for plot in plots:
            p = plot.split(':')
            if len(p) == 2:
                titles.append(p[0])
                mm = p[1].split(';')
                if len(mm) == 2:
                    minmax.append((float(mm[0]), float(mm[1]))) 
                else:
                     minmax.append('A')
            else:   
                titles.append(plot)
                minmax.append('A')             
        return titles, minmax
        
    def unpack_msg(self, msg):
        # method to convert received protocol to format returned in update method 
        _msg = msg.strip().split('#')
        if len(_msg) == 2:
            # here if preample with optional plot titles and min/max values
            plot_names, minmax = self.parse_preamble(_msg[0])
            data = _msg[1]
            # print("plot names", plot_names, "minmax", minmax)
        else:
            # print("no minmax or plotname prefix?")
            plot_names = None
            minmax = None 
            data = msg                 
  
        plot_data = data.split(';') 
        # print("split plot data:", plot_data)  
        glist = []
        for g in plot_data:
            glist.append(g.split(','))
        # print("glist", glist)
        trace_names = []
        trace_values = []
        for g in glist:
            tr = [] # list of trace name:value tuples for each plot
            for t in g:
               tr.append(t.split(':'))
            if len(tr[0]) == 2:
                trace_name, value = zip(*tr)
            else:
                value = []
                for v in tr: 
                    value.append(float(v[0]))
                trace_name = [''] * len(value)    
            trace_names.append(trace_name) # list of trace name tuples for each plot   
            trace_values.append(value)  # list of trace values for each plot
        # print('tr names', trace_names)
        # print('tr-values', trace_values)
        data_shape = self._get_shape(trace_values)
        if data_shape != self.data_shape:
            if True: # self.data_shape == None:
                self.data_shape = self._get_shape(trace_values)
                self.nbr_plots = len(self.data_shape)
                if plot_names == None:
                    print("replacing plot names", plot_names, "with defaults")
                    self.plot_names = [''] * self.nbr_plots
                else:
                    self.plot_names = plot_names
                self.minmax = minmax
                """   
                print("new shape:", self.data_shape)
                print('plot_names',  self.plot_names)
                print('minmax', self.minmax)
                """
                return (True, trace_names, trace_values) # True indicates data has changed

        return (False, trace_names, trace_values)
    
    def _get_shape(self, data):
        #  returns list of nbr traces for each plot)
        shape = []
        for traces in data:
            shape.append(len(traces))
        # print("shape", shape) 
        return shape
  
          
    def update(self):
        self.data = None  # fixme move this to init if returning stale data 
        if self.ser and self.ser.is_open():
            if self.ser.available():
                msg = self.ser.read()
                is_format_change, self.trace_names, self.data = self.unpack_msg(msg)
        elif self.UDP_port and self.udp:
            msg = None
            while self.udp.available():
                addr, msg = self.udp.get()
            if msg:
                is_format_change, self.trace_names, self.data = self.unpack_msg(msg)
                
        if self.data:
            if len(self.data) > self.MAX_NBR_PLOTS :        
                print("\nToo many plots, change MAX_NBR_PLOTS in qt_plot_cfg.py to", len(self.data))
                sys.exit()
            return is_format_change, self.data  
        return False, None
        
        """        
        if self.data:
            if len(self.data) <= self.max_nbr_traces and len(self.data[0]) == self.nbr_plots:
                # print(self.data)   
                return self.data
            else:
                if len(self.data) > self.max_nbr_traces:
                    print("Too many data elements per plot, max is {}, got {}"
                        .format( self.max_nbr_traces, len(self.data)))
     
                else:  # len(self.data[0]) != self.nbr_plots:
                    print("\nData protocol mismatch, expected {} data field(s), got {}" 
                        .format( self.nbr_plots, len(self.data[0])))
                    print("Change data source or configured number of plots and restart")
                    print("\nData:")
                    print(self.data)    
                sys.exit()
        """
        
class UdpReceive(object):

    def __init__(self, port):
        self.in_q = Queue()
        listen_address = ('', port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
        self.sock.bind(listen_address)
        t = threading.Thread(target=self.listener_thread, args= (self.sock, self.in_q))
        t.daemon = True
        print("UDP receiver listening on port", listen_address[1])
        t.start()
        
    def available(self):
        return self.in_q.qsize()
 
    def get(self):  # returns address, msg
        if self.available():
            return self.in_q.get_nowait()
        else:
            return None

    def send(self, data, addr):
        self.sock.sendto(data.encode('utf-8'), addr)    

    def listener_thread(self, sock, in_q ):
        MAX_MSG_LEN = 1024
        while True:
            try:
                msg, addr = sock.recvfrom(MAX_MSG_LEN)
                #  print addr, msg
                msg = msg.decode('utf-8').rstrip()
                self.in_q.put((addr, msg))
            except Exception as e:
                print("Udp listen error", e)
                


TERM_CHARS = bytearray([10]) # expect newline terminated msgs 
        
class MySerial(object):
    def __init__(self, result_queue=None):
        self.queue = None #result_queue
        self.lock = threading.Lock()
        self.s = serial.Serial()
        self.is_started = False
        self.data = None    

    def open_port(self, port, bd=115200, timeout=1):
        try:
            if not self.s.isOpen():
                self.s = serial.Serial(port, bd)
                self.s.timeout = timeout
                start = time.time()
                while time.time()-start < 1.1:
                    if self.s.isOpen():
                        self.is_started = True
                        t = threading.Thread(target=self.rx_thread)
                        t.daemon = True
                        t.start()
                        # print port, "opened"
                        return True
            else:
                print(port, "already open")
        except Exception as e:
            print("Serial error: ", e)
        return False

    def close_port(self):
        self.is_started = False  # port will be closed when thread terminates

    def read(self):
        if self.queue != None:
            return self.queue.get(False)  #dont block
        else:
            data = None
            with self.lock:
                data = self.data
            return data

    def available(self):
        if self.queue != None:
            return self.queue.qsize()
        elif self.data != None:
            return 1
        else:
            return 0

    def is_open(self):
        return self.s.isOpen()

    def _read_until(self, expected=TERM_CHARS ):
        """\
        Read until an expected sequence is found (line feed by default)
        note this is running on the rx thread
        """
        lenterm = len(expected)
        line = bytearray()
        while True:
            c = self.s.read(1)
            if c:
                line += c
                if line[-lenterm:] == expected:
                    break
            else:
                break
        return bytes(line)
        
    def rx_thread(self):
        while self.is_started == True:
            try:
                data = self._read_until().decode()                                
                if data:
                    if self.queue != None:                    
                        self.queue.put(data)
                    else:
                        with self.lock: 
                            self.data = data
            except Exception as e:
                print(e)
                print("unable to read line from serial")
        self.s.close()
