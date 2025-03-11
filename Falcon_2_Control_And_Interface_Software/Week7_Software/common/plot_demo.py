# plot_demo.py


from plot_itf import PlotItf

import math
import time
from random import randint


dur = 3 # second
interval = .05 # seconds
trace_names = ('trace 1', 'trace 2', 'trace 3') # , 'trace 4', 'trace 5', 'trace 6')
nbr_traces = len(trace_names)
frequency = 1 # hz
max_amplitude = 4 # used to generate waves
min_max = (-10,10) # passed to plotter to set scale
plot_names = ('plot1', 'plot2', 'plot3', 'plot4', 'plot5', 'plot6', 'plot7', 'plot8', 'plot9', 'plot10')
nbr_plots = 6 #  len(plot_names)

   
base_frequency = 1 # hz
    

class DummyData():
    def __init__(self, nbr_traces, max_amplitude):
        self.nbr_traces = nbr_traces
        self.base_frequency = base_frequency
        self.max_value = max_amplitude
        self.step = randint(0,7)
        self.amplitudes = []
        for i in range(nbr_traces):
            self.amplitudes.append(randint(1, max_amplitude))
    
    def get(self):
        # return trace data for this plot
        data = []
        for i in range(self.nbr_traces):
            value = self._get_wave(self.step + (i*3), self.base_frequency + (i * .5 ), self.amplitudes[i])
            data.append(value)
        self.step += 1    
        return data
            
    def _get_wave(self, step, frequency, amplitude):
        degrees = frequency * 360 * step * interval    
        rad = math.radians(degrees)
        deg2 = frequency * 360 * (step + 11) * interval  
        rad2 =  math.radians(deg2)
        return (math.sin(rad) + math.sin(rad2))*amplitude

"""

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
main_title =  "test"
nbr_plots = 2
titles = ['plot','plot2']  # comma needed even if only one plot
traces_per_plot =3
plotter = PlotItf( nbr_plots, traces_per_plot, main_title=main_title)
dummy_data  = []
for i in range(nbr_plots):
    dummy_data.append(DummyData(traces_per_plot, randint(1,100)))

data = []
for i in range(nbr_plots):
    data.append(dummy_data[i].get()) 
print("wha", data)    
plotter.plot(data)
    
def simple_plot_itf_example():
    # one plot each with two traces
    main_title =  "one plot each with two autoscaling traces"
    nbr_plots = 1
    plot_titles = 'plot',  # comma needed even if only one plot
    traces_per_plot = 2
    trace_names= ('trace1', 'trace2')
    
    dummy_data = DummyData(traces_per_plot, randint(1,100))
    # plotter = PlotItf( nbr_plots, traces_per_plot, main_title, plot_titles, legends=trace_names)
    plotter = PlotItf( nbr_plots, traces_per_plot, main_title=main_title )
    for step in range(50):
        data = dummy_data.get() # get a list of trace data values
        print(data)
        plotter.plot(data)
        time.sleep(.01)

# simple_plot_itf_example()
"""    

def two_plots():
    # two plots each with three traces
    main_title = "two plots each with three traces"
    nbr_plots = 2
    titles = 'plot1', 'plot2'), 
    traces_per_plot = 3
    trace_names= ('trace1', 'trace2', 'trace3')



    self.plotter = PlotItf(main_title, nbr_plots, titles, traces_per_plot, legends=trace_names,  minmax=(0,100), grouping= 'traces')
     
           

           nbr_plots = 6
            traces_per_plot = 2
            titles = ('Strut 0', 'Strut 1',  'Strut 2',  'Strut 3',  'Strut 4',  'Strut 5')                 
            legends = ('Distance', 'Pressure')
            main_title = "Distance and pressure vacd lues for platform actuators"
            self.plotter = PlotItf(main_title, nbr_plots, titles, traces_per_plot, legends=legends,  minmax=(0,100), grouping= 'traces')


    self.plotter = PlotItf(main_title, nbr_plots, titles, traces_per_plot, legends=legends,  minmax=(0,100), grouping= 'traces')
    
    def do_plot(self, distances, percents, out_pressures):
        trace1 = [d/2 for d in distances]
        trace2 = [p/60 for p in out_pressures]
        self.plotter.plot([trace1, trace2])  
"""        