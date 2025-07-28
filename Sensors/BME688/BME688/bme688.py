# FILE: bme688.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: A MicroPython module for the Bosch BME688 4-in-1 environmental sensor
# LAST UPDATED: 2025-07-24
from micropython import const
import time
import ustruct
from machine import I2C, Pin
from os import uname
from bme688_const import *


class BME688:
    """Bosch BME688 environmental sensor driver

    Args:
        i2c: Initialized I2C bus
        address: I2C address (default 0x76)
    """

    def __init__(self, i2c=None, address=0x76):
        """Initialize sensor interface

        Args:
            i2c: Initialized I2C bus
            address: I2C address (default 0x76)
        """
        if i2c != None:
            self._i2c = i2c
        else:
            if uname().sysname in ("esp32", "esp8266", "Soldered Dasduino CONNECTPLUS"):
                self._i2c = I2C(0, scl=Pin(22), sda=Pin(21))
            else:
                raise Exception("Board not recognized, enter I2C pins manually")
        self._address = address
        self.printLogs = False
        self.allowHighTemps = False
        self.t_fine = 0
        self.p_fine = 0
        self.h_fine = 0
        self.g_res = 0
        self.cf_p = 1.0
        self.mode = BME_688_SLEEP_MODE
        self.temp_oss = BME_688_OSS_1
        self.press_oss = BME_688_OSS_1
        self.hum_oss = BME_688_OSS_1

        # Calibration parameters
        self.par_t16 = [0, 0]
        self.par_t3 = 0
        self.par_p1 = 0
        self.par_p16 = [0] * 6
        self.par_p8 = [0] * 4
        self.par_p10 = 0
        self.par_h16 = [0, 0]
        self.par_h8 = [0] * 5
        self.par_h6 = 0
        self.par_g1 = 0
        self.par_g2 = 0
        self.par_g3 = 0
        self.res_heat_range = 0
        self.res_heat_val = 0

    def begin(self, mode=None, oss=None):
        """Initialize sensor with specified mode and oversampling

        Args:
            mode: Operation mode (None=forced, 0=sleep, 1=forced, 2=parallel)
            oss: Oversampling setting (None=1x, 0-5 for 1x-16x)

        Returns:
            bool: True if initialization succeeded
        """
        if mode is None and oss is None:
            # Default initialization
            self.i2c_execute(BME_688_CTRL_MEAS_HUM_REG, self.hum_oss)
            self.i2c_execute(
                BME_688_CTRL_MEAS_REG,
                self.temp_oss << 5 | self.press_oss << 2 | BME_688_FORCED_MODE,
            )
            self.i2c_execute(BME_688_IIR_FILTER_REG, BME_688_IIR_FILTER_C15)
            self.readCalibParams()
        elif oss is None:
            # Mode-only initialization
            if mode <= BME_688_PARALLEL_MODE:
                self.i2c_execute(BME_688_CTRL_MEAS_HUM_REG, BME_688_OSS_1)
                self.i2c_execute(
                    BME_688_CTRL_MEAS_REG,
                    BME_688_OSS_1 << 5 | BME_688_OSS_1 << 2 | mode,
                )
                self.i2c_execute(BME_688_IIR_FILTER_REG, BME_688_IIR_FILTER_C15)
                self.readCalibParams()
            else:
                self.printLog(BME_688_VALUE_INVALID)
                return False
        else:
            # Mode and OSS initialization
            if mode <= BME_688_PARALLEL_MODE and oss <= BME_688_OSS_16:
                self.i2c_execute(BME_688_CTRL_MEAS_HUM_REG, oss)
                self.i2c_execute(BME_688_CTRL_MEAS_REG, oss << 5 | oss << 2 | mode)
                self.i2c_execute(BME_688_IIR_FILTER_REG, BME_688_IIR_FILTER_C15)
                self.readCalibParams()
            else:
                self.printLog(BME_688_VALUE_INVALID)
                return False

        return self.isConnected()

    def printLog(self, log):
        print(log)

    def showLogs(self, show):
        self.printLogs = show

    def readCalibParams(self):
        """
        Read all calibration parameters from sensor registers
        Returns True if all parameters were read successfully, False otherwise
        """
        success = True

        # --- Temperature Calibration ---
        temp1 = self.i2c_read_Xbit_LE(BME_688_TEMP_CALIB1_REG, 16)
        temp2 = self.i2c_read_Xbit_LE(BME_688_TEMP_CALIB2_REG, 16)
        temp3 = self.i2c_readByte(BME_688_TEMP_CALIB3_REG, 1)

        if None in (temp1, temp2, temp3):
            self.printLog(BME_688_TEMP_CAL_EXCEPT)
            success = False
        else:
            self.par_t16[0] = temp1
            self.par_t16[1] = temp2
            self.par_t3 = temp3[0] if temp3 else 0

        # --- Pressure Calibration ---
        p1 = self.i2c_read_Xbit_LE(BME_688_PRES_CALIB1_REG, 16)
        p2 = self.i2c_read_Xbit_LE(BME_688_PRES_CALIB2_REG, 16)
        p3 = self.i2c_readByte(BME_688_PRES_CALIB3_REG, 1)
        p4 = self.i2c_read_Xbit_LE(BME_688_PRES_CALIB4_REG, 16)
        p5 = self.i2c_read_Xbit_LE(BME_688_PRES_CALIB5_REG, 16)
        p6 = self.i2c_readByte(BME_688_PRES_CALIB6_REG, 1)
        p7 = self.i2c_readByte(BME_688_PRES_CALIB7_REG, 1)
        p8 = self.i2c_read_Xbit_LE(BME_688_PRES_CALIB8_REG, 16)
        p9 = self.i2c_read_Xbit_LE(BME_688_PRES_CALIB9_REG, 16)
        p10 = self.i2c_readByte(BME_688_PRES_CALIB10_REG, 1)

        if None in (p1, p2, p3, p4, p5, p6, p7, p8, p9, p10):
            self.printLog(BME_688_PRES_CAL_EXCEPT)
            success = False
        else:
            self.par_p1 = p1
            self.par_p16[1] = BME688.to_signed(p2, 16)
            self.par_p8[0] = BME688.to_signed(p3[0], 8)
            self.par_p16[2] = BME688.to_signed(p4, 16)
            self.par_p16[3] = BME688.to_signed(p5, 16)
            self.par_p8[1] = BME688.to_signed(p6[0], 8)
            self.par_p8[2] = BME688.to_signed(p7[0], 8)
            self.par_p16[4] = BME688.to_signed(p8, 16)
            self.par_p16[5] = BME688.to_signed(p9, 16)
            self.par_p10 = BME688.to_signed(p10[0], 8)
            self.par_p8[3] = self.par_p10
            self.par_p16[0] = self.par_p1

        # --- Humidity Calibration ---
        h1 = self.i2c_read_Xbit_LE(BME_688_HUM_CALIB1_REG, 12)
        h2 = self.i2c_read_Xbit(BME_688_HUM_CALIB2_REG, 12)
        h3 = self.i2c_readByte(BME_688_HUM_CALIB3_REG, 1)
        h4 = self.i2c_readByte(BME_688_HUM_CALIB4_REG, 1)
        h5 = self.i2c_readByte(BME_688_HUM_CALIB5_REG, 1)
        h6 = self.i2c_readByte(BME_688_HUM_CALIB6_REG, 1)
        h7 = self.i2c_readByte(BME_688_HUM_CALIB7_REG, 1)

        if None in (h1, h2, h3, h4, h5, h6, h7):
            self.printLog(BME_688_HUM_CAL_EXCEPT)
            success = False
        else:
            self.par_h16[0] = h1
            self.par_h16[1] = h2
            self.par_h8[0] = h3[0] if h3 else 0
            self.par_h8[1] = h4[0] if h4 else 0
            self.par_h8[2] = h5[0] if h5 else 0
            self.par_h6 = h6[0] if h6 else 0
            self.par_h8[4] = h7[0] if h7 else 0  # Note: par_h8[3] not used

        # --- Gas Calibration ---
        g1 = self.i2c_readByte(BME_688_GAS_CALIB1_REG, 1)
        g2 = self.i2c_read_Xbit_LE(BME_688_GAS_CALIB2_REG, 16)
        g3 = self.i2c_readByte(BME_688_GAS_CALIB3_REG, 1)
        heat_range = self.i2c_readByte(BME_688_GAS_HEAT_RANGE_REG, 1)
        heat_val = self.i2c_readByte(BME_688_GAS_HEAT_VAL_REG, 1)

        if None in (g1, g2, g3, heat_range, heat_val):
            self.printLog(BME_688_TEMP_CAL_EXCEPT)
            success = False
        else:
            self.par_g1 = g1[0] if g1 else 0
            self.par_g2 = g2
            self.par_g3 = g3[0] if g3 else 0
            self.res_heat_range = heat_range[0] if heat_range else 0
            self.res_heat_val = heat_val[0] if heat_val else 0
        # Set up heating profiles if all calibrations succeeded
        if success:
            self.setHeatProfiles()

        return success

    def setHeatProfiles(self):
        self.readTemperature()
        for i in range(9):
            gasTemp = self.readUCGas(BME_688_GAS_START_TEMP + i * 25)
            self.i2c_execute(
                BME_688_GAS_WAIT_PROFILE_REG + i,
                BME_688_GAS_WAIT_MULFAC1 << 6 | int(0.25 * gasTemp - 22),
            )
            self.i2c_execute(BME_688_GAS_RES_HEAT_PROFILE_REG + i, gasTemp)
        return True

    def isConnected(self):
        """Check if sensor is connected and returns correct chip ID"""
        try:
            # First check if device responds
            self._i2c.writeto(self._address, b"")
        except OSError:
            self.printLog(
                "I2C device not found at address 0x{:02X}".format(self._address)
            )
            return False

        # Read chip ID
        chip_id = self.i2c_readByte(BME_688_CHIP_ID_REG)
        if chip_id is None:
            self.printLog("Failed to read chip ID")
            return False

        # Handle both bytes object and integer comparison
        expected_id = bytes([BME_688_CHIP_ID])  # b'\x61'
        if isinstance(chip_id, bytes):
            if chip_id == expected_id:
                return True
            self.printLog(
                "Unexpected chip ID: received {} expected {}".format(
                    chip_id, expected_id
                )
            )
        elif chip_id == BME_688_CHIP_ID:  # Integer comparison
            return True

        return False

    def setTemperatureOversampling(self, oss):
        if oss <= BME_688_OSS_16:
            self.temp_oss = oss
        else:
            self.printLog(BME_688_VALUE_INVALID)
            return False
        return True

    def readRawTemp(self):
        raw = 0
        raw = self.i2c_read_Xbit(BME_688_TEMP_RAW_REG, 20)
        return raw

    def readRawPres(self):
        raw = 0
        raw = self.i2c_read_Xbit(BME_688_PRES_RAW_REG, 20)
        return raw

    def readRawHum(self):
        raw = 0
        raw = self.i2c_read_Xbit(BME_688_HUM_RAW_REG, 16)
        return raw

    def readRawGas(self):
        raw = 0
        raw = self.i2c_read_Xbit(BME_688_GAS_RAW_REG, 16)
        return raw

    def readUCTemp(self, adc_T):
        var1 = (adc_T / 16384.0 - self.par_t16[0] / 1024.0) * self.par_t16[1]
        var2 = ((adc_T / 131072.0 - self.par_t16[0] / 8192.0) ** 2) * (
            self.par_t3 * 16.0
        )
        self.t_fine = var1 + var2
        return self.t_fine / 5120.0

    def readUCPres(self, adc_P):
        """Identical pressure calculation to C++ version"""
        # Verify we have temperature calibration
        if not hasattr(self, "t_fine") or self.t_fine == 0:
            self.readTemperature()

        # Note array access pattern:
        # par_p16 = [p1, p2, p4, p5, p8, p9]
        # par_p8 = [p3, p6, p7, p10]

        var1 = (self.t_fine / 2.0) - 64000.0
        var2 = var1 * var1 * (self.par_p8[1] / 131072.0)  # p6
        var2 = var2 + (var1 * self.par_p16[3] * 2.0)  # p5
        var2 = (var2 / 4.0) + (self.par_p16[2] * 65536.0)  # p4

        var1 = (
            ((self.par_p8[0] * var1 * var1) / 16384.0) + (self.par_p16[1] * var1)
        ) / 524288.0  # p3 and p2
        var1 = (1.0 + (var1 / 32768.0)) * self.par_p16[0]  # p1

        if var1 == 0:
            return 0  # Avoid division by zero

        press_comp = 1048576.0 - float(adc_P)
        press_comp = ((press_comp - (var2 / 4096.0)) * 6250.0) / var1

        var1 = (self.par_p16[5] * press_comp * press_comp) / 2147483648.0  # p9
        var2 = press_comp * (self.par_p16[4] / 32768.0)  # p8
        var3 = (
            (press_comp / 256.0)
            * (press_comp / 256.0)
            * (press_comp / 256.0)
            * (self.par_p8[3] / 131072.0)
        )  # p10

        self.p_fine = (
            press_comp + (var1 + var2 + var3 + (self.par_p8[2] * 128.0)) / 16.0
        )  # p7
        return self.p_fine  # Returns pressure in Pascals

    def readUCHum(self, adc_H):
        temp = self.t_fine / 5120.0
        var1 = adc_H - (self.par_h16[0] * 16.0 + (self.par_h8[0] / 2.0) * temp)
        var2 = var1 * (
            (self.par_h16[1] / 262144.0)
            * (
                1.0
                + (self.par_h8[1] / 16384.0) * temp
                + (self.par_h8[2] / 1048576.0) * temp * temp
            )
        )
        var3 = self.par_h6 / 16384.0
        var4 = self.par_h8[4] / 2097152.0
        self.h_fine = var2 + ((var3 + (var4 * temp)) * var2 * var2)
        return self.h_fine

    def readUCGas(self, target_temp):
        temp = self.t_fine / 5120.0
        var1 = (self.par_g1 / 16.0) + 49.0
        var2 = ((self.par_g2 / 32768.0) * 0.0005) + 0.00235
        var3 = self.par_g3 / 1024.0
        var4 = var1 * (1.0 + (var2 * target_temp))
        var5 = var4 + (var3 * temp)
        self.g_fine = int(
            3.4
            * (
                var5
                * (
                    4.0
                    / (4.0 + ((self.res_heat_range & BME_688_HEAT_RANGE_MASK) >> 4))
                    * (1.0 / (1.0 + (self.res_heat_val * 0.002)))
                    - 25
                )
            )
        )
        return self.g_fine

    def checkGasMeasurementCompletion(self):
        m_Complete = 0
        self.i2c_readByte(BME_688_GAS_MEAS_STATUS_REG1, m_Complete, 1)
        m_Complete &= BME_688_GAS_HEAT_STAB_MASK | BME_688_GAS_VALID_REG_MASK
        return m_Complete == BME_688_GAS_MEAS_FINISH

    def readTemperature(self):
        """Read compensated temperature value

        Returns:
            float: Temperature in °C
            None: If reading failed
        """
        # Trigger new measurement
        self.i2c_execute(
            BME_688_CTRL_MEAS_REG,
            self.temp_oss << 5 | self.press_oss << 2 | BME_688_FORCED_MODE,
        )
        # Wait for measurement to complete (depends on oversampling)
        time.sleep_ms(self.getMeasurementDelay())
        raw_temp = self.readRawTemp()
        if raw_temp is None:
            return None
        return self.readUCTemp(raw_temp)

    def readPressure(self):
        """Read compensated pressure value

        Returns:
            float: Pressure in Pascals
            None: If reading failed
        """
        # Share the same measurement as temperature (t_fine is needed)
        self.readTemperature()  # Ensure we have a recent temperature reading
        raw_pres = self.readRawPres()
        if raw_pres is None:
            return None
        return self.readUCPres(raw_pres)

    def readHumidity(self):
        """Read compensated humidity value

        Returns:
            float: Relative humidity in %RH
            None: If reading failed
        """
        # Configure humidity first
        self.i2c_execute(BME_688_CTRL_MEAS_HUM_REG, self.hum_oss)
        # Then trigger a new measurement
        self.i2c_execute(
            BME_688_CTRL_MEAS_REG,
            self.temp_oss << 5 | self.press_oss << 2 | BME_688_FORCED_MODE,
        )
        time.sleep_ms(self.getMeasurementDelay())
        raw_hum = self.readRawHum()
        if raw_hum is None:
            return None
        return self.readUCHum(raw_hum)

    def getMeasurementDelay(self):
        """Calculate minimum delay needed based on oversampling settings

        Returns:
            int: Required delay in milliseconds
        """
        delay = 5  # Base delay in ms
        # Add delays for each oversampling setting
        delay += (1 << self.temp_oss) * 2
        delay += (1 << self.press_oss) * 2
        delay += (1 << self.hum_oss) * 2
        return delay

    def startGasMeasurement(self, profile, waitTime):
        """Perform a gas resistance measurement using specified heating profile

        Handles the complete gas measurement sequence:
        1. Enables gas heater with specified profile
        2. Triggers a forced mode measurement
        3. Waits for measurement completion
        4. Validates measurement stability
        5. Calculates gas resistance from raw values

        Args:
            profile (int): Heating profile to use (0-9)
            waitTime (int): Duration in ms to wait for measurement completion

        Returns:
            float: Gas resistance in Ohms
            None: If any step in the measurement fails
            -2.0: If measurement didn't stabilize

        Note:
            Requires prior configuration of heating profiles via setHeatProfiles()
        """
        # Enable gas heater
        if not self.i2c_execute(BME_688_CTRL_GAS_REG, BME_688_GAS_RUN | profile):
            return None

        # Trigger measurement
        if not self.i2c_execute(
            BME_688_CTRL_MEAS_REG,
            self.temp_oss << 5 | self.press_oss << 2 | BME_688_FORCED_MODE,
        ):
            return None

        # Wait for measurement
        time.sleep_ms(waitTime)

        # Check if measurement completed
        status = self.i2c_readByte(BME_688_GAS_MEAS_STATUS_REG1, 1)
        if status is None:
            return None

        if not (status[0] & (BME_688_GAS_HEAT_STAB_MASK | BME_688_GAS_VALID_REG_MASK)):
            self.printLog(BME_688_GAS_MEAS_FAILURE)
            return -2.0

        # Read and calculate gas resistance
        gas_adc = self.i2c_read_Xbit(BME_688_GAS_ADC_REG, 10)
        gas_range = self.i2c_readByte(BME_688_GAS_RANGE_REG, 1)

        if None in (gas_adc, gas_range):
            return None

        gas_range = gas_range[0] & BME_688_GAS_RANGE_VAL_MASK
        var1 = 262144 >> gas_range
        var2 = gas_adc - 512
        var2 *= 3
        var2 = 4096 + var2
        self.g_res = 1000000.0 * var1 / var2
        return self.g_res

    def readGasForTemperature(self, temperature):
        """Perform gas measurement at specific target temperature

        Args:
            temperature (int): Target heater temperature in °C (200-450 typical)

        Returns:
            float: Gas resistance in Ohms
            -1.0: If temperature exceeds safety limits
            -2.0: If measurement fails

        Note:
            For temperatures >350°C, must call ignoreUnsafeTemperatureWarnings(True)
        """
        if self.allowHighTemps or temperature <= BME_688_HEAT_PLATE_MAX_TEMP:
            if temperature < BME_688_HEAT_PLATE_ULTRA_TEMP:
                t_temp = self.readUCGas(temperature)
                t_wait = int(0.25 * t_temp - 17)
                self.i2c_execute(BME_688_CTRL_GAS_REG, 0x20)
                self.i2c_execute(BME_688_GAS_WAIT_PROFILE_REG, t_wait)
                self.i2c_execute(BME_688_GAS_RES_HEAT_PROFILE_REG, t_temp)
                return self.startGasMeasurement(BME_688_GAS_PROFILE_START, t_wait + 5)
            else:
                self.printLog(BME_688_TEMP_EXCEED_MAX_LIMIT)
        else:
            self.printLog(BME_688_TEMP_WARNING)
        return -1.0

    def readGas(self, profile):
        """Perform gas measurement using predefined heating profile

        Args:
            profile (int): Heating profile index (0-9)

        Returns:
            float: Gas resistance in Ohms
            -1.0: If profile is invalid
            -2.0: If measurement fails

        Note:
            Profiles are configured during begin() via setHeatProfiles()
            Each profile has predefined temperature and timing settings
        """
        if 0 <= profile < 10:
            return self.startGasMeasurement(
                profile,
                int(0.25 * self.readUCGas(BME_688_GAS_START_TEMP + profile * 25) - 17),
            )
        else:
            self.printLog(BME_688_PROFILE_OUT_OF_RANGE)
        return -1.0

    def ignoreUnsafeTemperatureWarnings(self, ignore):
        """Enable/disable safety checks for high heater temperatures

        Args:
            ignore (bool): True to allow unsafe temperatures (>350°C)
                          False to enable safety checks

        Warning:
            Using high temperatures (>350°C) may:
            - Reduce sensor lifespan
            - Cause inaccurate readings
            - Potentially damage the sensor
        """
        self.allowHighTemps = ignore
        self.printLog(BME_688_TEMP_UNSAFE_WARNING)

    def is_sensor_connected(self):
        """Check basic I2C connectivity to sensor

        Returns:
            bool: True if device responds to I2C, False otherwise

        Note:
            This only verifies I2C communication, not full sensor functionality
        """
        try:
            self._i2c.writeto(self._address, b"")
            return True
        except OSError:
            return False

    # I2C communication methods
    def i2c_execute(self, reg, data):
        """Write single byte to I2C register"""
        try:
            # Ensure data is within 8-bit range (0-255)
            data = data & 0xFF
            self._i2c.writeto_mem(self._address, reg, bytes([data]))
            return True
        except OSError as e:
            self.printLog(f"I2C write failed to reg 0x{reg:02X}: {e}")
            return False

    def i2c_execute_16bit(self, reg, data):
        """Write 16-bit value to I2C register"""
        try:
            # Ensure data is within 16-bit range (0-65535)
            data = data & 0xFFFF
            # Split into two bytes (MSB first)
            msb = (data >> 8) & 0xFF
            lsb = data & 0xFF
            self._i2c.writeto_mem(self._address, reg, bytes([msb, lsb]))
            return True
        except OSError as e:
            self.printLog(f"I2C 16-bit write failed to reg 0x{reg:02X}: {e}")
            return False

    def i2c_readByte(self, reg, length=1):
        """Read bytes from I2C register"""
        try:
            return self._i2c.readfrom_mem(self._address, reg, length)
        except OSError as e:
            self.printLog(f"I2C read failed: {e}")
            return None

    def i2c_read_Xbit_LE(self, reg, length):
        """Read X bits from register (little-endian)"""
        bytes_to_read = (length + 7) // 8
        data = self.i2c_readByte(reg, bytes_to_read)
        if data is None:
            return None

        temp = 0
        for i in range(bytes_to_read):
            temp |= data[i] << (8 * i)

        if length % 8:
            temp >>= 8 - (length % 8)

        return temp

    def i2c_read_Xbit(self, reg, length):
        """Read X bits from register (big-endian)"""
        bytes_to_read = (length + 7) // 8
        data = self.i2c_readByte(reg, bytes_to_read)
        if data is None:
            return None

        temp = 0
        for i in range(bytes_to_read):
            temp |= data[i] << (8 * (bytes_to_read - 1 - i))

        if length % 8:
            temp >>= 8 - (length % 8)

        return temp

    @staticmethod
    def to_signed(value, bits):
        """Convert unsigned value to signed integer

        Args:
            value: Raw unsigned value
            bits: Bit length of value

        Returns:
            int: Signed value
        """
        if value & (1 << (bits - 1)):
            value -= 1 << bits
        return value
