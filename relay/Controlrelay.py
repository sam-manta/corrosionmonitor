import serial
import time

ser = serial.Serial("COM3", 9600, timeout=1)
print(ser.is_open)


def relay_on(channel):
    if 1 <= channel <= 8:
        command = bytearray([0xFF, 0x01, channel, 0x01])
        ser.write(command)


def relay_off(channel):
    if 1 <= channel <= 8:
        command = bytearray([0xFF, 0x01, channel, 0x00])
        ser.write(command)


# Example usage:
try:
    while True:
        # Turn relay 1 on
        relay_on(1)
        time.sleep(1)
        # Turn relay 1 off
        relay_off(1)
        time.sleep(1)
except KeyboardInterrupt:
    # Close the serial connection
    ser.close()
