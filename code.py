"""Author: Andrei Tretiakov QuBiT lab, UCLA This code run and displays magnetic field measurements from the
magnetometer This code was generously copied and pasted from here:
https://learn.adafruit.com/adafruit-128x64-oled-featherwing/circuitpython bitch """

import time
import board
import displayio
import terminalio
import adafruit_lis3mdl
import math
import usb_cdc
import supervisor
import ulab.numpy as np

# can try import bitmap_label below for alternative
from micropython import const

from adafruit_display_text import label
import adafruit_displayio_sh1107

displayio.release_displays()
# oled_reset = board.D9

# Use for I2C
i2c = board.I2C()
display_bus = displayio.I2CDisplay(i2c, device_address=0x3C)  # connect to the display
sensor = adafruit_lis3mdl.LIS3MDL(i2c)  # connect to the magnetometer

########################
# Set up the display
# SH1107 is vertically oriented 64x128
WIDTH = 128
HEIGHT = 64
BORDER = 2
REFRESH_TIME = 0.2
yb = 8

display = adafruit_displayio_sh1107.SH1107(
    display_bus, width=WIDTH, height=HEIGHT, rotation=0
)

# Make the display context
splash = displayio.Group()
display.show(splash)

# Draw a smaller inner rectangle in black
inner_bitmap = displayio.Bitmap(WIDTH - BORDER * 2, HEIGHT - BORDER * 2, 1)
inner_palette = displayio.Palette(1)
inner_palette[0] = 0x000000  # Black
inner_sprite = displayio.TileGrid(
    inner_bitmap, pixel_shader=inner_palette, x=BORDER, y=BORDER
)
splash.append(inner_sprite)

SAMPLE_NUM = 20
CHARS_PER_LINE = 20
usbl = usb_cdc.data

###########
# continuously measure and display the magnetic field
splash = displayio.Group()

l1 = ""
l2 = ""
l3 = ""
l4 = ""

_TICKS_PERIOD = const(1<<29)
_TICKS_MAX = const(_TICKS_PERIOD-1)
_TICKS_HALFPERIOD = const(_TICKS_PERIOD//2)

def ticks_add(ticks, delta):
    "Add a delta to a base number of ticks, performing wraparound at 2**29ms."
    return (ticks + delta) % _TICKS_PERIOD

def ticks_diff(ticks1, ticks2):
    "Compute the signed difference between two ticks values, assuming that they are within 2**28 ticks"
    diff = (ticks1 - ticks2) & _TICKS_MAX
    diff = ((diff + _TICKS_HALFPERIOD) & _TICKS_MAX) - _TICKS_HALFPERIOD
    return diff


def handleException(exception):
    splash = displayio.Group()
    full_text = str(exception)
    for i in range(4):
        # in first round, print chars from 0 - 20, second round print 20 - 40.. and so on to print full exception on display
        text_area = label.Label(terminalio.FONT, text=full_text[i * (CHARS_PER_LINE):(i + 1) * (CHARS_PER_LINE)],
                                scale=1, x=2, y=yb + (i * 15))
        splash.append(text_area)
    display.show(splash)
    time.sleep(10)

def displayDebug(text, sec):
    splash = displayio.Group()
    full_text = str(text)
    for i in range(4):
        # in first round, print chars from 0 - 20, second round print 20 - 40.. and so on to print full exception on display
        text_area = label.Label(terminalio.FONT, text=full_text[i * (CHARS_PER_LINE):(i + 1) * (CHARS_PER_LINE)],
                                scale=1, x=2, y=yb + (i * 15))
        splash.append(text_area)
    display.show(splash)
    time.sleep(sec)


def displayNormal(text1, text2, text3, text4):
    splash = displayio.Group()

    if text1 != "":
        text_area1 = label.Label(terminalio.FONT, text=text1, scale=1, x=8, y=yb)
        splash.append(text_area1)

    if text2 != "":
        text_area2 = label.Label(terminalio.FONT, text=text2, scale=1, x=8, y=yb + 15)
        splash.append(text_area2)

    if text3 != "":
        text_area3 = label.Label(terminalio.FONT, text=text3, scale=1, x=8, y=yb + 30)
        splash.append(text_area3)

    if text4 != "":
        text_area4 = label.Label(terminalio.FONT, text=text4, scale=1, x=8, y=yb + 45)
        splash.append(text_area4)

    display.show(splash)
    time.sleep(0.2)


def requestResponseMode():
    l1 = "trm mode: (m-stop)"
    continueLoop = True
    while continueLoop:
        while usb_cdc.data.in_waiting == 0:
            time.sleep(0.0001)

        call = str(usb_cdc.data.readline(), "utf-8").strip()
        l2 = "received " + call
        try:
            command, acquisition_time_str, acquisition_rate_str = call.split(" ")
        except Exception as e:
            displayDebug(e, 1)
            continue
        acquisition_time = float(acquisition_time_str)
        acquisition_rate = int(acquisition_rate_str)
        if command == "g-mag-all":
            total_number_of_acquisitions = int(acquisition_rate * acquisition_time)
            t0 = supervisor.ticks_ms()
            for j in range(int(total_number_of_acquisitions / 250)):
                number_of_acquisitions = 250
                # l3 = "acq total: " + str(250)
                # l4 = "in " + acquisition_time_str + " seconds"
                # displayNormal(l1, l2, l3, l4)
                data_array = np.empty([number_of_acquisitions, 4])
                time_past_ms = t0
                for i in range(number_of_acquisitions):
                    tr0 = supervisor.ticks_ms()
                    bx, by, bz = sensor.magnetic
                    tdiff = ticks_diff(supervisor.ticks_ms(), t0)
                    data_array[i][0] = float(tdiff)
                    data_array[i][1] = bx
                    data_array[i][2] = by
                    data_array[i][3] = bz
                    time_past_ms = ticks_diff(supervisor.ticks_ms(), tr0)
                    time_to_sleep_seconds = ((1000/acquisition_rate) - time_past_ms)/1000
                    if time_to_sleep_seconds > 0:
                        time.sleep(time_to_sleep_seconds)

                senddata = data_array.tobytes() + bytes("STOPACQUISITION", 'utf-8')
                usbl.write(senddata)
                # l3 = "acq bytes: " + str(len(senddata))
                # l4 = "t: %2.5f ms" % (supervisor.ticks_ms() - t0)
                # displayNormal(l1, l2, l3, l4)
        elif command == "m-stop":
            return


def loopMode(splash):
    continueLoop = True
    displayNormal("continue loop", str(continueLoop), "", "")
    while continueLoop:
        splash = displayio.Group()
        mag_x, mag_y, mag_z = sensor.magnetic
        for i in range(SAMPLE_NUM - 1):
            mag_x2, mag_y2, mag_z2 = sensor.magnetic
            mag_x += mag_x2
            mag_y += mag_y2
            mag_z += mag_z2
        mag_x, mag_y, mag_z = mag_x / SAMPLE_NUM, mag_y / SAMPLE_NUM, mag_z / SAMPLE_NUM

        # display Bx
        yb = 8
        text1 = "Bx = " + str(mag_x) + " uT"
        text_area1 = label.Label(terminalio.FONT, text=text1, scale=1, x=8, y=yb)
        splash.append(text_area1)
        # display By
        text2 = "By = " + str(mag_y) + " uT"
        text_area2 = label.Label(terminalio.FONT, text=text2, scale=1, x=8, y=yb + 15)
        splash.append(text_area2)
        # display Bz
        text3 = "Bz = " + str(mag_z) + " uT"
        text_area3 = label.Label(terminalio.FONT, text=text3, scale=1, x=8, y=yb + 30)
        splash.append(text_area3)
        # display the magnitude of B
        text4 = "|B| = " + str(math.sqrt(mag_x ** 2 + mag_y ** 2 + mag_z ** 2)) + " uT"
        text_area4 = label.Label(terminalio.FONT, text=text4, scale=1, x=8, y=yb + 45)
        splash.append(text_area4)
        display.show(splash)
        time.sleep(REFRESH_TIME)

        if usb_cdc.data.in_waiting != 0:
            command = str(usb_cdc.data.readline(), "utf-8").strip()
            if command == "go-trm":
               return "go-trm"
            else:
                displayNormal("no command:", command, "", "")


def mainloop(command):
    while True:
        if command == "":
            displayNormal("command plz", "", "", "")
            i = 3
            while i != 0 and usb_cdc.data.in_waiting == 0:
                displayNormal("entering local loop", "unless cmd received", "waiting ..", str(i) + " sec")
                i = i - 1
                time.sleep(1)
            if usb_cdc.data.in_waiting != 0:
                command = str(usb_cdc.data.readline(), "utf-8").strip()

        if command == "go-trm":
            command = ""
            senddata = bytes("roger-trm" + "\n", 'utf-8')
            usbl.write(senddata)
            displayNormal("enter trm mode", "", "", "")
            requestResponseMode()
        else:
            command = loopMode(splash)


displayNormal("command plz", "", "", "")
while True:
    try:
        mainloop("")

    except BaseException as err:
        handleException(err)
        time.sleep(15)
        displayNormal("command plz", "", "", "")
        mainloop()

