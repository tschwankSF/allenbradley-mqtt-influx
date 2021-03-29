# import AB PLC Library "pylogix". 
# details about pylogix: https://github.com/dmroeder/pylogix 
from pylogix import PLC

# create PLC object
ab = PLC()

# set IP address of PLC
ab.IPAddress = 'aaa.bbb.ccc.ddd'

# read one tag
t = ab.Read('ASSET[1].PARTCOUNT')

# print values
print('\nTag Name: ', t.TagName, '\tTag Value: ', t.Value, '\n')

# close connection to PLC
ab.Close()