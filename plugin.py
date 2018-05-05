# Global Cache GC-100 plugin
#
# Author: Dnpwwo
#
#   API Spec: http://www.globalcache.com/files/docs/API-GC-100.pdf
#
#   Current version only supports Relay operations
#
"""
<plugin key="GC-100" name="Global Cache 100" author="dnpwwo" version="2.2.3" externallink="//http://www.globalcache.com/products/gc-100/models1/">
    <params>
        <param field="Address" label="MAC Address" width="200px" required="true" default="0000000000000"/>
        <param field="Mode1" label="Relay 1 Control" width="100px">
            <options>
                <option label="Momentary" value="Momentary" default="true"/>
                <option label="Latched" value="Latched" />
            </options>
        </param>
        <param field="Mode2" label="Relay 2 Control" width="100px">
            <options>
                <option label="Momentary" value="Momentary" default="true"/>
                <option label="Latched" value="Latched" />
            </options>
        </param>
        <param field="Mode3" label="Relay 3 Control" width="100px">
            <options>
                <option label="Momentary" value="Momentary" default="true"/>
                <option label="Latched" value="Latched" />
            </options>
        </param>
        <param field="Mode4" label="Momentary Period" width="40px">
            <options>
                <option label="1" value="1" default="true"/>
                <option label="2" value="2" />
                <option label="3" value="3" />
                <option label="4" value="4" />
                <option label="5" value="5" />
            </options>
        </param>
        <param field="Mode5" label="Ping fails before reconnect" width="40px">
            <options>
                <option label="5" value="5" default="true"/>
                <option label="10" value="10" />
                <option label="15" value="15" />
                <option label="20" value="20" />
                <option label="25" value="25" />
            </options>
        </param>
        <param field="Mode6" label="Debug" width="150px">
            <options>
                <option label="None" value="0"  default="true" />
                <option label="Python Only" value="2"/>
                <option label="Basic Debugging" value="62"/>
                <option label="Basic+Messages" value="126"/>
                <option label="Connections Only" value="16"/>
                <option label="Connections+Python" value="18"/>
                <option label="Connections+Queue" value="144"/>
                <option label="All" value="-1"/>
            </options>
        </param>
    </params>
</plugin>
"""
import Domoticz

class BasePlugin:
    enabled = False
    relayDeviceNo = -1
    lastPolled = 0
    lastResponse = 0
    GC100Conn = None
    
    def __init__(self):
        return

    def onStart(self):
        if Parameters["Mode6"] != "0":
            Domoticz.Debugging(int(Parameters["Mode6"]))
            DumpConfigToLog()

        self.GC100Conn = Domoticz.Connection(Name="Beacon", Transport="UDP/IP", Address="239.255.250.250", Port=str(9131))
        self.GC100Conn.Listen()
        Domoticz.Heartbeat(20)
        for Device in Devices:
            UpdateDevice(Device, Devices[Device].nValue, Devices[Device].sValue, 1)

    def onStop(self):
        Domoticz.Log("onStop called")

    def onConnect(self, Connection, Status, Description):
        if (Connection == self.GC100Conn):
            if (Status == 0):
                Domoticz.Log("Connected successfully to: "+Connection.Address+":"+Connection.Port)
                self.GC100Conn.Send("getdevices\r")
            else:
                if (Description.find("Only one usage of each socket address") > 0) or (Description.find("Address already in use") > 0):
                    Domoticz.Log(Connection.Address+":"+Connection.Port+" is busy, waiting.")
                else:
                    Domoticz.Log("Failed to connect ("+str(Status)+") to: "+Connection.Address+":"+Connection.Port)
                    Domoticz.Debug("Failed to connect ("+str(Status)+") to: "+Connection.Address+":"+Connection.Port+" with error: "+Description)
                self.GC100Conn = None

    def onMessage(self, Connection, Data):
        strData = Data.decode("utf-8", "ignore")

        try:
            # Beacon messages to find the GC-100
            if (Connection.Name == "Beacon"):
                dictAMXB = DecodeDDDMessage(strData)
                if (dictAMXB['SDKClass'] == "Utility") and (dictAMXB['Make'] == "GlobalCache") and (dictAMXB['Model'].find("GC-100") >= 0):
                    if (dictAMXB["UUID"].find(Parameters["Address"]) >= 0):
                        if (self.GC100Conn != None): self.GC100Conn.Disconnect()
                        self.GC100Conn = Domoticz.Connection(Name="GC-100", Transport="TCP/IP", Protocol="Line", Address=Connection.Address, Port=str(4998))
                        self.GC100Conn.Connect()
                        Domoticz.Log(dictAMXB['Make']+" - "+dictAMXB['Model']+" with UUID '"+dictAMXB["UUID"]+"' discovered successfully at address: "+Connection.Address)
                    else:
                        Domoticz.Debug("Saw discovery message for wrong GC-100")
                else:
                    try:
                        Domoticz.Log("Discovery message for Type: '"+dictAMXB['SDKClass']+"', '"+dictAMXB['Make']+", "+dictAMXB['Model']+"' seen at address: "+Connection.Address)
                    except KeyError:
                        Domoticz.Log("Discovery message '"+str(strData)+"' seen at address: "+Connection.Address)
            # Otherwise handle GC-100
            else:
                self.lastResponse = 0
                action, sep, params = strData.partition(',')

                if (action == "state"):
                    devNo, sep, nValue = params.partition(',')
                    modNo, sep, devNo = devNo.partition(':')
                    Domoticz.Debug("Device status message for module '"+modNo+"' relay '"+devNo+"': ' value: '"+nValue+"', Last update was: "+Devices[(int(modNo)*10)+int(devNo)].LastUpdate)
                    sValue = 'On'
                    if (nValue == '0'): sValue = 'Off'
                    UpdateDevice((int(modNo)*10)+int(devNo), int(nValue), sValue, 0)
                elif (action == "device"):
                    # message looks like:  'device,3,3 RELAY'
                    devNo, sep, params = params.partition(',')
                    devCount, sep, devType = params.partition(' ')
                    if (devType != "RELAY"):
                        Domoticz.Debug("Hardware reported existence of module: '"+devNo+"', of type: '"+devType+"' - Not Supported by plugin")
                    else:
                        Domoticz.Log("Hardware reported existence of module: '"+devNo+"', of type: '"+devType+"'")
                        self.relayDeviceNo = int(devNo)
                elif (action == "endlistdevices"):
                    if (self.relayDeviceNo < 0):
                        Domoticz.Error("No RELAY support reported by hardware, no devices created.")
                    else:
                        if (len(Devices) == 0):
                            if Parameters["Mode1"] == "Momentary":
                                Domoticz.Device(Name="Momentary 1",  Unit=(self.relayDeviceNo*10)+1, Type=17,  Switchtype=9).Create()
                            else:
                                Domoticz.Device(Name="Latched 1",  Unit=(self.relayDeviceNo*10)+1, TypeName="Switch").Create()
                            if Parameters["Mode2"] == "Momentary":
                                Domoticz.Device(Name="Momentary 2",  Unit=(self.relayDeviceNo*10)+2, Type=17,  Switchtype=9).Create()
                            else:
                                Domoticz.Device(Name="Latched 2",  Unit=(self.relayDeviceNo*10)+2, TypeName="Switch").Create()
                            if Parameters["Mode3"] == "Momentary":
                                Domoticz.Device(Name="Momentary 3",  Unit=(self.relayDeviceNo*10)+3, Type=17,  Switchtype=9).Create()
                            else:
                                Domoticz.Device(Name="Latched 3",  Unit=(self.relayDeviceNo*10)+3, TypeName="Switch").Create()
                            Domoticz.Log("3 Devices created. Remove unwanted devices via the 'Devices' web page.")
                    # get current state of relays
                    self.GC100Conn.Send(Message="getstate,"+str(self.relayDeviceNo)+":1\r")
                    self.GC100Conn.Send(Message="getstate,"+str(self.relayDeviceNo)+":2\r", Delay=2)
                    self.GC100Conn.Send(Message="getstate,"+str(self.relayDeviceNo)+":3\r", Delay=4)
                else:
                    Domoticz.Error("onMessage, called with unknown action: '"+str(strData)+"'")
        except Exception as inst:
            Domoticz.Error("Exception in onMessage, called with Data: '"+str(strData)+"'")
            Domoticz.Error("Exception detail: '"+str(inst)+"'")
            raise

    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Log("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))
        strUnit = str(Unit)
        modNo = strUnit[0]
        devNo = strUnit[1]
        action = "0"
        if (Command == "On"): action = "1"

        # Make sure that all momentaries are off prior to send because there may be a clash
        if (Parameters["Mode1"] == "Momentary") and (1 in Devices) and (Device[1].sValue == 'On'):
            self.GC100Conn.Send("setstate,"+modNo+":1,0\r")
        if (Parameters["Mode2"] == "Momentary") and (2 in Devices) and (Device[2].sValue == 'On'):
            self.GC100Conn.Send("setstate,"+modNo+":2,0\r")
        if (Parameters["Mode3"] == "Momentary") and (3 in Devices) and (Device[3].sValue == 'On'):
            self.GC100Conn.Send("setstate,"+modNo+":3,0\r")

        self.GC100Conn.Send("setstate,"+modNo+":"+devNo+","+action+"\r")
        # For momentary relays schedule the switch off
        if (Parameters["Mode"+devNo] == "Momentary") and (Command == 'On'):
            self.GC100Conn.Send(Message="setstate,"+modNo+":"+devNo+",0\r", Delay=int(Parameters["Mode4"]))
        
    def onDisconnect(self, Connection):
        Domoticz.Log("Hardware has disconnected.")
        self.GC100Conn = None
        for Device in Devices:
            UpdateDevice(Device, Devices[Device].nValue, Devices[Device].sValue, 1)
        return

    def onHeartbeat(self):
        Domoticz.Debug("onHeartbeat called, last response seen "+str(self.lastResponse)+" heartbeats ago.")
        if (self.GC100Conn == None):
            self.GC100Conn = Domoticz.Connection(Name="Beacon", Transport="UDP/IP", Address="239.255.250.250", Port=str(9131))
            self.GC100Conn.Listen()
        else:
            if (self.GC100Conn.Name != "Beacon"):
                if (self.GC100Conn.Connected() == False):
                    self.GC100Conn.Connect()
                else:
                    self.lastPolled = self.lastPolled + 1
                    if (self.lastPolled > 3): self.lastPolled = 1
                    self.GC100Conn.Send(Message="getstate,"+str(self.relayDeviceNo)+":"+str(self.lastPolled)+"\r")

            if (self.lastResponse > int(Parameters["Mode5"])):
                Domoticz.Error(self.GC100Conn.Name+" has not responded to "+int(Parameters["Mode5"])+" pings, terminating connection.")
                self.GC100Conn.Disconnect()
                self.GC100Conn = None
                self.lastResponse = -1
            self.lastResponse = self.lastResponse + 1
                    
global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)

def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)

def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)

def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

    # Generic helper functions
def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug( "'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
    return
    
def UpdateDevice(Unit, nValue, sValue, TimedOut):
    # Make sure that the Domoticz device still exists (they can be deleted) before updating it 
    if (Unit in Devices):
        if (Devices[Unit].nValue != nValue) or (Devices[Unit].sValue != sValue) or (Devices[Unit].TimedOut != TimedOut):
            Devices[Unit].Update(nValue=nValue, sValue=str(sValue), TimedOut=TimedOut)
            Domoticz.Log("Update "+str(nValue)+":'"+str(sValue)+"' ("+Devices[Unit].Name+")")
    return

def DecodeDDDMessage(Message):
    # Sample discovery message
    # AMXB<-SDKClass=Receiver><-Make=DENON><-Model=AVR-4306>
    strChunks = Message.strip()
    strChunks = strChunks[4:len(strChunks)-1].replace("<-","")
    dirChunks = dict(item.split("=") for item in strChunks.split(">"))
    return dirChunks
