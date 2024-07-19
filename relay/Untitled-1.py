import sys
import serial
import time

portName = "COM5"
relayNum = "1"
relayCmd = "on"
# Open port for communication
fd = serial.Serial(portName, 9600, timeout=1)
time.sleep(1)
# fd.write(0x50)
# time.sleep(0.5)
# fd.write(0x51)


def relay_1():
    fd.write(0x00)
    time.sleep(1)
    fd.write(0x01)


# relay_1()
# Send the command
fd.write(0x01)
print("Command sent")
# Close the port
# fd.close()
