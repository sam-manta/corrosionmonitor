"""
File:                       Corrpotential.py

Library Call Demonstrated:  mcculw.ul.a_in_scan() in Background mode with scan
                            option mcculw.enums.ScanOptions.BACKGROUND and, if
                            supported, mcculw.enums.ScanOptions.SCALEDATA

Purpose:                    Scans a range of A/D Input Channels and stores
                            the sample data in an array.

Demonstration:              Displays the analog input on up to four channels.

Other Library Calls:        mcculw.ul.win_buf_alloc()
                                or mcculw.ul.win_buf_alloc_32()
                                or mcculw.ul.scaled_win_buf_alloc()
                            mcculw.ul.win_buf_free()
                            mcculw.ul.get_status()
                            mcculw.ul.stop_background()
                            mcculw.ul.release_daq_device()

Special Requirements:       Device must have an A/D converter.
                            Analog signals on up to four input channels.
"""

## Import packages
from __future__ import absolute_import, division, print_function
from builtins import *  # @UnusedWildImport

from time import sleep
from ctypes import cast, POINTER, c_double, c_ushort, c_ulong

from mcculw import ul
from mcculw.enums import ScanOptions, FunctionType, Status
from mcculw.device_info import DaqDeviceInfo

try:
    from console_examples_util import config_first_detected_device
except ImportError:
    from .console_examples_util import config_first_detected_device

import schedule
import time
import keyboard
import datetime

## For the relay
import sys
import serial

## Functions


def maketxtfile(relaynumber, typeofmeasurament):
    # This function opens a txt file with the sample number and writes down
    # the title + extra infor
    if typeofmeasurament == 0:
        file_name = "potential_measurament_{}.txt".format(relaynumber + 1)
        typem = "Potential measurament V"
    else:
        file_name = "corrosion_current_{}.txt".format(relaynumber + 1)
        typem = "Corrosion current -10mV/microAmpere"

    current_time = time.strftime("%H:%M:%S", time.localtime())
    today = datetime.date.today()
    file = open(file_name, "w")
    file.write("First point of data acquisition:\n")
    writetheday = "{}, {}\n".format(today, current_time)
    file.write(writetheday)
    file.write("Sample n. {}, {}. \n".format(relaynumber + 1, typem))
    file.write("Ch1 V, Ch2 V, Time\n")

    file.close()
    return file_name


def openrelay(relay_n, fd):
    print("opening relay n.{}".format(relay_n))

    command = 2 * relay_n - 1
    # if relay_n < 6:
    # command = "0{}".format(2 * relay_n - 1)
    # else:
    # command = "{}".format(2 * relay_n - 1)

    fd.write(bytes([command]))
    time.sleep(1)


def closerelay(relay_n, fd):
    print("closing relay n.{}".format(relay_n))

    command = 2 * relay_n
    # if relay_n < 5:
    #    command = "0{}".format(2 * relay_n - 1)
    # else:
    #    command = "{}".format(2 * relay_n - 1)

    fd.write(bytes([command]))
    time.sleep(1)


def collectdatafromsensor(file_name, ch_number):
    # Detects and displays all available devices and
    # selects the first device listed. Use the dev_id_list variable to filter
    # detected devices by device ID (see UL documentation for device IDs).
    # If use_device_detection is set to False, the board_num variable needs to
    # match the desired board number configured with Instacal.
    print("Function is running", flush=True)

    use_device_detection = True
    dev_id_list = []
    board_num = 0
    rate = 100
    points_per_channel = 1000
    memhandle = None
    print_to_csv_data = []

    try:
        if use_device_detection:
            config_first_detected_device(board_num, dev_id_list)

        daq_dev_info = DaqDeviceInfo(board_num)
        if not daq_dev_info.supports_analog_input:
            raise Exception("Error: The DAQ device does not support " "analog input")

        print(
            "\nActive DAQ device: ",
            daq_dev_info.product_name,
            " (",
            daq_dev_info.unique_id,
            ")\n",
            sep="",
        )

        ai_info = daq_dev_info.get_ai_info()

        low_chan = 0
        high_chan = min(3, ai_info.num_chans - 1)
        num_chans = high_chan - low_chan + 1

        total_count = points_per_channel * num_chans

        ai_range = ai_info.supported_ranges[0]

        scan_options = ScanOptions.BACKGROUND

        if ScanOptions.SCALEDATA in ai_info.supported_scan_options:
            # If the hardware supports the SCALEDATA option, it is easiest to
            # use it.
            scan_options |= ScanOptions.SCALEDATA

            memhandle = ul.scaled_win_buf_alloc(total_count)
            # Convert the memhandle to a ctypes array.
            ctypes_array = cast(memhandle, POINTER(c_double))
        elif ai_info.resolution <= 16:
            # Use the win_buf_alloc method for devices with a resolution <= 16
            memhandle = ul.win_buf_alloc(total_count)
            # Convert the memhandle to a ctypes array.
            ctypes_array = cast(memhandle, POINTER(c_ushort))
        else:
            # Use the win_buf_alloc_32 method for devices with a resolution > 16
            memhandle = ul.win_buf_alloc_32(total_count)
            # Convert the memhandle to a ctypes array.
            ctypes_array = cast(memhandle, POINTER(c_ulong))

        # Note: the ctypes array will no longer be valid after win_buf_free is
        # called.
        # A copy of the buffer can be created using win_buf_to_array or
        # win_buf_to_array_32 before the memory is freed. The copy can be used
        # at any time.

        # Check if the buffer was successfully allocated
        if not memhandle:
            raise Exception("Error: Failed to allocate memory")

        # Start the scan
        ul.a_in_scan(
            board_num,
            low_chan,
            high_chan,
            total_count,
            rate,
            ai_range,
            memhandle,
            scan_options,
        )

        # Create a format string that aligns the data in columns
        row_format = "{:>12}" * (2)
        # num_chans

        # Print the channel name headers
        labels = []
        # for ch_num in range(low_chan, high_chan + 1):
        for ch_num in range(2):
            labels.append("CH" + str(ch_num))
        print(row_format.format(*labels))

        # Start updating the displayed values
        status, curr_count, curr_index = ul.get_status(
            board_num, FunctionType.AIFUNCTION
        )
        while status != Status.IDLE:
            # Make sure a data point is available for display.
            if curr_count > 0:
                # curr_index points to the start of the last completed
                # channel scan that was transferred between the board and
                # the data buffer. Display the latest value for each
                # channel.
                display_data = []
                # Change the range based on potential or current
                if ch_number == 0:
                    record_channel = curr_index

                else:
                    record_channel = curr_index + 2

                for data_index in range(record_channel, record_channel + 2):
                    # Change this so that it only reads channel 1 and 2 and alternative 3 and 4.
                    if ScanOptions.SCALEDATA in scan_options:
                        # If the SCALEDATA ScanOption was used, the values
                        # in the array are already in engineering units.
                        eng_value = ctypes_array[data_index]
                    else:
                        # If the SCALEDATA ScanOption was NOT used, the
                        # values in the array must be converted to
                        # engineering units using ul.to_eng_units().
                        eng_value = ul.to_eng_units(
                            board_num, ai_range, ctypes_array[data_index]
                        )
                    display_data.append("{:.3f}".format(eng_value))
                    timestamp = "{:%Y-%m-%d %H:%M:%S}".format(datetime.datetime.now())
                display_data.append(timestamp)
                print(row_format.format(*display_data))
                print_to_csv_data.append(display_data)

            # Wait a while before adding more values to the display.
            sleep(0.5)

            status, curr_count, curr_index = ul.get_status(
                board_num, FunctionType.AIFUNCTION
            )

        # Stop the background operation (this is required even if the
        # scan completes successfully)
        ul.stop_background(board_num, FunctionType.AIFUNCTION)

        print("Scan completed successfully")

    except Exception as e:
        print("\n", e)
    finally:
        if memhandle:
            # Free the buffer in a finally block to prevent a memory leak.
            ul.win_buf_free(memhandle)
        if use_device_detection:
            ul.release_daq_device(board_num)
    # Print to file
    with open(file_name, "a") as file:
        for inner_list in print_to_csv_data:
            line = ",".join(inner_list)
            file.write(line + "\n")


def mainfunction():
    # This function takes care of switching on and off the relays and
    # saving to file the collected data. It should run every some minutes.
    print("runs every 20 minutes")
    relaynumber = 3
    portName = "COM5"

    # Open port for communication
    fd = serial.Serial(portName, 9600, timeout=1)
    time.sleep(1)
    fd.write(b"\x50")
    # Reads device identification
    time.sleep(0.5)
    fd.write(b"\x51")
    # Device ready

    for j in range(2):
        if j == 0:
            ch_number = 0
            file_n = "potential_measurament_"
            closerelay(j + 7, fd)
        else:
            ch_number = 2
            file_n = "corrosion_current_"
            openrelay(j + 6, fd)

        for i in range(relaynumber):
            file_name = "{}{}.txt".format(file_n, i + 1)
            openrelay(i + 1, fd)
            openrelay(i + 4, fd)
            collectdatafromsensor(file_name, ch_number)
            closerelay(i + 1, fd)
            closerelay(i + 4, fd)

    fd.close()
    print("Serial connection closed")


# Main
relaynumber = 3


# One extra relay opens and close for potential (off) and current (on), relay 7

# Move this inside mainfuction
for j in range(2):
    for i in range(relaynumber):
        maketxtfile(i, j)

mainfunction()
schedule.every(10).minutes.do(mainfunction)
print("Press 'q' to stop the script.")

while True:
    schedule.run_pending()
    time.sleep(1)
    if keyboard.is_pressed("q"):  # Check if 'q' key is pressed
        print("Script stopped.")
        break
