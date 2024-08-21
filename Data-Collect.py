#!/usr/bin/env python
""" \example XEP_X4M200_X4M300_plot_record_playback_radar_raw_data.py

#Target module: X4M200,X4M300,X4M03

#Introduction: XeThru modules support both RF and baseband data output. This is an example of radar raw data manipulation. 
               Developer can use Module Connecter API to read, record radar raw data, and also playback recorded data. 
			   
#Command to run: "python XEP_X4M200_X4M300_plot_record_playback_radar_raw_data.py -d com8" or "python3 X4M300_printout_presence_state.py -d com8"
                 change "com8" with your device name, using "--help" to see other options.
                 Using TCP server address as device name is also supported, e.g. 
                 "python X4M200_sleep_record.py -d tcp://192.168.1.169:3000".
"""

from __future__ import print_function, division
import os
import sys
from optparse import OptionParser
from time import sleep
# from time import time
import time
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
area_start, area_end = 0.3, 3  # Area Start and End
fs = 23.328e9  # Sampling Rate
fc = 7.29e9  # Center Frequency
import pymoduleconnector
from pymoduleconnector import DataType
raw_data =[]
interval = 10
__version__ = 3
# COM port from where radar module is connected
device_name = "COM17"
# directory
dir = r'D:/radar_xethru/X4_records' 
def reset(device_name):
    mc = pymoduleconnector.ModuleConnector(device_name)
    xep = mc.get_xep()
    xep.module_reset()
    mc.close()
    sleep(3)

def on_file_available(data_type, filename):
    print("new file available for data type: {}".format(data_type))
    print("  |- file: {}".format(filename))
    if data_type == DataType.FloatDataType:
        print("processing Float data from file")

def on_meta_file_available(session_id, meta_filename):
    print("new meta file available for recording with id: {}".format(session_id))
    print("  |- file: {}".format(meta_filename))

def clear_buffer(mc):
    """Clears the frame buffer"""
    xep = mc.get_xep()
    while xep.peek_message_data_float():
        xep.read_message_data_float()

def simple_xep_plot(device_name, record=False, baseband=False):
    FPS = 20
    directory = '.'
    reset(device_name)
    mc = pymoduleconnector.ModuleConnector(device_name)

    # Assume an X4M300/X4M200 module and try to enter XEP mode
    app = mc.get_x4m300()
    # Stop running application and set module in manual mode.
    try:
        app.set_sensor_mode(0x13, 0) # Make sure no profile is running.
    except RuntimeError:
        # Profile not running, OK
        pass

    try:
        app.set_sensor_mode(0x12, 0) # Manual mode.
    except RuntimeError:
        # Maybe running XEP firmware only?
        pass

    if record:
        recorder = mc.get_data_recorder()
        recorder.subscribe_to_file_available(pymoduleconnector.AllDataTypes, on_file_available )
        recorder.subscribe_to_meta_file_available(on_meta_file_available)

    xep = mc.get_xep()
    # Set DAC range
    xep.x4driver_set_dac_min(900)
    xep.x4driver_set_dac_max(1150)
    # Set X4 Parameters
    xep.x4driver_set_frame_area_offset(0)
    xep.x4driver_set_frame_area(area_start, area_end)
    # Set integration
    xep.x4driver_set_iterations(16)
    xep.x4driver_set_pulses_per_step(26)

    xep.x4driver_set_downconversion(int(baseband))
    # Start streaming of data
    xep.x4driver_set_fps(FPS)

    def read_frame():
        """Gets frame data from module"""
        d = xep.read_message_data_float()
        frame = np.array(d.data)
         # Convert the resulting frame to a complex array if downconversion is enabled
        if baseband:
            n = len(frame)
            frame = frame[:n//2] + 1j*frame[n//2:]
        return frame

    def animate(i):
        if baseband:
            line.set_ydata(abs(read_frame())) # update the data
        else:
            line.set_ydata(read_frame())
        return line,

    fig = plt.figure()
    fig.suptitle("example version %d "%(__version__))
    ax = fig.add_subplot(1,1,1)
    ax.set_ylim(0 if baseband else -0.03,0.03) #keep graph in frame (FIT TO YOUR DATA)
    frame = read_frame()
    print("bukan baseband")
    print("frame shape : ", frame)
    if baseband:
        frame = abs(frame)
        print("frame shape : ", frame.shape)
    line, = ax.plot(frame)
    # Simpan Data 
    # Start streaming of data
    start = time.time()
    timestr = time.strftime("%Y-%m-%d_%H-%M-%S")

    # Replace colons with underscores in the timestamp
    timestr = timestr.replace(":", "_")

    clear_buffer(mc)

    if record:
        recorder.start_recording(DataType.BasebandApDataType | DataType.FloatDataType, directory)

    # ani = FuncAnimation(fig, animate, interval=FPS)
    # try:
    #     plt.show()
    # finally:
    # # Stop streaming of data
    #     xep.x4driver_set_fps(0)
    while True :
    # Update the data and check if the data is okay
        if time.time() - start < interval:
            data = read_frame()
            print("ukuran data-tiap frame : ", data.shape)
            print("data frame : ", data)
            raw_data.append(time.time())
            raw_data.append(data)
        else:
            # Finish and save X4 files inside a previously defined directory
            # Stop acquisition
            xep.x4driver_set_fps(0)
            filename = timestr + ".txt"
            full_path = os.path.join(dir, filename)
            f = open(full_path, "w+")
            f.write("FPS: " + str(FPS) + "\n")
            f.write("area_start: " + str(area_start) + "\n")
            f.write("area_end: " + str(area_end) + "\n")
            f.write("fs: " + str(fs) + "\n")
            f.write("fc: " + str(fc) + "\n")
            f.write("PRF: " + str(15.1875e6 ) + "\n")
            f.write("dac_min: " + str(900) + "\n")
            f.write("dac_max: " + str(1150) + "\n")
            f.write("interations: " + str(16) + "\n")
            f.write("duty_: " + str(0.95) + "\n")
            f.write("pulses_per_step: " + str(26) + "\n")

            for i in range(len(raw_data) - 1):
                if isinstance(raw_data[i], np.ndarray):
                    if raw_data[i].size > 1:
                        # Process the NumPy array
                        for x in np.nditer(raw_data[i]):
                            f.write(str(x) + " ")
                    else:
                        # Handle the case where raw_data[i] is a single float
                        f.write("\n" + str(raw_data[i]) + "\n")
                else:
                    # Handle the case where raw_data[i] is a float
                    f.write("\n" + str(raw_data[i]) + "\n")

            f.write("\n")
            f.close()

            break


def main(device_name, record=False, baseband=False):
    simple_xep_plot(device_name, record=record, baseband=baseband)

if __name__ == "__main__":
    main('COM17', False, False)
