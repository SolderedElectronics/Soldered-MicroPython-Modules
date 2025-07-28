# FILE: bme688_const
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: Constants used in the main BME688 module
# LAST UPDATED: 2025-07-24

# I2C Addresses
BME688_I2C_ADDR_PRIMARY = const(0x76)
BME688_I2C_ADDR_SECONDARY = const(0x76)

# Status Codes
BME688_OK = const(0)
BME688_E_NULL_PTR = const(-1)
BME688_E_COM_FAIL = const(-2)
BME688_E_DEV_NOT_FOUND = const(-3)
BME688_E_INVALID_LENGTH = const(-4)
BME688_E_DEV_NOT_POWERED = const(-5)
BME688_E_USER_REG = const(-6)
BME688_E_I2C = const(-7)
BME688_E_I2C_TIMEOUT = const(-8)
BME688_E_I2C_FAIL = const(-9)
BME688_E_SENSOR_NOT_SUPPORTED = const(-10)
BME688_E_SENSOR_NOT_ENABLED = const(-11)
BME688_E_SENSOR_NOT_POWERED = const(-12)

# Control Registers
BME_688_CTRL_MEAS_REG = const(0x74)
BME_688_CTRL_MEAS_HUM_REG = const(0x72)

# Oversampling Settings
BME_688_OSS_NONE = const(0x00)
BME_688_OSS_1 = const(0x01)
BME_688_OSS_2 = const(0x02)
BME_688_OSS_4 = const(0x03)
BME_688_OSS_8 = const(0x04)
BME_688_OSS_16 = const(0x05)

# Operation Modes
BME_688_SLEEP_MODE = const(0x00)
BME_688_FORCED_MODE = const(0x01)
BME_688_PARALLEL_MODE = const(0x02)

# Data Registers
BME_688_TEMP_RAW_REG = const(0x22)
BME_688_PRES_RAW_REG = const(0x1F)
BME_688_HUM_RAW_REG = const(0x25)
BME_688_CTRL_GAS_REG = const(0x71)
BME_688_GAS_RAW_REG = const(0x2C)
BME_688_GAS_RANGE_REG = const(0x2C)
BME_688_GAS_ADC_REG = const(0x2C)

# Temperature Calibration Registers
BME_688_TEMP_CALIB1_REG = const(0xE9)
BME_688_TEMP_CALIB2_REG = const(0x8A)
BME_688_TEMP_CALIB3_REG = const(0x8C)

# Pressure Calibration Registers
BME_688_PRES_CALIB1_REG = const(0x8E)
BME_688_PRES_CALIB2_REG = const(0x90)
BME_688_PRES_CALIB3_REG = const(0x92)
BME_688_PRES_CALIB4_REG = const(0x94)
BME_688_PRES_CALIB5_REG = const(0x96)
BME_688_PRES_CALIB6_REG = const(0x99)
BME_688_PRES_CALIB7_REG = const(0x98)
BME_688_PRES_CALIB8_REG = const(0x9C)
BME_688_PRES_CALIB9_REG = const(0x9E)
BME_688_PRES_CALIB10_REG = const(0xA0)

# Humidity Calibration Registers
BME_688_HUM_CALIB1_REG = const(0xE2)
BME_688_HUM_CALIB2_REG = const(0xE1)
BME_688_HUM_CALIB3_REG = const(0xE4)
BME_688_HUM_CALIB4_REG = const(0xE5)
BME_688_HUM_CALIB5_REG = const(0xE6)
BME_688_HUM_CALIB6_REG = const(0xE7)
BME_688_HUM_CALIB7_REG = const(0xE8)

# Gas Calibration Registers
BME_688_GAS_CALIB1_REG = const(0xED)
BME_688_GAS_CALIB2_REG = const(0xEB)
BME_688_GAS_CALIB3_REG = const(0xEE)
BME_688_GAS_HEAT_RANGE_REG = const(0x02)
BME_688_GAS_HEAT_VAL_REG = const(0x00)

# IIR Filter Settings
BME_688_IIR_FILTER_REG = const(0x75)
BME_688_IIR_FILTER_C0 = const(0x00)
BME_688_IIR_FILTER_C1 = const(0x01)
BME_688_IIR_FILTER_C3 = const(0x02)
BME_688_IIR_FILTER_C7 = const(0x03)
BME_688_IIR_FILTER_C15 = const(0x04)
BME_688_IIR_FILTER_C31 = const(0x05)
BME_688_IIR_FILTER_C63 = const(0x06)
BME_688_IIR_FILTER_C127 = const(0x07)

# Gas Measurement Status
BME_688_GAS_MEAS_STATUS_REG0 = const(0x2E)
BME_688_GAS_MEAS_STATUS_REG1 = const(0x2D)
BME_688_GAS_HEAT_STAB_MASK = const(0x10)
BME_688_GAS_VALID_REG_MASK = const(0x20)
BME_688_GAS_NEW_DATA_MASK = const(0x80)
BME_688_GAS_MEAS_MASK = const(0x40)
BME_688_MEAS_MASK = const(0x20)
BME_688_HEAT_RANGE_MASK = const(0x18)
BME_688_GAS_RANGE_REG_MASK = const(0x0F)
BME_688_GAS_MEAS_INDEX_MASK = const(0x0F)
BME_688_GAS_RANGE_VAL_MASK = const(0x0F)
BME_688_GAS_RUN = const(0x20)

# Gas Measurement States
BME_688_GAS_MEAS_FINISH = const(0x30)
BME_688_GAS_HEATING_INSUFFICIENT = const(0x10)
BME_688_GAS_RESULT_NOT_READY = const(0x00)
BME_688_GAS_PROFILE_START = const(0x00)
BME_688_HEAT_PLATE_MAX_TEMP = const(0x1A9)  # 425°C
BME_688_HEAT_PLATE_ULTRA_TEMP = const(0x258)  # 600°C

# Gas Wait Time Registers
BME_688_GAS_WAIT_PROFILE_REG = const(0x64)
BME_688_GAS_RES_HEAT_PROFILE_REG = const(0x5A)
BME_688_GAS_START_TEMP = const(0xC8)  # 200°C

# Gas Wait Time Multiplication Factors
BME_688_GAS_WAIT_MULFAC1 = const(0x00)
BME_688_GAS_WAIT_MULFAC2 = const(0x01)
BME_688_GAS_WAIT_MULFAC3 = const(0x02)
BME_688_GAS_WAIT_MULFAC4 = const(0x03)

# Predefined Gas Wait Times (in ms)
BME_688_GAS_WAIT_PROFILE1 = const(0x3C)  # 60ms
BME_688_GAS_WAIT_PROFILE2 = const(0x50)  # 80ms
BME_688_GAS_WAIT_PROFILE3 = const(0x64)  # 100ms
BME_688_GAS_WAIT_PROFILE4 = const(0x90)  # 144ms
BME_688_GAS_WAIT_PROFILE5 = const(0xC0)  # 192ms
BME_688_GAS_WAIT_PROFILE6 = const(0xD2)  # 210ms
BME_688_GAS_WAIT_PROFILE7 = const(0xE0)  # 224ms
BME_688_GAS_WAIT_PROFILE8 = const(0xF0)  # 240ms
BME_688_GAS_WAIT_PROFILE9 = const(0xFA)  # 250ms
BME_688_GAS_WAIT_PROFILE10 = const(0xFF)  # 255ms

# Predefined Heater Temperatures (in °C)
BME_688_GAS_HEAT_PROFILE1 = const(200)
BME_688_GAS_HEAT_PROFILE2 = const(220)
BME_688_GAS_HEAT_PROFILE3 = const(240)
BME_688_GAS_HEAT_PROFILE4 = const(260)
BME_688_GAS_HEAT_PROFILE5 = const(280)
BME_688_GAS_HEAT_PROFILE6 = const(300)
BME_688_GAS_HEAT_PROFILE7 = const(320)
BME_688_GAS_HEAT_PROFILE8 = const(340)
BME_688_GAS_HEAT_PROFILE9 = const(360)
BME_688_GAS_HEAT_PROFILE10 = const(380)

# Chip Identification
BME_688_CHIP_ID_REG = const(0xD0)
BME_688_CHIP_ID = const(0x61)

# Correction Factors
BME_688_GAS_CORRECTION = const(1.3801)
BME_688_GAS_CORRECTION_NIL = const(1.0)

# Error Messages
BME_688_CHECK_CONN_ERR = (
    "BME688 is disconnected. Check connections or make sure it is working."
)
BME_688_TEMP_CAL_EXCEPT = "Exception: Failed to read temperature calibration parameters"
BME_688_PRES_CAL_EXCEPT = "Exception: Failed to read pressure calibration parameters"
BME_688_HUM_CAL_EXCEPT = "Exception: Failed to read humidity calibration parameters"
BME_688_VALUE_INVALID = "Invalid value. Use a value within the range."
BME_688_READ_FAILURE = "Exception: Failed to read from BME688"
BME_688_GAS_MEAS_FAILURE = "Exception: Gas measurement incomplete.\nTemperature not achieved or heating might be too high for the provided wait time."
BME_688_TEMP_WARNING = "Warning: Higher temperatures will degrade the lifespan of the sensor. \nThis operation has been automatically denied for safety. \nIf you still wish to use high temperatures, call ignoreUnsafeTemperatureWarnings(false)\nIn safe mode, Temperature limit is 425°C. Bypassing this protection will raise the limit to 600°C."
BME_688_TEMP_EXCEED_MAX_LIMIT = (
    "Exception: Operation blocked. The temperature value exceeds maximum limit."
)
BME_688_PROFILE_OUT_OF_RANGE = (
    "Exception: Operation blocked. Profile value should be between 0 and 9."
)
BME_688_TEMP_UNSAFE_WARNING = "Warning: Higher temperatures will degrade the lifespan of the sensor. It is recommended to use a value under 425°C"
