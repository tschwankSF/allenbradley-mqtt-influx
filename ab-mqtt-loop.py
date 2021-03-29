# imports
from pylogix import PLC
from csv import reader
import time

# settings
##########

# Allen Bradley PLC IP
plc_ip = "aaa.bbb.ccc.ddd"


# Filename with list of PLC addresses to read
filename = "plc_adresses.csv"

# read list of PLC adresses to read
def read_addresses(filename):
    addresses = []
    with open(filename,'r') as data:
        for row in reader(data):
            addresses.append(row[0])
    return addresses

def main():
    # read addresses from file
    addresses = read_addresses(filename)

    with PLC() as ab:
        ab.IPAddress = plc_ip

        read = True
        while read:
            try:
                start = int(time.time() * 1000)
                # loop over addresses
                for a in addresses:
                    # get value from PLC
                    v = ab.Read(a)
                    # print('Tag Name: ', v.TagName, 'Tag Value: ', v.Value)
                print('Time needed to read ', len(addresses), ' Tags: ', str(int(time.time() * 1000) - start) + ' milliseconds')
                
                time.sleep(1)
            
            # loop until interrupedt by Ctrl+C
            except KeyboardInterrupt:
                read = False
                print("Done!")
                    
if __name__ == "__main__":
    print('\n\nAllen Bradley - reader started!\n\n')
    main()
