# FILE: HallEffect.py 
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: A Micropython module used for the Hall Effect sensor family of products, supports both 
#        Digital and Analog versions as well as the native and Qwiic variants
# LAST UPDATED: 2025-06-10 

from os import uname
from Qwiic import Qwiic
from machine import Pin,I2C,ADC


ANALOG_READ_REG=0


class HallEffectAnalog(Qwiic):
    def __init__(self,i2c=None,address=0x30,pin=None):
        """
        Initializes the Hall Effect Sensor.

        :param i2c: I2C object (required for Qwiic mode)
        :param address: I2C address (default 0x30)
        :param pin: GPIO pin number for native mode. If provided, native mode is used.
        """
        if uname().sysname == "esp32":
            self.VOLTAGE_RES=3.3
            self.ADC_MAX=4096
            self.NUM_BITS=12
        elif uname().sysname == "esp8266":
            self.VOLTAGE_RES=3.3
            self.ADC_MAX=1024
            self.NUM_BITS=10
        else:
            self.VOLTAGE_RES=5
            self.ADC_MAX=1024
            self.NUM_BITS=10
        
        if pin is not None:
            # Native mode
            super().__init__(i2c=None, native=True)
            self.pin = ADC(pin)
            self.native=True
            self.pin.atten(ADC.ATTN_11DB)
        else:
            if i2c != None:
                i2c = i2c
            else:
                if uname().sysname == "esp32" or uname().sysname == "esp8266":
                    i2c = I2C(0, scl=Pin(22), sda=Pin(21))
                else:
                    raise Exception("Board not recognized, enter I2C pins manually")
            super().__init__(i2c=i2c, address=address, native=False)
        
    def initialize_native(self):
        """
        Setup for native GPIO input.
        """
        # Already initialized in __init__
        pass
    
    def getReading(self) -> int:
        if self.native:
            return self.pin.read()
        else:
            data = self.read_register(ANALOG_READ_REG,2)
            value=data[1]<<8|data[0]
            return value
    
    def getMilliTeslas(self) -> float:
        value=self.getReading()
        if self.native:
            if uname().sysname == "esp32":
                if (value >= 2710):
                    return (value - 2710.0) * (20.47 - 0.0) / (4095.0 - 2710.0) + 0.0
                else:
                    return (value) * (20.47) / (2710.0) - 20.47
            else:
                return 20.47 * (self.NUM_BITS * (value / (self.ADC_MAX - 1)) / self.VOLTAGE_RES - 1)
        else:
            return 20.47 * (10 * (value / 1023.0) / 5.0 - 1)
        
        
        
class HallEffectDigital(Qwiic):
    def __init__(self,i2c=None,address=0x30,pin=None):
        """
        Initializes the Hall Effect Sensor.

        :param i2c: I2C object (required for Qwiic mode)
        :param address: I2C address (default 0x30)
        :param pin: GPIO pin number for native mode. If provided, native mode is used.
        """

        if pin is not None:
            # Native mode
            super().__init__(i2c=None, native=True)
            self.pin = Pin(pin, Pin.IN)
            self.native=True
        else:
            if i2c != None:
                i2c = i2c
            else:
                if uname().sysname == "esp32" or uname().sysname == "esp8266":
                    i2c = I2C(0, scl=Pin(22), sda=Pin(21))
                else:
                    raise Exception("Board not recognized, enter I2C pins manually")
            super().__init__(i2c=i2c, address=address, native=False)
        
    def initialize_native(self):
        """
        Setup for native GPIO input.
        """
        # Already initialized in __init__
        pass
    
    def getReading(self) -> int:
        if self.native:
            return not (self.pin.value())
        else:
            data = self.read_register(0,2)
            return not (data[1])
    