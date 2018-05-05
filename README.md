# Domoticz-GlobalCache-Plugin
Domoticz Python Plugin for GlobalCache GC-100. Developed and tested on a GC-100-12.

Controls relays on a single GC-100 on your network.  If you have more than one you can create multiple instances of the plugin via the Hardware page, one per GC-100.

## Key Features

* Creates three Domoticz devices per GC-100, one per relay.
* Will discover the GC-100 by MAC Address so static IP is not required
* When network connectivity is lost the Domoticz UI will optionally show the device(s) with Red banner

## Installation

Python version 3.4 or higher required & Domoticz version 3.7xxx or greater.

To install:
* Go in your Domoticz directory, open the plugins directory.
* Navigate to the directory using a command line
* Run: ```git clone https://github.com/dnpwwo/Domoticz-GlobalCache-Plugin.git```
* Restart Domoticz.

In the web UI, navigate to the Hardware page.  In the hardware dropdown there will be an entry called "Global Cache 100".

## Updating

To update:
* Go in your Domoticz directory using a command line and open the plugins directory then the Domoticz-GlobalCache-Plugin directory.
* Run: ```git pull```
* Restart Domoticz.

## Configuration

| Field | Information|
| ----- | ---------- |
| MAC Address | MAC Address of the device.  Will be discovered on the network using SSDP. Enter the address without colons |
| Relay 1 Control | Dropdown allowing relays to be controled as latched on momentary, this infuences the Domoticz device type created |
| Relay 2 Control | As above |
| Relay 3 Control | As above |
| Momentary Period | Controls how long momentary relays are 'on' for before being released |
| Debug | When true the logging level will be much higher to aid with troubleshooting |

## Change log

| Version | Information|
| ----- | ---------- |
| 2.1.7 | Initial upload version |
| 2.1.8 | Uplift debugging |
| 2.2.0 | Terminate UDP Listen connection explicitly |
| 2.2.3 | Add parameter to control how many pings can be missed |
