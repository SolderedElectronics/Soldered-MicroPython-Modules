# FILE: TMP117.py 
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: A MicroPython module for the TMP117 Temperature Sensor Breakout
# LAST UPDATED: 2025-09-22 
from micropython import const
import machine
import time

# Register addresses
_TMP117_REG_TEMPERATURE = const(0x00)
_TMP117_REG_CONFIGURATION = const(0x01)
_TMP117_REG_TEMP_HIGH_LIMIT = const(0x02)
_TMP117_REG_TEMP_LOW_LIMIT = const(0x03)
_TMP117_REG_EEPROM_UNLOCK = const(0x04)
_TMP117_REG_EEPROM1 = const(0x05)
_TMP117_REG_EEPROM2 = const(0x06)
_TMP117_REG_EEPROM3 = const(0x08)
_TMP117_REG_TEMPERATURE_OFFSET = const(0x07)
_TMP117_REG_DEVICE_ID = const(0x0F)

_TMP117_RESOLUTION = 0.0078125

# Enums as classes
class TMP117_PMODE:
    THERMAL = 0
    ALERT = 1
    DATA = 2

class TMP117_CMODE:
    CONTINUOUS = 0
    SHUTDOWN = 1
    ONESHOT = 3

class TMP117_CONVT:
    C15mS5 = 0
    C125mS = 1
    C250mS = 2
    C500mS = 3
    C1S = 4
    C4S = 5
    C8S = 6
    C16S = 7

class TMP117_AVE:
    NOAVE = 0
    AVE8 = 1
    AVE32 = 2
    AVE64 = 3

class TMP117_ALERT:
    NOALERT = 0
    HIGHALERT = 1
    LOWALERT = 2

class TMP117:
    def __init__(self, i2c, addr=0x49):
        self.i2c = i2c
        self.address = addr
        self.alert_pin = None
        self.alert_type = TMP117_ALERT.NOALERT
        self.newDataCallback = None
        
    def init(self, newDataCallback=None):
        """Initialize in default mode"""
        self.setConvMode(TMP117_CMODE.CONTINUOUS)
        self.setConvTime(TMP117_CONVT.C125mS)
        self.setAveraging(TMP117_AVE.AVE8)
        self.setAlertMode(TMP117_PMODE.DATA)
        self.setOffsetTemperature(0)
        
        self.newDataCallback = newDataCallback
        
    def update(self):
        """Read configuration register and handle events"""
        return self.readConfig()
    
    def softReset(self):
        """Performs a soft reset"""
        reg_value = 1 << 1
        self.writeConfig(reg_value)
    
    def setAlertMode(self, mode):
        """Set alert pin mode"""
        reg_value = self.readConfig()
        
        if mode == TMP117_PMODE.THERMAL:
            reg_value |= 1 << 4    # change to thermal mode
            reg_value &= ~(1 << 2) # set pin as alert flag
            reg_value &= ~(1 << 3) # alert pin low active
        elif mode == TMP117_PMODE.ALERT:
            reg_value &= ~(1 << 4) # change to alert mode
            reg_value &= ~(1 << 2) # set pin as alert flag
            reg_value &= ~(1 << 3) # alert pin low active
        elif mode == TMP117_PMODE.DATA:
            reg_value |= 1 << 2    # set pin as data ready flag
            
        self.writeConfig(reg_value)
    
    def setAlertCallback(self, alert_callback, pin):
        """Set alert callback function with proper configuration"""
        # Configure alert pin with strong pull-up
        self.alert_pin = machine.Pin(pin, machine.Pin.IN, machine.Pin.PULL_UP)
        
        # First, ensure we're in proper alert mode
        self.configureAlertMode()
        
        # Clear any existing alerts
        self.clearAlertFlags()
        
        # Wait for pin to stabilize
        time.sleep_ms(100)
        
        # Only set interrupt if pin is not currently active
        if self.alert_pin.value() == 1:  # Should be high when no alert
            self.alert_pin.irq(trigger=machine.Pin.IRQ_FALLING, handler=alert_callback)
            print("Alert interrupt configured")
        else:
            print("Warning: Alert pin is active during setup!")
            # Try to clear and reconfigure
            self.clearAlertFlags()
            time.sleep_ms(50)
            if self.alert_pin.value() == 1:
                self.alert_pin.irq(trigger=machine.Pin.IRQ_FALLING, handler=alert_callback)
            else:
                print("Alert pin still active - check hardware")

    def configureAlertMode(self):
        """Ensure proper alert mode configuration"""
        reg_value = self.i2cRead2B(_TMP117_REG_CONFIGURATION)
        
        # Set to alert mode (not thermal mode)
        reg_value &= ~(1 << 4)  # Clear T/nA bit (0 = Alert mode)
        
        # Set pin as alert flag (not data ready)
        reg_value &= ~(1 << 2)  # Clear DR/Alert bit (0 = Alert mode)
        
        # Set active low polarity (typical for open-drain)
        reg_value &= ~(1 << 3)  # Clear POL bit (0 = Active Low)
        
        self.writeConfig(reg_value)
        print("Alert mode configured")

    def clearAlertFlags(self):
        """Force clear any alert flags"""
        reg_value = self.i2cRead2B(_TMP117_REG_CONFIGURATION)
        # Clear both alert flags
        clear_value = reg_value & ~((1 << 15) | (1 << 14))
        self.i2cWrite2B(_TMP117_REG_CONFIGURATION, clear_value)
    
    def setAlertTemperature(self, lowtemp, hightemp):
        """Set alert temperature boundaries"""
        high_temp_value = int(hightemp / _TMP117_RESOLUTION)
        low_temp_value = int(lowtemp / _TMP117_RESOLUTION)
        
        self.i2cWrite2B(_TMP117_REG_TEMP_HIGH_LIMIT, high_temp_value)
        self.i2cWrite2B(_TMP117_REG_TEMP_LOW_LIMIT, low_temp_value)
    
    def setConvMode(self, cmode):
        """Set conversion mode"""
        reg_value = self.readConfig()
        reg_value &= ~((1 << 11) | (1 << 10))  # clear bits
        reg_value |= (cmode & 0x03) << 10      # set bits
        self.writeConfig(reg_value)
    
    def setConvTime(self, convtime):
        """Set conversion time"""
        reg_value = self.readConfig()
        reg_value &= ~((1 << 9) | (1 << 8) | (1 << 7))  # clear bits
        reg_value |= (convtime & 0x07) << 7             # set bits
        self.writeConfig(reg_value)
    
    def setAveraging(self, ave):
        """Set averaging mode"""
        reg_value = self.readConfig()
        reg_value &= ~((1 << 6) | (1 << 5))  # clear bits
        reg_value |= (ave & 0x03) << 5       # set bits
        self.writeConfig(reg_value)
    
    def setOffsetTemperature(self, offset):
        """Set offset temperature"""
        offset_temp_value = int(offset / _TMP117_RESOLUTION)
        self.i2cWrite2B(_TMP117_REG_TEMPERATURE_OFFSET, offset_temp_value)
    
    def setTargetTemperature(self, target):
        """Set target temperature for calibration"""
        actual_temp = self.getTemperature()
        delta_temp = target - actual_temp
        self.setOffsetTemperature(delta_temp)
    
    def getTemperature(self):
        """Get temperature in °C"""
        temp = self.i2cRead2B(_TMP117_REG_TEMPERATURE)
        # Convert to signed 16-bit integer
        if temp & 0x8000:
            temp = temp - 0x10000
        return temp * _TMP117_RESOLUTION
    
    def getDeviceID(self):
        """Get Device ID (bits [11:0])"""
        raw = self.i2cRead2B(_TMP117_REG_DEVICE_ID)
        return raw & 0x0FFF
    
    def getDeviceRev(self):
        """Get Device Revision (bits [15:12])"""
        raw = self.i2cRead2B(_TMP117_REG_DEVICE_ID)
        return (raw >> 12) & 0x3
    
    def getOffsetTemperature(self):
        """Get offset temperature in °C"""
        temp = self.i2cRead2B(_TMP117_REG_TEMPERATURE_OFFSET)
        # Convert to signed 16-bit integer
        if temp & 0x8000:
            temp = temp - 0x10000
        return temp * _TMP117_RESOLUTION
    
    def getAlertType(self):
        """Get alert type"""
        return self.alert_type
    
    def writeEEPROM(self, data, eeprom_nr):
        """Write data to EEPROM"""
        if not self.EEPROMisBusy():
            self.unlockEEPROM()
            if eeprom_nr == 1:
                self.i2cWrite2B(_TMP117_REG_EEPROM1, data)
            elif eeprom_nr == 2:
                self.i2cWrite2B(_TMP117_REG_EEPROM2, data)
            elif eeprom_nr == 3:
                self.i2cWrite2B(_TMP117_REG_EEPROM3, data)
            else:
                print("EEPROM value must be between 1 and 3")
            self.lockEEPROM()
        else:
            print("EEPROM is busy")
    
    def readEEPROM(self, eeprom_nr):
        """Read data from EEPROM"""
        if not self.EEPROMisBusy():
            if eeprom_nr == 1:
                return self.i2cRead2B(_TMP117_REG_EEPROM1)
            elif eeprom_nr == 2:
                return self.i2cRead2B(_TMP117_REG_EEPROM2)
            elif eeprom_nr == 3:
                return self.i2cRead2B(_TMP117_REG_EEPROM3)
            else:
                print("EEPROM value must be between 1 and 3")
                return 0
        else:
            print("EEPROM is busy")
            return 0
    
    def readConfig(self):
        """Read configuration register and clear alert flags"""
        reg_value = self.i2cRead2B(_TMP117_REG_CONFIGURATION)
        data_ready = (reg_value >> 13) & 0x1
        
        # Handle data ready callback
        if data_ready and self.newDataCallback:
            self.newDataCallback()
        
        # Check for alert flags
        high_alert = (reg_value >> 15) & 0x1
        low_alert = (reg_value >> 14) & 0x1
        
        # Update alert type
        if high_alert:
            self.alert_type = TMP117_ALERT.HIGHALERT
        elif low_alert:
            self.alert_type = TMP117_ALERT.LOWALERT
        else:
            self.alert_type = TMP117_ALERT.NOALERT
        
        # Clear alert flags if they are set
        if high_alert or low_alert:
            # Clear both alert flags while preserving other bits
            clear_value = reg_value & ~((1 << 15) | (1 << 14))
            self.i2cWrite2B(_TMP117_REG_CONFIGURATION, clear_value)
        
        return reg_value
    
    def printConfig(self):
        """Print configuration in readable format"""
        reg_value = self.i2cRead2B(_TMP117_REG_CONFIGURATION)
        print(f"Configuration: {bin(reg_value)}")
        print(f"HIGH alert:  {(reg_value >> 15) & 0x1}")
        print(f"LOW alert:   {(reg_value >> 14) & 0x1}")
        print(f"Data ready:  {(reg_value >> 13) & 0x1}")
        print(f"EEPROM busy: {(reg_value >> 12) & 0x1}")
        print(f"MOD[1:0]:    {(reg_value >> 10) & 0x3}")
        print(f"CONV[2:0]:   {(reg_value >> 7) & 0x7}")
        print(f"AVG[1:0]:    {(reg_value >> 5) & 0x3}")
        print(f"T/nA:        {(reg_value >> 4) & 0x1}")
        print(f"POL:         {(reg_value >> 3) & 0x1}")
        print(f"DR/Alert:    {(reg_value >> 2) & 0x1}")
        print(f"Soft_Reset:  {(reg_value >> 1) & 0x1}")
    
    # Private methods
    def i2cWrite2B(self, reg, data):
        """Write two bytes to I2C device"""
        buf = bytearray(3)
        buf[0] = reg
        buf[1] = (data >> 8) & 0xFF
        buf[2] = data & 0xFF
        self.i2c.writeto(self.address, buf)
        time.sleep_ms(10)
    
    def i2cRead2B(self, reg):
        """Read two bytes from I2C device"""
        buf = bytearray(2)
        self.i2c.writeto(self.address, bytes([reg]))
        self.i2c.readfrom_into(self.address, buf)
        return (buf[0] << 8) | buf[1]
    
    def writeConfig(self, config_data):
        """Write configuration to config register"""
        if not self.EEPROMisBusy():
            self.unlockEEPROM()
            self.i2cWrite2B(_TMP117_REG_CONFIGURATION, config_data)
            self.lockEEPROM()
        else:
            print("EEPROM is busy")
    
    def lockEEPROM(self):
        """Lock EEPROM, write protection"""
        code = 0
        code &= ~(1 << 15)
        self.i2cWrite2B(_TMP117_REG_EEPROM_UNLOCK, code)
        time.sleep_ms(100)
    
    def unlockEEPROM(self):
        """Unlock EEPROM, remove write protection"""
        code = 1 << 15
        self.i2cWrite2B(_TMP117_REG_EEPROM_UNLOCK, code)
        time.sleep_ms(100)
    
    def EEPROMisBusy(self):
        """Check if EEPROM is busy"""
        code = self.i2cRead2B(_TMP117_REG_EEPROM_UNLOCK)
        return bool((code >> 14) & 0x01)