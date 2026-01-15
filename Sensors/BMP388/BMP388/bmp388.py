# FILE: bmp388.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: MicroPython library for the BMP388 temperature and pressure sensor
# LAST UPDATED: 2025-01-15

import struct
import time
from machine import I2C, Pin
from os import uname
from bmp388_constants import *

class BMP388:
    """
    MicroPython class for the Bosch BMP388 temperature and pressure sensor.
    Supports temperature, pressure, and altitude measurements.
    """

    def __init__(self, i2c=None, address=BMP388_I2C_ALT_ADDR):
        """
        Initialize the BMP388 sensor.

        :param i2c: Initialized I2C object
        :param address: I2C address of the sensor (default None = auto-detect)
        """
        if i2c != None:
            self.i2c = i2c
        else:
            if uname().sysname in ("esp32", "esp8266", "Soldered Dasduino CONNECTPLUS"):
                self.i2c = I2C(0, scl=Pin(22), sda=Pin(21))
            else:
                raise Exception("Board not recognized, enter I2C pins manually")

        self.address = address
        self.seaLevelPressure = 1013.23
        self.pwrCtrl = 0x00
        self.osrReg = 0x00
        self.odrReg = 0x00
        self.configReg = 0x00
        self.intCtrl = 0x00
        self.fifoConfig1 = 0x00
        self.fifoConfig2 = 0x00
        self.ifConfig = 0x00
        self.altEnable = False
        if not self.begin():
            raise Exception("BMP388 initialization failed! Check wiring and I2C address.")

    # Read 8-bit unsigned value from a register
    def _read8(self, register):
        """Read a single byte from the specified register."""
        try:
            # Write register address, then read data
            self.i2c.writeto(self.address, bytes([register]))
            data = self.i2c.readfrom(self.address, 1)
            value = data[0]
            return value
        except OSError as e:
            raise Exception(f"I2C read error at address 0x{self.address:02X}, register 0x{register:02X}: {e}")

    # Read multiple bytes from a register
    def _readBytes(self, register, length):
        """Read multiple bytes from the specified register."""
        try:
            # Write register address, then read data
            self.i2c.writeto(self.address, bytes([register]))
            data = self.i2c.readfrom(self.address, length)
            return data
        except OSError as e:
            raise Exception(f"I2C read error at address 0x{self.address:02X}, register 0x{register:02X}: {e}")

    # Write a byte to a register
    def _write8(self, register, value):
        """Write a single byte to the specified register."""
        try:
            # Ensure value is within 8-bit range (0-255)
            value = value & 0xFF
            # Write register address and data in a single transaction
            self.i2c.writeto(self.address, bytes([register, value]))
            time.sleep_us(100)  # Small delay to ensure write completes
        except OSError as e:
            raise Exception(f"I2C write error at address 0x{self.address:02X}, register 0x{register:02X}: {e}")

    def _waitCmdReady(self, timeoutMs=100):
        """Wait until the sensor reports cmd_rdy in STATUS (bit 4)."""
        start = time.ticks_ms()
        while True:
            status = self._read8(BMP388_STATUS)
            if status & 0x10:
                return True
            if time.ticks_diff(time.ticks_ms(), start) > timeoutMs:
                return False
            time.sleep_ms(2)

    # Load all factory calibration parameters from sensor registers
    def _loadCalibrationParams(self):
        """
        Read and store all sensor calibration parameters from internal registers.
        Required for temperature and pressure compensation.
        """
        # Read trim parameters (21 bytes starting at 0x31)
        # The struct is packed: uint16_t, uint16_t, int8_t, int16_t, int16_t, int8_t, int8_t,
        # uint16_t, uint16_t, int8_t, int8_t, int16_t, int8_t, int8_t
        # Write register address, then read data
        self.i2c.writeto(self.address, bytes([BMP388_TRIM_PARAMS]))
        rawParams = self.i2c.readfrom(self.address, 21)

        # Unpack parameters matching the datasheet layout
        # All values are little-endian
        self.param_T1 = struct.unpack("<H", rawParams[0:2])[0]      # uint16_t at offset 0
        self.param_T2 = struct.unpack("<H", rawParams[2:4])[0]      # uint16_t at offset 2
        self.param_T3 = struct.unpack("b", rawParams[4:5])[0]       # int8_t at offset 4
        self.param_P1 = struct.unpack("<h", rawParams[5:7])[0]      # int16_t at offset 5
        self.param_P2 = struct.unpack("<h", rawParams[7:9])[0]      # int16_t at offset 7
        self.param_P3 = struct.unpack("b", rawParams[9:10])[0]      # int8_t at offset 9
        self.param_P4 = struct.unpack("b", rawParams[10:11])[0]     # int8_t at offset 10
        self.param_P5 = struct.unpack("<H", rawParams[11:13])[0]    # uint16_t at offset 11
        self.param_P6 = struct.unpack("<H", rawParams[13:15])[0]    # uint16_t at offset 13
        self.param_P7 = struct.unpack("b", rawParams[15:16])[0]     # int8_t at offset 15
        self.param_P8 = struct.unpack("b", rawParams[16:17])[0]     # int8_t at offset 16
        self.param_P9 = struct.unpack("<h", rawParams[17:19])[0]   # int16_t at offset 17
        self.param_P10 = struct.unpack("b", rawParams[19:20])[0]   # int8_t at offset 19
        self.param_P11 = struct.unpack("b", rawParams[20:21])[0]    # int8_t at offset 20

        # Convert to floating point parameters
        self.floatParam_T1 = float(self.param_T1) / pow(2.0, -8.0)
        self.floatParam_T2 = float(self.param_T2) / pow(2.0, 30.0)
        self.floatParam_T3 = float(self.param_T3) / pow(2.0, 48.0)
        self.floatParam_P1 = (float(self.param_P1) - pow(2.0, 14.0)) / pow(2.0, 20.0)
        self.floatParam_P2 = (float(self.param_P2) - pow(2.0, 14.0)) / pow(2.0, 29.0)
        self.floatParam_P3 = float(self.param_P3) / pow(2.0, 32.0)
        self.floatParam_P4 = float(self.param_P4) / pow(2.0, 37.0)
        self.floatParam_P5 = float(self.param_P5) / pow(2.0, -3.0)
        self.floatParam_P6 = float(self.param_P6) / pow(2.0, 6.0)
        self.floatParam_P7 = float(self.param_P7) / pow(2.0, 8.0)
        self.floatParam_P8 = float(self.param_P8) / pow(2.0, 15.0)
        self.floatParam_P9 = float(self.param_P9) / pow(2.0, 48.0)
        self.floatParam_P10 = float(self.param_P10) / pow(2.0, 48.0)
        self.floatParam_P11 = float(self.param_P11) / pow(2.0, 65.0)

    # Initialize the sensor
    def begin(
        self,
        mode=SLEEP_MODE,
        presOversampling=OVERSAMPLING_X16,
        tempOversampling=OVERSAMPLING_X2,
        iirFilter=IIR_FILTER_OFF,
        timeStandby=TIME_STANDBY_5MS,
    ):
        """
        Initialize the BMP388 with specified settings.

        :param mode: Operating mode (SLEEP_MODE, FORCED_MODE, NORMAL_MODE)
        :param presOversampling: Pressure oversampling (OVERSAMPLING_X2 to X32)
        :param tempOversampling: Temperature oversampling (OVERSAMPLING_X2 to X32)
        :param iirFilter: IIR filter setting (IIR_FILTER_OFF to IIR_FILTER_128)
        :param timeStandby: Time standby setting (TIME_STANDBY_5MS to TIME_STANDBY_10240MS)
        :return: True if initialization successful, False otherwise
        """
        # Reset the sensor
        if not self.reset():
            return False

        # Wait a bit longer after reset to ensure sensor is fully ready
        time.sleep_ms(20)
        if not self._waitCmdReady(timeoutMs=100):
            pass

        # Check chip ID
        chipId = self._read8(BMP388_CHIP_ID)
        if chipId != BMP388_ID and chipId != BMP390_ID:
            return False

        # Load calibration parameters (must be done after reset and chip ID check)
        self._loadCalibrationParams()
        
        # Small delay after loading calibration
        time.sleep_ms(10)

        # Configure sensor
        if not self._waitCmdReady(timeoutMs=100):
            pass
        # Ensure interface config is in a known state (disable I2C watchdog, SPI 3-wire off)
        self._write8(BMP388_IF_CONFIG, 0x00)
        self.setIIRFilter(iirFilter)
        self.setTimeStandby(timeStandby)
        self.setOversampling(presOversampling, tempOversampling)

        # Enable pressure and temperature sensors, then set mode
        # According to BMP388 datasheet (register 0x1B):
        # Bit 0: press_en, Bit 1: temp_en, Bits 2-3: reserved (must be 0), Bits 4-5: mode
        # Initialize internal state
        self.pwrCtrl = 0x00  # Start with all bits clear
        self.pwrCtrl |= 0x01  # Set press_en (bit 0)
        self.pwrCtrl |= 0x02  # Set temp_en (bit 1)
        # Now set mode bits (bits 4-5)
        self.pwrCtrl |= ((mode & 0x03) << 4)
        
        # Write the complete register value in one go
        if not self._waitCmdReady(timeoutMs=100):
            pass
        self._write8(BMP388_PWR_CTRL, self.pwrCtrl)
        time.sleep_ms(50)  # Wait for register to update
        
        # Verify the write succeeded
        verify = self._read8(BMP388_PWR_CTRL)
        if verify != self.pwrCtrl:
            errReg = self._read8(BMP388_ERR_REG)
            # Try one more time with longer delay
            time.sleep_ms(100)
            self._write8(BMP388_PWR_CTRL, self.pwrCtrl)
            time.sleep_ms(100)
            verify = self._read8(BMP388_PWR_CTRL)
            if verify != self.pwrCtrl:
                pass
        
        # Update internal state to match what's actually in the register
        self.pwrCtrl = verify
        
        # Verify mode was set
        finalPwrCtrl = self._read8(BMP388_PWR_CTRL)
        finalMode = (finalPwrCtrl & 0x30) >> 4
        if finalMode != mode:
            print(f"Warning: Failed to set mode. Expected {mode}, got {finalMode}. PWR_CTRL=0x{finalPwrCtrl:02X}")

        return True

    # Reset the sensor
    def reset(self):
        """Soft reset the BMP388 sensor."""
        self._write8(BMP388_CMD, RESET_CODE)
        time.sleep_ms(10)
        eventReg = self._read8(BMP388_EVENT)
        return (eventReg & 0x01) != 0  # Check por_detected bit

    # Set the operating mode
    def setMode(self, mode):
        """Set the BMP388 operating mode."""
        # Read current register to get actual state (press_en and temp_en should already be set)
        currentPwrCtrl = self._read8(BMP388_PWR_CTRL)
        # Update internal state: preserve press_en and temp_en (bits 0-1), set mode (bits 4-5)
        # Bits 2-3 are reserved and must be 0 (already cleared by masking with 0x03)
        # Clear mode bits (4-5), then set new mode
        self.pwrCtrl = (currentPwrCtrl & 0x03) | ((mode & 0x03) << 4)
        
        # Write the complete register value
        if not self._waitCmdReady(timeoutMs=100):
            pass
        self._write8(BMP388_PWR_CTRL, self.pwrCtrl)
        time.sleep_ms(20)  # Wait longer for register to update (sensor may need time to process mode change)
        
        # Verify the write succeeded
        verifyPwrCtrl = self._read8(BMP388_PWR_CTRL)
        if verifyPwrCtrl != self.pwrCtrl:
            # Write failed - try one more time with fresh read
            errReg = self._read8(BMP388_ERR_REG)
            # If configuration error (conf_err), try a safer ODR/OSR combo before retry
            if errReg & 0x04:
                # Use slower ODR and lower oversampling to satisfy timing constraints
                self.setTimeStandby(TIME_STANDBY_80MS)
                self.setOversampling(OVERSAMPLING_X2, OVERSAMPLING_X2)
            time.sleep_ms(10)
            if not self._waitCmdReady(timeoutMs=100):
                pass
            currentPwrCtrl = self._read8(BMP388_PWR_CTRL)
            self.pwrCtrl = (currentPwrCtrl & 0x03) | ((mode & 0x03) << 4)
            self._write8(BMP388_PWR_CTRL, self.pwrCtrl)
            time.sleep_ms(20)
            verifyPwrCtrl = self._read8(BMP388_PWR_CTRL)
            if verifyPwrCtrl != self.pwrCtrl:
                pass
        
        # Update internal state to match what's actually in the register
        self.pwrCtrl = verifyPwrCtrl

    # Set oversampling rates
    def setOversampling(self, presOversampling, tempOversampling):
        """Set pressure and temperature oversampling rates."""
        self.osrReg = ((tempOversampling & 0x07) << 3) | (presOversampling & 0x07)
        self._write8(BMP388_OSR, self.osrReg)

    # Set pressure oversampling
    def setPresOversampling(self, presOversampling):
        """Set the pressure oversampling rate."""
        self.osrReg = (self.osrReg & 0xF8) | (presOversampling & 0x07)
        self._write8(BMP388_OSR, self.osrReg)

    # Set temperature oversampling
    def setTempOversampling(self, tempOversampling):
        """Set the temperature oversampling rate."""
        self.osrReg = (self.osrReg & 0xC7) | ((tempOversampling & 0x07) << 3)
        self._write8(BMP388_OSR, self.osrReg)

    # Set IIR filter
    def setIIRFilter(self, iirFilter):
        """Set the IIR filter setting."""
        self.configReg = (self.configReg & 0xF1) | ((iirFilter & 0x07) << 1)
        self._write8(BMP388_CONFIG, self.configReg)

    # Set time standby
    def setTimeStandby(self, timeStandby):
        """Set the time standby measurement interval."""
        self.odrReg = timeStandby & 0x1F
        self._write8(BMP388_ODR, self.odrReg)

    # Set sea level pressure
    def setSeaLevelPressure(self, pressure):
        """Set the sea level pressure value for altitude calculations."""
        self.seaLevelPressure = pressure

    # Check if data is ready
    def _dataReady(self, debug=False):
        """Check if measurement data is ready."""
        # Use cached mode; forced mode can return to sleep before INT_STATUS is read
        mode = (self.pwrCtrl & 0x30) >> 4

        # Read interrupt status register
        intStatus = self._read8(BMP388_INT_STATUS)
        drdy = (intStatus & 0x08) != 0  # Check drdy bit (bit 3)

        if debug:
            currentPwrCtrl = self._read8(BMP388_PWR_CTRL)
            print(f"INT_STATUS: 0x{intStatus:02X} (drdy={drdy}), PWR_CTRL: 0x{currentPwrCtrl:02X} (mode={mode})")

        if drdy:
            # If in FORCED_MODE, switch back to SLEEP_MODE
            if mode == FORCED_MODE:
                self.setMode(SLEEP_MODE)
            return True

        if mode == SLEEP_MODE:
            return False

        return False

    # Start normal conversion mode
    def startNormalConversion(self):
        """Start continuous measurement in NORMAL_MODE."""
        self.setMode(NORMAL_MODE)
        # Give sensor time to start conversion
        # With OVERSAMPLING_X16 for pressure and X2 for temp, first measurement takes longer
        time.sleep_ms(100)

    # Start forced conversion mode
    def startForcedConversion(self):
        """Start a one-shot measurement in FORCED_MODE."""
        if (self.pwrCtrl & 0x30) == SLEEP_MODE:
            self.setMode(FORCED_MODE)

    # Stop conversion
    def stopConversion(self):
        """Stop the conversion and return to SLEEP_MODE."""
        self.setMode(SLEEP_MODE)

    # Temperature compensation function
    def _compensateTemp(self, uncompTemp):
        """Bosch temperature compensation function."""
        partialData1 = uncompTemp - self.floatParam_T1
        partialData2 = partialData1 * self.floatParam_T2
        return partialData2 + partialData1 * partialData1 * self.floatParam_T3

    # Pressure compensation function
    def _compensatePress(self, uncompPress, tLin):
        """Bosch pressure compensation function."""
        partialData1 = self.floatParam_P6 * tLin
        partialData2 = self.floatParam_P7 * tLin * tLin
        partialData3 = self.floatParam_P8 * tLin * tLin * tLin
        partialOut1 = self.floatParam_P5 + partialData1 + partialData2 + partialData3

        partialData1 = self.floatParam_P2 * tLin
        partialData2 = self.floatParam_P3 * tLin * tLin
        partialData3 = self.floatParam_P4 * tLin * tLin * tLin
        partialOut2 = uncompPress * (
            self.floatParam_P1 + partialData1 + partialData2 + partialData3
        )

        partialData1 = uncompPress * uncompPress
        partialData2 = self.floatParam_P9 + self.floatParam_P10 * tLin
        partialData3 = partialData1 * partialData2
        partialData4 = (
            partialData3 + uncompPress * uncompPress * uncompPress * self.floatParam_P11
        )

        return partialOut1 + partialOut2 + partialData4

    # Get temperature measurement
    def getTemperature(self):
        """
        Get a temperature measurement.

        :return: Temperature in Celsius if data ready, None otherwise
        """
        if not self._dataReady():
            return None

        # Read temperature data (3 bytes: DATA_3, DATA_4, DATA_5)
        data = self._readBytes(BMP388_DATA_3, 3)
        adcTemp = (data[2] << 16) | (data[1] << 8) | data[0]

        temperature = self._compensateTemp(float(adcTemp))
        return temperature

    # Get pressure measurement
    def getPressure(self):
        """
        Get a pressure measurement.

        :return: Pressure in hPa if data ready, None otherwise
        """
        temperature, pressure = self.getTempPres()
        if temperature is None:
            return None
        return pressure

    # Get temperature and pressure measurements
    def getTempPres(self, debug=False):
        """
        Get temperature and pressure measurements.

        :return: Tuple (temperature in Celsius, pressure in hPa) if data ready, (None, None) otherwise
        """
        if not self._dataReady(debug=debug):
            return (None, None)

        # Read all 6 bytes starting from DATA_0
        # Data order: DATA_0 (P XLSB), DATA_1 (P LSB), DATA_2 (P MSB), DATA_3 (T XLSB), DATA_4 (T LSB), DATA_5 (T MSB)
        data = self._readBytes(BMP388_DATA_0, 6)

        # Construct 24-bit values
        # Pressure: data[2] (MSB) << 16 | data[1] (LSB) << 8 | data[0] (XLSB)
        # Temperature: data[5] (MSB) << 16 | data[4] (LSB) << 8 | data[3] (XLSB)
        adcPres = (data[2] << 16) | (data[1] << 8) | data[0]
        adcTemp = (data[5] << 16) | (data[4] << 8) | data[3]

        temperature = self._compensateTemp(float(adcTemp))
        pressure = self._compensatePress(float(adcPres), temperature)
        pressure /= 100.0  # Convert to hPa

        return (temperature, pressure)

    # Get altitude measurement
    def getAltitude(self):
        """
        Get an altitude measurement.

        :return: Altitude in meters if data ready, None otherwise
        """
        temperature, pressure, altitude = self.getMeasurements()
        if temperature is None:
            return None
        return altitude

    # Get all measurements (temperature, pressure, altitude)
    def getMeasurements(self, debug=False):
        """
        Get temperature, pressure, and altitude measurements.

        :return: Tuple (temperature in Celsius, pressure in hPa, altitude in meters) if data ready,
                 (None, None, None) otherwise
        """
        temperature, pressure = self.getTempPres(debug=debug)
        if temperature is None:
            return (None, None, None)

        # Calculate altitude using the barometric formula
        altitude = (
            (pow(self.seaLevelPressure / pressure, 0.190223) - 1.0)
            * (temperature + 273.15)
            / 0.0065
        )

        return (temperature, pressure, altitude)

    def enableInterrupt(self, outputDrive=PUSH_PULL, activeLevel=ACTIVE_HIGH, latchConfig=UNLATCHED):
        """Enable data-ready interrupt on the INT pin."""
        self.intCtrl = (latchConfig & 0x01) << 2 | (activeLevel & 0x01) << 1 | (outputDrive & 0x01)
        self.intCtrl |= (1 << 6)
        self._write8(BMP388_INT_CTRL, self.intCtrl)

    def disableInterrupt(self):
        """Disable data-ready interrupt on the INT pin."""
        self.intCtrl &= ~(1 << 6)
        self._write8(BMP388_INT_CTRL, self.intCtrl)

    def setIntOutputDrive(self, outputDrive):
        """Set the interrupt pin output drive."""
        self.intCtrl = (self.intCtrl & ~0x01) | (outputDrive & 0x01)
        self._write8(BMP388_INT_CTRL, self.intCtrl)

    def setIntActiveLevel(self, activeLevel):
        """Set the interrupt active level."""
        self.intCtrl = (self.intCtrl & ~0x02) | ((activeLevel & 0x01) << 1)
        self._write8(BMP388_INT_CTRL, self.intCtrl)

    def setIntLatchConfig(self, latchConfig):
        """Set the interrupt latch configuration."""
        self.intCtrl = (self.intCtrl & ~0x04) | ((latchConfig & 0x01) << 2)
        self._write8(BMP388_INT_CTRL, self.intCtrl)

    def enableFIFO(self, pressEnable=PRESS_ENABLED, altEnable=ALT_ENABLED, timeEnable=TIME_ENABLED,
                   subsampling=SUBSAMPLING_OFF, dataSelect=FILTERED, stopOnFull=STOP_ON_FULL_ENABLED):
        """Enable FIFO operation with the selected configuration."""
        self.altEnable = altEnable == ALT_ENABLED
        self.fifoConfig1 = (1 << 4) | ((pressEnable & 0x01) << 3) | ((timeEnable & 0x01) << 2) | ((stopOnFull & 0x01) << 1) | 0x01
        self.fifoConfig2 = ((dataSelect & 0x07) << 3) | (subsampling & 0x07)
        self._write8(BMP388_FIFO_CONFIG_1, self.fifoConfig1)
        self._write8(BMP388_FIFO_CONFIG_2, self.fifoConfig2)

    def disableFIFO(self):
        """Disable FIFO operation."""
        self.fifoConfig1 &= ~0x01
        self._write8(BMP388_FIFO_CONFIG_1, self.fifoConfig1)

    def setFIFONoOfMeasurements(self, noOfMeasurements):
        """Set FIFO watermark based on number of measurements."""
        fifoPress = (self.fifoConfig1 >> 3) & 0x01
        fifoTemp = (self.fifoConfig1 >> 4) & 0x01
        fifoWatermark = noOfMeasurements * ((fifoPress | fifoTemp) + 3 * fifoPress + 3 * fifoTemp)
        return self.setFIFOWatermark(fifoWatermark)

    def setFIFOWatermark(self, fifoWatermark):
        """Set FIFO watermark value."""
        fifoTime = (self.fifoConfig1 >> 2) & 0x01
        if fifoWatermark + fifoTime + 3 * fifoTime + 2 > FIFO_SIZE:
            return False
        fifoWatermarkLSB = fifoWatermark & 0xFF
        fifoWatermarkMSB = (fifoWatermark >> 8) & 0x01
        self._write8(BMP388_FIFO_WTM_0, fifoWatermarkLSB)
        self._write8(BMP388_FIFO_WTM_1, fifoWatermarkMSB)
        return True

    def getFIFOWatermark(self):
        """Get FIFO watermark value."""
        data = self._readBytes(BMP388_FIFO_WTM_0, 2)
        return data[0] | (data[1] << 8)

    def setFIFOPressEnable(self, pressEnable):
        """Enable or disable pressure data in FIFO."""
        self.fifoConfig1 = (self.fifoConfig1 & ~(1 << 3)) | ((pressEnable & 0x01) << 3)
        self._write8(BMP388_FIFO_CONFIG_1, self.fifoConfig1)

    def setFIFOTimeEnable(self, timeEnable):
        """Enable or disable sensor time in FIFO."""
        self.fifoConfig1 = (self.fifoConfig1 & ~(1 << 2)) | ((timeEnable & 0x01) << 2)
        self._write8(BMP388_FIFO_CONFIG_1, self.fifoConfig1)

    def setFIFOSubsampling(self, subsampling):
        """Set FIFO subsampling rate."""
        self.fifoConfig2 = (self.fifoConfig2 & ~0x07) | (subsampling & 0x07)
        self._write8(BMP388_FIFO_CONFIG_2, self.fifoConfig2)

    def setFIFODataSelect(self, dataSelect):
        """Set FIFO data selection (filtered or unfiltered)."""
        self.fifoConfig2 = (self.fifoConfig2 & ~(0x07 << 3)) | ((dataSelect & 0x07) << 3)
        self._write8(BMP388_FIFO_CONFIG_2, self.fifoConfig2)

    def setFIFOStopOnFull(self, stopOnFull):
        """Set FIFO stop on full configuration."""
        self.fifoConfig1 = (self.fifoConfig1 & ~(1 << 1)) | ((stopOnFull & 0x01) << 1)
        self._write8(BMP388_FIFO_CONFIG_1, self.fifoConfig1)

    def getFIFOLength(self):
        """Get FIFO length in bytes."""
        data = self._readBytes(BMP388_FIFO_LENGTH_0, 2)
        return data[0] | (data[1] << 8)

    def getFIFOData(self):
        """Read FIFO data and return status and measurements."""
        if not self.fifoReady():
            return (FIFO_DATA_PENDING, [], [], [], 0)

        configError = False
        fifoTime = (self.fifoConfig1 >> 2) & 0x01
        fifoPress = (self.fifoConfig1 >> 3) & 0x01
        fifoTemp = (self.fifoConfig1 >> 4) & 0x01

        fifoLength = self.getFIFOLength() + fifoTime + 3 * fifoTime
        packetSize = (fifoPress | fifoTemp) + 3 * fifoPress + 3 * fifoTemp

        temperatures = []
        pressures = []
        altitudes = []
        sensorTime = 0
        count = 0

        while count < fifoLength:
            data = self._readBytes(BMP388_FIFO_DATA, packetSize if packetSize else 1)
            header = data[0]

            if header == FIFO_SENSOR_PRESS:
                adcTemp = (data[3] << 16) | (data[2] << 8) | data[1]
                temperature = self._compensateTemp(float(adcTemp))
                adcPres = (data[6] << 16) | (data[5] << 8) | data[4]
                pressure = self._compensatePress(float(adcPres), temperature) / 100.0
                temperatures.append(temperature)
                pressures.append(pressure)
                if self.altEnable:
                    altitude = (
                        (pow(self.seaLevelPressure / pressure, 0.190223) - 1.0)
                        * (temperature + 273.15)
                        / 0.0065
                    )
                    altitudes.append(altitude)
                count += 6
            elif header == FIFO_SENSOR_TEMP:
                adcTemp = (data[3] << 16) | (data[2] << 8) | data[1]
                temperature = self._compensateTemp(float(adcTemp))
                temperatures.append(temperature)
                count += 3
            elif header == FIFO_SENSOR_TIME:
                sensorTime = (data[3] << 16) | (data[2] << 8) | data[1]
                count += 3
            elif header in (FIFO_CONFIG_CHANGE, FIFO_EMPTY):
                count += 1
            elif header == FIFO_CONFIG_ERROR_HEADER:
                configError = True
                count += 1
            else:
                count += 1

        status = FIFO_CONFIG_ERROR if configError else FIFO_DATA_READY
        return (status, temperatures, pressures, altitudes, sensorTime)

    def enableFIFOInterrupt(self, outputDrive=PUSH_PULL, activeLevel=ACTIVE_HIGH, latchConfig=UNLATCHED):
        """Enable FIFO watermark/full interrupts on the INT pin."""
        self.intCtrl = (latchConfig & 0x01) << 2 | (activeLevel & 0x01) << 1 | (outputDrive & 0x01)
        self.intCtrl |= (1 << 3) | (1 << 4)
        self._write8(BMP388_INT_CTRL, self.intCtrl)

    def disableFIFOInterrupt(self):
        """Disable FIFO watermark/full interrupts on the INT pin."""
        self.intCtrl &= ~((1 << 3) | (1 << 4))
        self._write8(BMP388_INT_CTRL, self.intCtrl)

    def flushFIFO(self):
        """Flush the FIFO buffer."""
        self._write8(BMP388_CMD, FIFO_FLUSH)

    def getSensorTime(self):
        """Read the sensor time value."""
        data = self._readBytes(BMP388_SENSORTIME_0, 3)
        return (data[2] << 16) | (data[1] << 8) | data[0]

    def enableI2CWatchdog(self):
        """Enable I2C watchdog."""
        self.ifConfig = self._read8(BMP388_IF_CONFIG) | (1 << 1)
        self._write8(BMP388_IF_CONFIG, self.ifConfig)

    def disableI2CWatchdog(self):
        """Disable I2C watchdog."""
        self.ifConfig = self._read8(BMP388_IF_CONFIG) & ~(1 << 1)
        self._write8(BMP388_IF_CONFIG, self.ifConfig)

    def setI2CWatchdogTimeout(self, watchdogTimeout):
        """Set I2C watchdog timeout."""
        self.ifConfig = (self._read8(BMP388_IF_CONFIG) & ~(1 << 2)) | ((watchdogTimeout & 0x01) << 2)
        self._write8(BMP388_IF_CONFIG, self.ifConfig)

    def fifoReady(self):
        """Check if FIFO data is ready."""
        intStatus = self._read8(BMP388_INT_STATUS)
        drdy = (intStatus & 0x08) != 0
        fwm = (intStatus & 0x01) != 0
        return drdy and fwm

    # Read all values (compatibility with other sensor modules)
    def readAllValues(self):
        """
        Read and return compensated temperature, pressure, and altitude values.

        :return: (temperature °C, pressure hPa, altitude m) 
        """
        return self.getMeasurements()

    # Get error register
    def getErrorReg(self):
        """Read the error register."""
        return self._read8(BMP388_ERR_REG)

    # Get status register
    def getStatusReg(self):
        """Read the status register."""
        return self._read8(BMP388_STATUS)
