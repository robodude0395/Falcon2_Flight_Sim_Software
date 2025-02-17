"""
PI_Mdx_controls.py
flight sim panael Input / Output

command msg format:  'cmd;{"Parking_brake":(0/1),"Landing_gear":(0/1),"Flaps":(0..1),"Throttle":(0..1),"Mixture":(0..1)}\n'  
event msg format     'evt;{"Parking_brake":(0/1),"Landing_gear":(0/1),"Flaps":(0..1),"Throttle":(0..1),"Mixture":(0..1)}\n'  

"""

from XPPython3 import xp
from udp_tx_rx import UdpReceive
import json
import socket
import numpy as np

LISTEN_PORT = 10022  # port to listen on, default sender is 10025
                         

class PythonInterface:
    def XPluginStart(self):
        self.Name = "InputOutput1 v.01"
        self.Sig = "FlightPanel.Python.InputOutput1"
        self.Desc = "A plug-in that handles data Input/Output."


        self.udp = UdpReceive(LISTEN_PORT)
        self.sender = None # address,port tuple  of command message senser
        
        self.fields =  ('x_accel',        'y_accel',      'z_accel', 'roll_rate', 'pitch_rate', 'yaw_rate', 'bank_angle', 'pitch_angle')
        self.cmd_cache = [0,              0,              0,          0,           0,            0,         0,             0] # cache received command values
        self.cmd_values = self.cmd_cache
        self.OutputEdit = self.cmd_cache

        # Create our menu
        Item = xp.appendMenuItem(xp.findPluginsMenu(), "Python - Input/Output 1", 0)
        self.InputOutputMenuHandlerCB = self.InputOutputMenuHandler
        self.Id = xp.createMenu("Telemetry Display", xp.findPluginsMenu(), Item, self.InputOutputMenuHandlerCB, 0)
        xp.appendMenuItem(self.Id, "Data", 1)

        # Flag to tell us if the widget is being displayed.
        self.MenuItem1 = 0
       
        # Register our FL callbadk with initial callback freq of 1 second
        self.InputOutputLoopCB = self.InputOutputLoopCallback
        xp.registerFlightLoopCallback(self.InputOutputLoopCB, 0.02, 0)

        return self.Name, self.Sig, self.Desc

    def XPluginStop(self):
        # Unregister the callback
        xp.unregisterFlightLoopCallback(self.InputOutputLoopCB, 0)

        if self.MenuItem1 == 1:
            xp.destroyWidget(self.InputOutputWidget, 1)
            self.MenuItem1 = 0

        xp.destroyMenu(self.Id)
        self.udp.close()

    def XPluginEnable(self):
        return 1

    def XPluginDisable(self):
        pass

    def XPluginReceiveMessage(self, inFromWho, inMessage, inParam):
        pass

    def InputOutputLoopCallback(self, elapsedMe, elapsedSim, counter, refcon):
        self.service_msgs()

        # Process each field
        for Item in range(len(self.fields)):
            value = self.cmd_values[Item]
            if(Item > 2):
                xp.setWidgetDescriptor(self.OutputEdit[Item], str(value*180/np.pi))
            else:
                xp.setWidgetDescriptor(self.OutputEdit[Item], str(value))
        
        return 0.1  

    def InputOutputMenuHandler(self, inMenuRef, inItemRef):
        # If menu selected create our widget dialog
        if inItemRef == 1:
            if self.MenuItem1 == 0:
                self.CreateInputOutputWidget(300, 550, 350, 400)
                self.MenuItem1 = 1
            else:
                if not xp.isWidgetVisible(self.InputOutputWidget):
                    xp.showWidget(self.InputOutputWidget)

    """
    This will create our widget dialog.
    I have made all child widgets relative to the input paramter.
    This makes it easy to position the dialog
    """
    def CreateInputOutputWidget(self, x, y, w, h):
        x2 = x + w
        y2 = y - h

        print("PENIS")

        # Create the Main Widget window
        self.InputOutputWidget = xp.createWidget(x, y, x2, y2, 1, "Flight Control interface by Middlesex University",
                                                 1, 0, xp.WidgetClass_MainWindow)

        # Add Close Box decorations to the Main Widget
        xp.setWidgetProperty(self.InputOutputWidget, xp.Property_MainWindowHasCloseBoxes, 1)

        # Create the Sub Widget window
        InputOutputWindow = xp.createWidget(x + 50, y - 50, x2 - 50, y2 + 50, 1, "",
                                            0, self.InputOutputWidget, xp.WidgetClass_SubWindow)

        # Set the style to sub window
        xp.setWidgetProperty(InputOutputWindow, xp.Property_SubWindowType, xp.SubWindowStyle_SubWindow)

        # For each field
        InputText = []
        self.OutputEdit = [] # values from xplane
        for Item in range(len(self.fields)):
            # Create a text widget
            InputText.append(xp.createWidget(x + 60, y - (60 + (Item * 30)), x + 90, y - (82 + (Item * 30)), 1,
                                             self.fields[Item], 0, self.InputOutputWidget, xp.WidgetClass_Caption))
            
            # Create an edit widget values to the panel
            self.OutputEdit.append(xp.createWidget(x + 150, y - (60 + (Item * 30)), x + 230, y - (82 + (Item * 30)), 1,
                                                   "", 0, self.InputOutputWidget, xp.WidgetClass_TextField))

            # Set it to be text entry
            xp.setWidgetProperty(self.OutputEdit[Item], xp.Property_TextFieldType, xp.TextEntryField)

        yIndex = len(self.fields)
        xp.createWidget(x + 60, y - (60 + (yIndex * 30)), x + 90, y - (82 + (yIndex * 30)), 1,
                                             'Listening on port {}'.format(LISTEN_PORT), 0, self.InputOutputWidget, xp.WidgetClass_Caption)
                                             
        # Register our widget handler
        self.InputOutputHandlerCB = self.InputOutputHandler
        xp.addWidgetCallback(self.InputOutputWidget, self.InputOutputHandlerCB)

    def InputOutputHandler(self, inMessage, inWidget, inParam1, inParam2):
        if inMessage == xp.Message_CloseButtonPushed:
            if self.MenuItem1 == 1:
                xp.hideWidget(self.InputOutputWidget)
            return 1

        return 0

    def GetDataRefState(self, DataRefID, isArray = False):
        if isArray:
            self.IntVals = []
            xp.getDatavi(DataRefID, self.IntVals, 0, 8)
            DataRefi = self.IntVals[0]
        else:
            DataRefi = xp.getDatai(DataRefID)

        return DataRefi

    def SetDataRefState(self, DataRefID, State, isArray = False):
        if isArray:
            IntVals = [State, 0, 0, 0, 0, 0, 0, 0]
            xp.setDatavi(DataRefID, IntVals, 0, 8)
        else:
            xp.setDatai(DataRefID, State)
            
    def service_msgs(self):
        while self.udp.available() > 0:
            self.sender,payload = self.udp.get()
            # print( self.sender,payload)
            try:
                parts = payload.split(',')
                telemetry_vals = [float(num) for num in parts[1:]]
                self.cmd_values = telemetry_vals

            except Exception as e:
                xp.log(str(e)) 