import sys
import serial
import time

portName = "COM5"
relayNum = "1"
relayCmd = "on"
# Open port for communication
fd = serial.Serial(portName, 9600, timeout=1)
time.sleep(1)
fd.write(b"\x50")
# time.sleep(0.5)
fd.write(b"\x51")


def relay_1():
    fd.write(b"\x00")
    time.sleep(1)
    fd.write(b"\x01")


try:
    while True:
        # Toggle relay 1 on and off
        relay_1()
        time.sleep(1)  # Add a delay between operations
except KeyboardInterrupt:
    # Close the serial connection on interrupt
    fd.close()
    print("Serial connection closed")


# relay_1()
# Send the command
# fd.write(0x03)
# print("Command sent")
# Close the port
# fd.close()
