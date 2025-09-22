# FILE: tmp117-customConfig.py 
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF:  Example showing how use custom configurations to
#         set different measurement modes as well as measurement times
# WORKS WITH: Temperature Sensor TMP117 Breakout: www.solde.red/333175
# LAST UPDATED: 2025-09-22 

from machine import I2C, Pin
import time
from tmp117 import TMP117, TMP117_CMODE, TMP117_CONVT, TMP117_AVE

# Initialize I2C
i2c = I2C()

# Create TMP117 instance
tmp = TMP117(i2c, addr=0x49)

def new_temperature():
    """Callback function for new temperature data"""
    temperature = tmp.getTemperature()
    print("Temperature : {:.2f} °C".format(temperature))

# Initialize with callback function
tmp.init(new_temperature)

# Set continuous measurement mode
tmp.setConvMode(TMP117_CMODE.CONTINUOUS)

setup_nr = 3  # Select an example setup to see different modes

if setup_nr == 1:
    # Setup 1: C15mS5 + NOAVE = 15.5 mS measurement time
    tmp.setConvTime(TMP117_CONVT.C15mS5)
    tmp.setAveraging(TMP117_AVE.NOAVE)
    print("Setup 1: 15.5ms measurement time, no averaging")
    
elif setup_nr == 2:
    # Setup 2: C125mS + AVE8 = 125 mS measurement time
    tmp.setConvTime(TMP117_CONVT.C125mS)
    tmp.setAveraging(TMP117_AVE.AVE8)
    print("Setup 2: 125ms measurement time, 8x averaging")
    
elif setup_nr == 3:
    # Setup 3: C125mS + AVE32 = 500 mS measurement time
    tmp.setConvTime(TMP117_CONVT.C125mS)
    tmp.setAveraging(TMP117_AVE.AVE32)
    print("Setup 3: 500ms measurement time, 32x averaging")
    
elif setup_nr == 4:
    # Setup 4: C4S + AVE64 = 4000 mS measurement time
    tmp.setConvTime(TMP117_CONVT.C4S)
    tmp.setAveraging(TMP117_AVE.AVE64)
    print("Setup 4: 4000ms measurement time, 64x averaging")
    
else:
    # Default to setup 1
    tmp.setConvTime(TMP117_CONVT.C15mS5)
    tmp.setAveraging(TMP117_AVE.NOAVE)
    print("Default setup: 15.5ms measurement time, no averaging")

# Print current configuration for verification
print("Current configuration:")
tmp.printConfig()

while True:
    """Infinite loop"""
    tmp.update()  # Update the sensor/read configuration register
    time.sleep(0.5)  # Small delay to prevent busy waiting