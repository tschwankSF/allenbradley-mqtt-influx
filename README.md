# allenbradley-mqtt-influx
Sample python code how to read data from Allen Bradley PLC, publish the values to MQTT and store them into InfluxDB

![abmqtt_08](https://user-images.githubusercontent.com/53979638/112776061-a1978080-900c-11eb-9d58-5e8f876dc9ca.png)

The test set up consists of an Allen Bradley PLC with simulated data for 200 assets, with each asset having three tags so 600 tags in total. Connected to the PLC is a Linux VM with Python 3.8, InfluxDB Time Series Database, MQTT Broker, and Grafana for visualization. Goal is to stay below 100ms for reading and publishing the values to MQTT and storing into InfluxDB.

All my sample code below can be found in my public GitHub repository:
https://github.com/tschwankSF/allenbradley-mqtt-influx 

Main driver for this project was that I couldn’t find a readily available and fast solution with a small enough footprint to run on a Linux Edge device, with the additional requirement to be easy to set up and configure.

The core Python library used to communicate with the Allen Bradley PLC is pylogix, available at GitHub (https://github.com/dmroeder/pylogix). 

Using this library, a single tag can be read pretty simple and fast with a handful lines of code. In below example [ab-mqtt-basics.py](ab-mqtt-basics.py) we are reading the tag ‘ASSET[1].PARTCOUNT’:

```python
# import AB PLC Library "pylogix”
from pylogix import PLC

# create PLC object
ab = PLC()

# set IP address of PLC
ab.IPAddress = 'aaa.bbb.ccc.ddd'

# read one tag
t = ab.Read('ASSET[1].PARTCOUNT')

# print values
print('Tag Name: ', t.TagName, '\nTag Value: ', t.Value)

# close connection to PLC
ab.Close()
```
