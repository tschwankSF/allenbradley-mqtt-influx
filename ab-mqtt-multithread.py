# 
# Progam to read data from Allen Bradley PLC and publish to MQTT.
#
# Using threading to increase speed
#
# Two topics will be used for publishing:
#
# 1) Topic which gets values from all adresses, independent if they changed
#    or not changed since last read
# 2) Topic which gets values only from adresses which changed since last read
#
# In addition values gets stored in local InfluxDB Time Series Database, V1.8+ 
#
# Thomas Schwank, March/28/2021 - v0.4
#
##############################################################################


# libraries
###########
from pylogix import PLC
import paho.mqtt.client as paho
from csv import reader
import time
from datetime import datetime
from threading import Thread
from queue import Queue
from influxdb_client import InfluxDBClient, Point


# Settings
###########

# Allen Bradley PLC IP
plc_ip = "aaa.bbb.ccc.ddd"

# Read every x seconds:
read_s = 1

# Number of threads
ths = 4

# batch size for PLC value reading
n = 50

# MQTT Broker IP
broker_address = "127.0.0.1"

# Name of MQTT topic for publishing all values (independent if they changed from last read cycle)
ab_all = "ab_all"
ab_all_active = False

# Name of MQTT topic for publishing only values which changed from last cycle
ab_changed = "ab_changed"
ab_changed_active = True

# Filename with list of PLC addresses to read
filename = "plc_adresses.csv"

# Influx
write_to_influx = False

username = '<username>'
password = '<password>'

database = 'ab'
retention_policy = 'autogen'

bucket = f'{database}/{retention_policy}'

# read list of PLC adresses to read
def read_addresses(filename):
    addresses = []
    with open(filename,'r') as data:
        for row in reader(data):
            addresses.append(row[0])
    return addresses

# split list af addresses in chuncks for multithreading
def split(a, n):
    k, m = divmod(len(a), n)
    return (list(a[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(n)))


# read data from Allen Bradley PLC
def read_values(msec, ad, comm, lvalues, mq, mqc, lq, n, iapi):
    # payload for all values
    msg = ""

    # payload for changed values only
    msg_changes = ""    

    # split list in batches for batch reading
    x = list([ad[i:i + n] for i in range(0, len(ad), n)])

    # loop over all batches  
    for a in x:

        # read values from addresses in batch
        ret = comm.Read(a)

        # loop over all individual adreses from batch read
        for r in ret:
            # print(r.Value)
            msg = msg  + str(r.TagName)  + ", " + str(msec) + ", " + str(r.Value) + "\r\n"

            # check if we read addess for first time
            if r.TagName not in lvalues.keys():
                lvalues[r.TagName] = ''
           
            # check if value for tag changed since last read
            if r.Value != lvalues[r.TagName]:
                msg_changes = msg_changes  + str(r.TagName) + ", " + str(msec) + ", " + str(r.Value) + "\r\n"

                # write to Influx
                if write_to_influx:
                    x = r.TagName.split('.')
                    point = Point(x[0]).field(x[1], r.Value)
                    iapi.write(bucket=bucket, record=point)
           
            # store values for next read run
            lvalues[r.TagName] = r.Value

    # store results in queues
    mq.put(msg)
    mqc.put(msg_changes)
    lq.put(lvalues)

def main():
    
    # Init variables
    msg = ''
    msg_changes = ''
    last_values = {}
    end = datetime

    # MQTT Settings all values
    client = paho.Client("ab")
    client.connect(broker_address)

    # Create Influx Client
    if write_to_influx:    
        influx = InfluxDBClient(url='http://localhost:8086', token=f'{username}:{password}', org='-')
        influx_api = influx.write_api()
    else:
        influx_api = ''

    # Read from txt file which adresses to read from PLC
    addresses = read_addresses(filename)
    
    # Split addresses in chuncks for multi threading, one chunck for each thread
    chunks = list(split(addresses, ths))
    
    # create one PLC object for each tread    
    c = []
    for i in range(ths):
        com = PLC()
        com.IPAddress = plc_ip
        com.ConnectionSize = 4000
        c.append(com)

    # dict to store last values
    ld = {}

    # endless loop, until code gets interrupted
    read = True
    while read:
        try:
            # msg queue for threads
            msg_queue = Queue()
            msg_queue_changed = Queue()

            # queue to get last values from threads
            last_queue = Queue()
            
            # time when reads started 
            start = datetime.now()
            start_s = time.time()

            # epoche/UTC time in milliseconds for time stamp of read values
            msec = str(int(start_s * 1000))
            
            # store time of last read, for statistics only
            last = end

            # create threads
            t =[]
            for i in range(ths):
                t.append(Thread(target=read_values, args=(msec, chunks[i], c[i], ld, msg_queue, msg_queue_changed, last_queue, n, influx_api)))
            
            # start threads
            for i in range(ths):
                t[i].start()
            
            # join thread
            for i in range(ths):
                t[i].join()

            # read values from queue from each thread
            msg = ''
            for i in range(msg_queue.qsize()):
                msg = msg + msg_queue.get()

            # read changed values from queue from each thread
            msg_changes = ''
            for i in range(msg_queue_changed.qsize()):
                msg_changes = msg_changes + msg_queue_changed.get()

            # merge last values from all threads
            for i in range(last_queue.qsize()):
                ld.update(last_queue.get()) 

            # Publich to two different topics
            if ab_all_active:
                client.publish(ab_all,payload=msg,qos=0)
            
            if ab_changed_active:
                client.publish(ab_changed,payload=msg_changes,qos=0)
            
            # Loop ended, all adresses are read and published    
            end = datetime.now()

            # Calculate how long to sleep before next read
            sleep_s = (read_s - (time.time() - start_s))

            # Some statistics
            print("Time needed reading all tags:\t", str(int((time.time() - start_s)*1000)) + ' milliseconds')
            print("Tags:\t\t\t\t", len(addresses))
            print("Parallel Threads:\t\t", ths)
            print("Start next cycle in:\t\t", str(int(sleep_s * 1000)) + ' milliseconds', "\n")

            # If we needed longer for reads than required cycle time, read immediatly again
            if sleep_s < 0: sleep_s = 0
            
            # Sleep until next read
            time.sleep(sleep_s)

        except KeyboardInterrupt:
            print('\n Program exiting')
            read = False
            client.disconnect()
            influx_api.close()
            
if __name__ == "__main__":
    print('\n\nAllen Bradley - MQTT publisher started!\n#######################################\n\n\n')
    main()