# FILE: ltr507-CustomConfiguration.py 
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF:  An example showing how to initialize the LTR-507 sensor and get light and proximity measurements
# WORKS WITH: Digital light & proximity sensor LTR-507 breakout: www.solde.red/333063
# LAST UPDATED: 2025-06-10

from machine import I2C, Pin
from time import sleep
from ltr507 import LTR507  # This assumes you have an ltr507.py module with the driver
from ltr507_config import *

"""
Connecting diagram:

IMPORTANT: an IR LED must be connected when measuring proximity!
LTR-507                      IR LED
VLED------------------------>CATHODE (-)
VCC------------------------->ANODE (+)
"""

# If you aren't using the Qwiic connector, manually enter your I2C pins
#i2c = I2C(0, scl=Pin(22), sda=Pin(21))
#sensor = LTR507(i2c)

#Initialize I2C communication with the sensor over Qwiic
sensor = LTR507()

#Set up the sensor with its default values
sensor.begin()
# You can change the following settings:

# This turns off the ambient light sensor (ALS) and proximity sensor
# sensor.set_als_mode(False)
# sensor.set_ps_mode(False)
# Setting the parameter to 'True' will turn it back on, this is done by default in init()

# Set the gain of the sensor
# This way you can get more or less sensitivity
# From the datasheet:
#      - LTR507_ALS_GAIN_RANGE1: 1 lux to 64k lux (1 lux/count) (default)
#      - LTR507_ALS_GAIN_RANGE2: 0.5 lux to 32k lux (0.5 lux/count)
#      - LTR507_ALS_GAIN_RANGE3: 0.02 lux to 640 lux (0.01 lux/count)
#      - LTR507_ALS_GAIN_RANGE4: 0.01 lux to 320 lux (0.005 lux/count)
sensor.set_als_gain(LTR507_ALS_GAIN_RANGE1)

# Set the automatic measurement rate
# You can use:
#      - LTR507_ALS_MEASUREMENT_RATE_100MS (default)
#      - LTR507_ALS_MEASUREMENT_RATE_200MS
#      - LTR507_ALS_MEASUREMENT_RATE_500MS
#      - LTR507_ALS_MEASUREMENT_RATE_1000MS
#      - LTR507_ALS_MEASUREMENT_RATE_2000MS
sensor.set_als_meas_rate(LTR507_ALS_MEASUREMENT_RATE_100MS)

# Set the bit width of the ALS measurement
# This changes the time required to complete a single measurement
# So, it's recommended to leave it as default
# sensor.set_als_bitwidth(sensor.ALS_ADC_BIT_WIDTH_16BIT)

# Set the auto measurement rate for proximity
# You can use:
#      - LTR507_PS_MEASUREMENT_RATE_12_5MS
#      - LTR507_PS_MEASUREMENT_RATE_50MS
#      - LTR507_PS_MEASUREMENT_RATE_70MS
#      - LTR507_PS_MEASUREMENT_RATE_100MS (default)
#      - LTR507_PS_MEASUREMENT_RATE_200MS
#      - LTR507_PS_MEASUREMENT_RATE_500MS
#      - LTR507_PS_MEASUREMENT_RATE_1000MS
#      - LTR507_PS_MEASUREMENT_RATE_2000MS
sensor.set_ps_meas_rate(LTR507_PS_MEASUREMENT_RATE_100MS)

# Set the max current supplied to the IR LED
# You can use:
#      - LTR507_LED_PEAK_CURRENT_5MA
#      - LTR507_LED_PEAK_CURRENT_10MA
#      - LTR507_LED_PEAK_CURRENT_20MA
#      - LTR507_LED_PEAK_CURRENT_50MA (default)
sensor.set_led_peak_current(LTR507_LED_PEAK_CURRENT_50MA)

# Set the pulse frequency of the IR LED
# You can use:
#      - LTR507_LED_PULSE_FREQ_30KHZ
#      - LTR507_LED_PULSE_FREQ_40KHZ
#      - LTR507_LED_PULSE_FREQ_50KHZ
#      - LTR507_LED_PULSE_FREQ_60KHZ (default)
#      - LTR507_LED_PULSE_FREQ_70KHZ
#      - LTR507_LED_PULSE_FREQ_80KHZ
#      - LTR507_LED_PULSE_FREQ_90KHZ
#      - LTR507_LED_PULSE_FREQ_100KHZ
sensor.set_led_pulse_freq(LTR507_LED_PULSE_FREQ_60KHZ)

# Set the number of pulses for a proximity measurement
# You can use any number from 1 to 15, default is 1
sensor.set_ps_num_pulses(1)

# Main loop
while True:
    #Measure the light intensity from the sensor in lux 
    lux = sensor.getLightIntensity()
    #Measure the proximity value of the sensor
    prox = sensor.getProximity()

    # Print the readings
    print("Light sensor reading:", lux)
    print("Proximity reading:", prox)
    print()  # Newline

    # Wait a bit until the next reading so output isn't too fast
    sleep(1)