# FILE: ak09918_constants.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: Register definitions, error codes, and operating modes for the AK09918 sensor
# LAST UPDATED: 2026-04-23

# I2C address
AK09918_I2C_ADDR = 0x0C

# Register addresses
AK09918_WIA1 = 0x00  # Company ID register
AK09918_WIA2 = 0x01  # Device ID register
AK09918_ST1 = 0x10  # Status register 1 (data ready / overrun)
AK09918_HXL = 0x11  # X-axis measurement low byte
AK09918_HXH = 0x12  # X-axis measurement high byte
AK09918_HYL = 0x13  # Y-axis measurement low byte
AK09918_HYH = 0x14  # Y-axis measurement high byte
AK09918_HZL = 0x15  # Z-axis measurement low byte
AK09918_HZH = 0x16  # Z-axis measurement high byte
AK09918_TMPS = 0x17  # Dummy register (must be read as part of 8-byte block)
AK09918_ST2 = 0x18  # Status register 2 (overflow flag)
AK09918_CNTL2 = 0x31  # Control register 2 (operating mode)
AK09918_CNTL3 = 0x32  # Control register 3 (soft reset)

# Status register bits
AK09918_DRDY_BIT = 0x01  # Data ready
AK09918_DOR_BIT = 0x02  # Data overrun
AK09918_HOFL_BIT = 0x08  # Hall sensor overflow
AK09918_SRST_BIT = 0x01  # Soft reset

# Error codes
AK09918_ERR_OK = 0
AK09918_ERR_DOR = 1
AK09918_ERR_NOT_RDY = 2
AK09918_ERR_TIMEOUT = 3
AK09918_ERR_SELFTEST_FAILED = 4
AK09918_ERR_OVERFLOW = 5
AK09918_ERR_WRITE_FAILED = 6
AK09918_ERR_READ_FAILED = 7

# Operating modes
AK09918_POWER_DOWN = 0x00  # Power-down mode
AK09918_NORMAL = 0x01  # Single measurement mode (auto power-down after each reading)
AK09918_CONT_MEASURE_MODE1 = 0x02  # Continuous measurement at 10 Hz
AK09918_CONT_MEASURE_MODE2 = 0x04  # Continuous measurement at 20 Hz
AK09918_CONT_MEASURE_MODE3 = 0x06  # Continuous measurement at 50 Hz
AK09918_CONT_MEASURE_MODE4 = 0x08  # Continuous measurement at 100 Hz
AK09918_SELF_TEST = 0x10  # Self-test mode
