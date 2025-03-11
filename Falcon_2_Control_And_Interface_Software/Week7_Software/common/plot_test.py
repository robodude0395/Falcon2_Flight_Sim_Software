# plot_test.py


from plot_itf import PlotItf

import math
import time
from random import randint

    def __init__(self, nbr_traces, min_max):
        self.nbr_traces = nbr_traces
        self.max_value = (min_max[1]-min_max[0])/2
        self.base_frequency = 1 #hz
        self.interval = .05 # seconds
        self.step = randint(0,7)
        self.amplitudes = []
        for i in range(nbr_traces):
            self.amplitudes.append(randint(1, self.max_value))
            

class DummyData():
    def __init__(self, nbr_traces, max_amplitude):
        self.nbr_traces = nbr_traces
        self.max_value = max_amplitude
        self.base_frequency = 1 #hz
        self.interval = .05 # seconds
        self.step = randint(0,7)
        self.amplitudes = []
        for i in range(nbr_traces):
            self.amplitudes.append(randint(1, self.max_value))
    
    def get(self):
        # return trace data for this plot
        data = []
        for i in range(self.nbr_traces):
            value = self._get_wave(self.step + (i*3), self.base_frequency + (i * .5 ), self.amplitudes[i])
            data.append(value)
        self.step += 1    
        return data
            
    def _get_wave(self, step, frequency, amplitude):
        degrees = frequency * 360 * step * self.interval    
        rad = math.radians(degrees)
        deg2 = frequency * 360 * (step + 11) * self.interval  
        rad2 =  math.radians(deg2)
        return (math.sin(rad) + math.sin(rad2))*amplitude


while(True):
    main_title = input("Enter string for main title (or Return for defualt) ")
    if main_title=='':main_title=None
    nbr_plots = int(input("Enter number of plots (1-12) "))
    plot_titles = input("Enter {} comma seperated plot names (or Return for defaults)".format(nbr_plots))
    if plot_titles=='':
        plot_titles = None
    else:
        plot_titles = plot_titles.split(',')
    nbr_traces = int(input("Enter number of traces per plot (1-9) "))
    trace_names = input("Enter {} comma seperated trace names (or Return for defaults)".format(nbr_traces))
    if trace_names=='':
        trace_names = None
    else:
        trace_names = trace_names.split(',')    
    print("todo min max")

    plotter = PlotItf( nbr_plots, nbr_traces, main_title=main_title, plot_titles=plot_titles, legends=trace_names, minmax=None)
    
    dummy_data  = []
    for i in range(nbr_plots):
        dummy_data.append(DummyData(nbr_traces, randint(1,100)))
    for data_points in range(50):   
        data = []
        for i in range(nbr_plots):
            data.append(dummy_data[i].get())      
   
        plotter.plot(data)
        time.sleep(.01)
        # print(data)


"""
dur = 3 # second
interval = .05 # seconds

max_amplitude = 4 # used to generate waves
min_max = (-10,10) # passed to plotter to set scale  



    for i in range(nbr_plots):
        plot = DummyData(plot_names[i], randint(1, 6), frequency,  max_amplitude)
        plots.append(plot)
        # next line creates plot prefixes that includ emin/max scale
        plot_prefixes.append( '{}:{};{}'.format(plot_names[i], min_max[0], min_max[1]))
    prefix = ','.join( prefex for prefex in plot_prefixes)
    print("prefix=", prefix)


    for step in range(int(dur/interval)):
        trace_data = []
        for plot in  plots:
            trace_data.append(plot.get_data(step))
        main_title =   'MAIN_TITLE=Test with {} Plots,'.format(len(plots))
        msg = main_title + prefix + '#' + ';'.join(trace for trace in trace_data)        
        # print(msg) 
        udp_send(msg.encode(), ('192.168.1.117',10029))  
        time.sleep(.05)    
 """ 
"""
def simple_udp_example()
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    HOST = '127.0.0.1' # address of host running qt_plot
    
    udp_send(msg.encode(data), (HOST,10029)) # send to local host    
"""

    