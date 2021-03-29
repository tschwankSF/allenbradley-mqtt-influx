## Sample Python code how to read data from Allen Bradley PLC, publish the values to MQTT and store them into InfluxDB

![abmqtt_08](https://user-images.githubusercontent.com/53979638/112776061-a1978080-900c-11eb-9d58-5e8f876dc9ca.png)

The test set up consists of an Allen Bradley PLC with simulated data for 200 assets, with each asset having three tags so 600 tags in total. Connected to the PLC is a Linux VM with Python 3.8, InfluxDB Time Series Database, MQTT Broker, and Grafana for visualization. Goal is to stay below 100ms for reading and publishing the values to MQTT and storing into InfluxDB.

A more detailed decription can be foud in this article: [Medium Article](https://thomas-schwank.medium.com/how-to-read-and-store-600-addresses-from-an-allen-bradley-plc-in-40-milliseconds-using-python-df8eb4da0399)

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

## This repository contains the following additional examples:

* Importing a csv file with PLC addresses to read and reading them in an endless loop every one second, took about 400ms for 600 tags on my test system.
  * [ab-mqtt-loop.py](ab-mqtt-loop.py) 
* Taking code above and spinning up threads, reduce time to read 600 tags from 400ms to 200ms
  * [ab-mqtt-multithread-part01.py](ab-mqtt-multithread-part01.py) 
* Last change was to read addresses from PLC in batch, reducing the cycle time to about 40ms for the 600 tags.
  * [ab-mqtt-multithread.py](ab-mqtt-multithread.py)

## The last example also includes the code:

* to check if value for an address change since previous read
* publish values to MQTT, two different topics:
  * One topic “ab_all” will get all values, doesn’t matter if they changed or not since the last read. For some streaming analytics job it is easier if they get all values in one message to run their algorithms.
  * For other consumers like a Time Series database it is better to get only values when they changed, and for this use cases below code publishes only the changed values into a topic called “ab_changed”
* Stores the values into InfluxDB Time Series DB. I used Version 1.8 in this example.  

Thanks for your interest, feel free to contact me if you have questions or any other feedback.
