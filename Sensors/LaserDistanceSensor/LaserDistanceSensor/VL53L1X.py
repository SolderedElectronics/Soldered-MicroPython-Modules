# FILE: VL53L1X.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BASED ON: vl53l1x_pico module by drakxtwo (https://github.com/drakxtwo)
# BRIEF: A micropython module for the VL53L1X laser distance sensor
# LAST UPDATED: 2025-07-14

from VL53L1X_config import *
import machine
from os import uname
from machine import I2C, Pin


class VL53L1X:
    def __init__(
        self, i2c=None, address=0x29, interruptPin=None, interruptCallback=None
    ):
        """
        Initialize the VL53L1X sensor over I2C.
        Optionally set up GPIO interrupt handling if interruptPin and interruptCallback are provided.
        """
        if i2c != None:
            self.i2c = i2c
        else:
            if uname().sysname in ("esp32", "esp8266", "Soldered Dasduino CONNECTPLUS"):
                self.i2c = I2C(0, scl=Pin(22), sda=Pin(21))
            else:
                raise Exception("Board not recognized, enter I2C pins manually")
        self.address = address
        self.interruptCallback = interruptCallback
        self.interruptPin = None

        # Reset sensor to default state
        self.reset()
        machine.lightsleep(1)  # Brief pause to allow reset to complete

        # Read Model ID and check if it's the expected one
        if self.read_model_id() != 0xEACC:
            raise RuntimeError(
                "Failed to find expected ID register values. Check wiring!"
            )

        # Load default configuration to sensor starting at register 0x2D
        self.i2c.writeto_mem(
            self.address, 0x2D, VL51L1X_DEFAULT_CONFIGURATION, addrsize=16
        )

        # Apply part-to-part offset correction
        # OFFSET = OUTER_OFFSET_MM * 4 (as per ST datasheet)
        self.writeReg16Bit(0x001E, self.readReg16Bit(0x0022) * 4)

        machine.lightsleep(200)  # Let sensor settle after config

        # Set up interrupt pin if configured
        if interruptPin and interruptCallback:
            self.interruptPin = machine.Pin(interruptPin, machine.Pin.IN)
            self.interruptPin.irq(
                trigger=machine.Pin.IRQ_FALLING, handler=self.interruptCallback
            )
            self.enable_interrupt()
        elif interruptPin and not interruptCallback:
            raise RuntimeError(
                "If using the interrupt feature, you must also set the interrupt callback function!"
            )

    def writeReg(self, reg, value):
        """Write an 8-bit value to a 16-bit register address."""
        return self.i2c.writeto_mem(self.address, reg, bytes([value]), addrsize=16)

    def writeReg16Bit(self, reg, value):
        """Write a 16-bit value to a 16-bit register address."""
        return self.i2c.writeto_mem(
            self.address, reg, bytes([(value >> 8) & 0xFF, value & 0xFF]), addrsize=16
        )

    def readReg(self, reg):
        """Read an 8-bit value from a 16-bit register address."""
        return self.i2c.readfrom_mem(self.address, reg, 1, addrsize=16)[0]

    def readReg16Bit(self, reg):
        """Read a 16-bit value from a 16-bit register address."""
        data = self.i2c.readfrom_mem(self.address, reg, 2, addrsize=16)
        return (data[0] << 8) + data[1]

    def read_model_id(self):
        """Returns the sensor's model ID."""
        return self.readReg16Bit(0x010F)  # VL53L1_IDENTIFICATION__MODEL_ID

    def reset(self):
        """Perform a software reset on the sensor."""
        self.writeReg(0x0000, 0x00)  # SOFT_RESET = 0x00
        machine.lightsleep(100)
        self.writeReg(0x0000, 0x01)  # Re-enable device

    def read(self):
        """Read the current measured distance in mm (simplified)."""
        data = self.i2c.readfrom_mem(
            self.address, 0x0089, 17, addrsize=16
        )  # RESULT__RANGE_STATUS
        return (data[13] << 8) + data[14]  # final_crosstalk_corrected_range_mm_sd0

    def readDetailed(self):
        """
        Read detailed measurement data from the sensor:
        Returns:
            - range_mm: measured distance
            - status: string status from range status code
            - peak_signal_rate: peak signal rate in Mcps
            - ambient_rate: ambient light rate in Mcps
        """
        data = self.i2c.readfrom_mem(self.address, 0x0089, 17, addrsize=16)

        range_status = data[0]
        stream_count = data[2]
        peak_signal_count_rate_mcps_sd0 = (data[5] << 8) + data[6]
        ambient = float((data[7] << 8) + data[8]) / (1 << 7)
        range_mm = (data[13] << 8) + data[14]
        peak_signal_crosstalk_corrected = float((data[15] << 8) + data[16]) / (1 << 7)

        # Interpret status
        status = None
        if range_status in (17, 2, 1, 3):
            status = "HardwareFail"
        elif range_status == 13:
            status = "MinRangeFail"
        elif range_status == 18:
            status = "SynchronizationInt"
        elif range_status == 5:
            status = "OutOfBoundsFail"
        elif range_status in (4, 6):
            status = "SignalFail"
        elif range_status == 7:
            status = "WrapTargetFail"
        elif range_status == 12:
            status = "XtalkSignalFail"
        elif range_status == 8:
            status = "RangeValidMinRangeClipped"
        elif range_status == 9:
            if stream_count == 0:
                status = "RangeValidNoWrapCheckFail"
            else:
                status = "OK"

        return range_mm, status, peak_signal_crosstalk_corrected, ambient

    def set_distance_threshold_interrupt(
        self, low_mm, high_mm, window="in", int_on_no_target=False
    ):
        """
        Configure a distance threshold interrupt window.
        An interrupt will trigger based on whether the measured range
        is within, outside, above, or below the defined threshold.
        """
        SYSTEM__INTERRUPT_CONFIG_GPIO = 0x0046
        SYSTEM__THRESH_HIGH = 0x0072
        SYSTEM__THRESH_LOW = 0x0074

        # Convert window type to bit pattern
        if window == "in":
            config_val = 3  # Trigger when inside window
        elif window == "out":
            config_val = 2  # Trigger when outside window
        elif window == "below":
            config_val = 0
        elif window == "above":
            config_val = 1
        else:
            raise ValueError("window must be 'in', 'out', 'below', or 'above'")

        # Read current interrupt config and preserve unrelated bits
        temp = self.readReg(SYSTEM__INTERRUPT_CONFIG_GPIO)
        temp = temp & 0x47  # Mask: preserve bits [6] and [2:0]

        # Set new interrupt mode
        if int_on_no_target:
            temp |= (config_val & 0x07) | 0x40  # Enable "no target" flag (bit 6)
        else:
            temp |= config_val & 0x07

        # Apply config and threshold values
        self.writeReg(SYSTEM__INTERRUPT_CONFIG_GPIO, temp)
        self.writeReg16Bit(SYSTEM__THRESH_LOW, low_mm)
        self.writeReg16Bit(SYSTEM__THRESH_HIGH, high_mm)

    def start_ranging(self):
        """Start continuous ranging mode."""
        self.writeReg(0x86, 0x01)  # SYSTEM__INTERRUPT_CLEAR: clear interrupt
        self.writeReg(0x87, 0x40)  # SYSTEM__MODE_START: start ranging (continuous)

    def stop_ranging(self):
        """Stop ranging (sets SYSTEM__MODE_START to 0)."""
        self.writeReg(0x000, 0x00)  # SYSTEM__MODE_START: 0 = stop

    def enable_interrupt(self):
        """
        Configure sensor interrupt pin behavior:
        - IRQ on measurement ready
        - GPIO active low
        - Interrupt clears on read
        """
        self.writeReg(0x0B, 0x01)  # INTERRUPT_CONFIG_GPIO: new sample ready
        self.writeReg(0x0C, 0x00)  # GPIO_HV_MUX_ACTIVE_HIGH: active low
        self.writeReg(0x0E, 0x01)  # GPIO_INTERRUPT_CLEAR: clear on read

    def clear_interrupt(self):
        """Clear the sensor's interrupt flag manually."""
        self.writeReg(0x86, 0x01)  # SYSTEM__INTERRUPT_CLEAR
