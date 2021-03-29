# 
# Progam to read data from Allen Bradley PLC 
#
# Using threading to increase speed.
#
# Thomas Schwank, March/28/2021 - v0.4
#
##############################################################################


# libraries
###########
from pylogix import PLC
from csv import reader
import time
from datetime import datetime
from threading import Thread
from queue import Queue


# Settings
###########

# Allen Bradley PLC IP
plc_ip = "aaa.bbb.ccc.ddd"

# Read every x seconds:
read_s = 1

# Number of threads
ths = 4

# Filename with list of PLC addresses to read
filename = "plc_adresses.csv"


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
def read_values(msec, ad, comm, mq):
    # payload for all values
    msg = ""

    # loop over all addresses 
    for a in ad:
        r = comm.Read(a)        
        # print(r.Value)
        msg = msg  + str(r.TagName)  + ", " + str(msec) + ", " + str(r.Value) + "\r\n"

    # store results in queues
    mq.put(msg)

def main():
    
    # Init variables
    msg = ''
    end = datetime

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

    # endless loop, until code gets interrupted
    read = True
    while read:
        try:
            # msg queue for threads
            msg_queue = Queue()
            
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
                t.append(Thread(target=read_values, args=(msec, chunks[i], c[i], msg_queue)))
            
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

            
if __name__ == "__main__":
    print('\nAllen Bradley - reader started!\n')
    main()