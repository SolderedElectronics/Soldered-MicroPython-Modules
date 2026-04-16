# FILE: bhi385.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: A MicroPython module for the Bosch BHI385 Smart IMU sensor
# LAST UPDATED: 2026-04-15

import struct
import time
from machine import I2C, Pin
from os import uname

# ---------------------------------------------------------------------------
# I2C addresses (selected by HSDO pin)
# ---------------------------------------------------------------------------
BHI385_I2C_ADDR_LOW = 0x28  # HSDO = GND
BHI385_I2C_ADDR_HIGH = 0x29  # HSDO = VDDIO

# ---------------------------------------------------------------------------
# Channel registers (DMA channels for bulk transfer)
# ---------------------------------------------------------------------------
BHI385_CH_CMD = 0x00  # Host command input (write-only)
BHI385_CH_FIFO_WU = 0x01  # Wake-up FIFO output (read-only)
BHI385_CH_FIFO_NW = 0x02  # Non-wake-up FIFO output (read-only)
BHI385_CH_STATUS = 0x03  # Status and debug FIFO output (read-only)

# ---------------------------------------------------------------------------
# Configuration registers
# ---------------------------------------------------------------------------
BHI385_REG_CHIP_CTRL = 0x05
BHI385_REG_HOST_INTF_CTRL = 0x06
BHI385_REG_HOST_IRQ_CTRL = 0x07
BHI385_REG_RESET_REQ = 0x14
BHI385_REG_HOST_CTRL = 0x16
BHI385_REG_HOST_STATUS = 0x17

# ---------------------------------------------------------------------------
# Identity and status registers
# ---------------------------------------------------------------------------
BHI385_REG_FUSER2_ID = 0x1C  # Expected value: 0x89
BHI385_REG_FUSER2_REV = 0x1D  # 0x02 before firmware, 0x03 after
BHI385_REG_ROM_VER_L = 0x1E  # ROM version low byte  (0x2E)
BHI385_REG_ROM_VER_H = 0x1F  # ROM version high byte (0x14)
BHI385_REG_BOOT_STATUS = 0x25
BHI385_REG_CHIP_ID = 0x2B  # Expected value: 0x7C
BHI385_REG_INT_STATUS = 0x2D
BHI385_REG_ERROR_VAL = 0x2E

# ---------------------------------------------------------------------------
# Expected chip identity values
# ---------------------------------------------------------------------------
BHI385_CHIP_ID_VAL = 0x7C
BHI385_FUSER2_ID_VAL = 0x89

# ---------------------------------------------------------------------------
# Boot status register (0x25) bit masks
# ---------------------------------------------------------------------------
BHI385_BOOT_FLASH_DET = 0x01
BHI385_BOOT_FLASH_VER_DONE = 0x02
BHI385_BOOT_FLASH_VER_ERR = 0x04
BHI385_BOOT_NO_FLASH = 0x08
BHI385_BOOT_HOST_IFACE_RDY = 0x10  # Bootloader or firmware ready for host
BHI385_BOOT_FW_VER_DONE = 0x20  # RAM firmware CRC check passed
BHI385_BOOT_FW_VER_ERR = 0x40  # RAM firmware CRC check failed
BHI385_BOOT_FW_IDLE = 0x80

# ---------------------------------------------------------------------------
# Interrupt status register (0x2D) bit masks
# ---------------------------------------------------------------------------
BHI385_INT_ASSERTED = 0x01  # Interrupt is asserted
BHI385_INT_FIFO_WU = 0x02  # Wake-up FIFO data ready
BHI385_INT_FIFO_WU_LAT = 0x04  # Wake-up FIFO latency threshold reached
BHI385_INT_FIFO_NW = 0x08  # Non-wake-up FIFO data ready
BHI385_INT_FIFO_NW_LAT = 0x10  # Non-wake-up FIFO latency threshold reached
BHI385_INT_STATUS_DBG = 0x20  # Status / debug FIFO has data

# ---------------------------------------------------------------------------
# Host command IDs (written to channel 0x00)
# ---------------------------------------------------------------------------
BHI385_CMD_UPLOAD_FW = 0x0002
BHI385_CMD_BOOT_FW = 0x0003
BHI385_CMD_CONFIGURE_SENSOR = 0x000D
BHI385_CMD_CHANGE_RANGE = 0x000E

# ---------------------------------------------------------------------------
# Virtual sensor IDs
# ---------------------------------------------------------------------------
BHI385_SENSOR_ACCEL_PASSTHROUGH = 1
BHI385_SENSOR_ACCEL_RAW = 3  # Raw accelerometer (non-wake-up)
BHI385_SENSOR_ACCEL_CORRECTED = 4  # Corrected accelerometer (non-wake-up)
BHI385_SENSOR_GYRO_PASSTHROUGH = 10
BHI385_SENSOR_GYRO_RAW = 12  # Raw gyroscope (non-wake-up)
BHI385_SENSOR_GYRO_CORRECTED = 13  # Corrected gyroscope (non-wake-up)
BHI385_SENSOR_GAMERV = 37  # Game rotation vector (non-wake-up)
BHI385_SENSOR_STC = 52  # Step counter (non-wake-up)
BHI385_SENSOR_STC_LP = 136  # Step counter Low Power — used by bsxsam_lite firmware
BHI385_SENSOR_MULTI_TAP = 153  # Multi-tap detect (wake-up)
BHI385_SENSOR_WRIST_GEST = 156  # Wrist gesture detect Low Power (wake-up)
BHI385_SENSOR_WRIST_WEAR = 158  # Wrist wear wakeup (wake-up)

# Parameter page command ID for multi-tap enable configuration
BHI385_PARAM_MULTI_TAP_ENABLE = 0x0D01

# Physical sensor control parameter page for wrist gesture detect
# = 0xE00 | physical_sensor_id (56)
BHI385_PARAM_WRIST_GEST_PHY = 0x0E38

# HOST_INTERFACE_CTRL register (0x06) bit masks
BHI385_HIF_CTRL_ASYNC_STATUS = 0x80

# ---------------------------------------------------------------------------
# FIFO system event IDs
# Total size = 1 (ID byte) + payload bytes shown in comment
# ---------------------------------------------------------------------------
BHI385_FIFO_PAD = 0x00  # Padding (1 byte total)
BHI385_FIFO_TS_SMALL_DLT_WU = 0xF5  # WU small delta timestamp  (2 bytes total)
BHI385_FIFO_TS_LARGE_DLT_WU = 0xF6  # WU large delta timestamp  (3 bytes total)
BHI385_FIFO_TS_FULL_WU = 0xF7  # WU full timestamp         (6 bytes total)
BHI385_FIFO_META_WU = 0xF8  # WU meta event             (4 bytes total)
BHI385_FIFO_DEBUG_MSG = 0xFA  # Debug message             (18 bytes total)
BHI385_FIFO_TS_SMALL_DLT = 0xFB  # NW small delta timestamp  (2 bytes total)
BHI385_FIFO_TS_LARGE_DLT = 0xFC  # NW large delta timestamp  (3 bytes total)
BHI385_FIFO_TS_FULL = 0xFD  # NW full timestamp         (6 bytes total)
BHI385_FIFO_META = 0xFE  # NW meta event             (4 bytes total)
BHI385_FIFO_FILLER = 0xFF  # Filler byte               (1 byte total)

# ---------------------------------------------------------------------------
# Accelerometer sensitivity in LSB/g per dynamic range setting
# ---------------------------------------------------------------------------
BHI385_ACCEL_SENS_4G = 8192.0
BHI385_ACCEL_SENS_8G = 4096.0
BHI385_ACCEL_SENS_16G = 2048.0
BHI385_ACCEL_SENS_32G = 1024.0

# ---------------------------------------------------------------------------
# Gyroscope sensitivity in LSB/(deg/s) per full-scale range setting
# ---------------------------------------------------------------------------
BHI385_GYRO_SENS_125DPS = 262.144
BHI385_GYRO_SENS_250DPS = 131.072
BHI385_GYRO_SENS_500DPS = 65.536
BHI385_GYRO_SENS_1000DPS = 32.768
BHI385_GYRO_SENS_2000DPS = 16.384

# ---------------------------------------------------------------------------
# Timing constants (from datasheet)
# ---------------------------------------------------------------------------
BHI385_T_BOOT_BL_MS = 5  # Bootloader ready timeout (max 1.3 ms, use 5 ms)
BHI385_T_BOOT_FW_MS = 500  # Firmware boot timeout (typical 81 ms)
BHI385_T_FW_VER_MS = 5000  # Firmware CRC verify timeout (conservative)

# ---------------------------------------------------------------------------
# Buffer and chunk sizes
# ---------------------------------------------------------------------------
BHI385_FIFO_BUF_SIZE = 256  # Maximum FIFO read buffer
BHI385_I2C_CHUNK_SIZE = 28  # Max data bytes per I2C write (Wire buffer safe limit)

# ---------------------------------------------------------------------------
# Accelerometer dynamic range options (in g)
# ---------------------------------------------------------------------------
BHI385_ACCEL_4G = 4
BHI385_ACCEL_8G = 8
BHI385_ACCEL_16G = 16
BHI385_ACCEL_32G = 32

# ---------------------------------------------------------------------------
# Gyroscope full-scale range options (in deg/s)
# ---------------------------------------------------------------------------
BHI385_GYRO_125DPS = 125
BHI385_GYRO_250DPS = 250
BHI385_GYRO_500DPS = 500
BHI385_GYRO_1000DPS = 1000
BHI385_GYRO_2000DPS = 2000

# ---------------------------------------------------------------------------
# Wrist gesture identifiers
# ---------------------------------------------------------------------------
BHI385_WRIST_GEST_NONE = 0  # No gesture / unknown
BHI385_WRIST_GEST_SHAKE_JIGGLE = 3  # Wrist shake / jiggle
BHI385_WRIST_GEST_FLICK_IN = 4  # Arm flick in
BHI385_WRIST_GEST_FLICK_OUT = 5  # Arm flick out

# ---------------------------------------------------------------------------
# Tap type bitmask values
# As an event value: which tap was detected (one bit set at a time).
# As a config mask: OR together tap types to detect.
# ---------------------------------------------------------------------------
BHI385_TAP_NONE = 0  # No tap
BHI385_TAP_SINGLE = 1  # Single tap
BHI385_TAP_DOUBLE = 2  # Double tap
BHI385_TAP_DOUBLE_SINGLE = 3  # Double and single tap
BHI385_TAP_TRIPLE = 4  # Triple tap
BHI385_TAP_TRIPLE_SINGLE = 5  # Triple and single tap
BHI385_TAP_TRIPLE_DOUBLE = 6  # Triple and double tap
BHI385_TAP_ALL = 7  # All tap types enabled

# ---------------------------------------------------------------------------
# Wrist hand options
# ---------------------------------------------------------------------------
BHI385_WRIST_LEFT = 0  # Device worn on the left wrist (firmware default)
BHI385_WRIST_RIGHT = 1  # Device worn on the right wrist


class BHI385:
    """
    MicroPython class for the Bosch BHI385 Smart IMU sensor.
    Supports accelerometer, gyroscope, game rotation vector,
    step counter, wrist gesture detection, and multi-tap detection.

    The BHI385 requires a firmware binary to be uploaded from the host
    on every power-on. Call loadFirmware() after begin() before enabling
    any virtual sensors. Firmware must be obtained from Bosch Sensortec.
    """

    def __init__(self, i2c=None, address=BHI385_I2C_ADDR_LOW):
        """
        Initialize the BHI385 sensor.

        :param i2c: Initialized I2C object
        :param address: I2C address of the sensor (default BHI385_I2C_ADDR_LOW = 0x28)
        """
        if i2c is not None:
            self._i2c = i2c
        else:
            if uname().sysname in ("esp32", "esp8266", "Soldered Dasduino CONNECTPLUS"):
                self._i2c = I2C(0, scl=Pin(22), sda=Pin(21))
            else:
                raise Exception("Board not recognized, enter I2C pins manually")

        self._addr = address
        self._dbg = False
        self._initialized = False

        # Sensor data: accelerometer [x, y, z] in g
        self._accel = [0.0, 0.0, 0.0]
        # Sensor data: gyroscope [x, y, z] in deg/s
        self._gyro = [0.0, 0.0, 0.0]
        # Sensor data: quaternion [x, y, z, w, accuracyDeg]
        self._quat = [0.0, 0.0, 0.0, 1.0, 0.0]
        self._step_count = 0
        self._wrist_gesture = 0
        self._tap_type = 0

        # Updated flags — set by update(), cleared by clearUpdatedFlags()
        self._accel_updated = False
        self._gyro_updated = False
        self._quat_updated = False
        self._step_updated = False
        self._wrist_gesture_updated = False
        self._tap_updated = False

        # Active virtual sensor IDs
        self._accel_sensor_id = BHI385_SENSOR_ACCEL_CORRECTED
        self._gyro_sensor_id = BHI385_SENSOR_GYRO_CORRECTED
        self._quat_sensor_id = BHI385_SENSOR_GAMERV
        self._stc_sensor_id = BHI385_SENSOR_STC_LP
        self._wrist_gest_sensor_id = BHI385_SENSOR_WRIST_GEST
        self._tap_sensor_id = BHI385_SENSOR_MULTI_TAP

        # Sensitivity divisors (set when enabling each sensor)
        self._accel_sens = BHI385_ACCEL_SENS_8G
        self._gyro_sens = BHI385_GYRO_SENS_2000DPS

    def begin(self, address=None):
        """
        Initialize the BHI385 host interface.
        Issues a soft reset, waits for the bootloader, and verifies the chip ID.
        Call loadFirmware() after this.

        :param address: Optional I2C address override
        :return: True if host interface is ready and chip identity matches
        """
        if address is not None:
            self._addr = address

        # Issue a host software reset equivalent to power-on reset
        self._i2c_write_reg(BHI385_REG_RESET_REQ, 0x01)
        time.sleep_ms(10)

        # Configure host interface control: clear all bits including AP_SUSPENDED
        self._i2c_write_reg(BHI385_REG_HOST_INTF_CTRL, 0x00)

        # Configure interrupt: active-high, push-pull, level-triggered (polling mode)
        self._i2c_write_reg(BHI385_REG_HOST_IRQ_CTRL, 0x00)

        # Poll for bootloader ready (bit 4 of boot status, max hardware time 1.3 ms)
        if not self._poll_boot_status(BHI385_BOOT_HOST_IFACE_RDY, BHI385_T_BOOT_BL_MS):
            if self._dbg:
                print("[BHI385] begin: FAILED: bootloader not ready")
            return False

        if self._dbg:
            fuser2_id = self._i2c_read_reg(BHI385_REG_FUSER2_ID, 1)
            fuser2_rev = self._i2c_read_reg(BHI385_REG_FUSER2_REV, 1)
            rom_ver_l = self._i2c_read_reg(BHI385_REG_ROM_VER_L, 1)
            rom_ver_h = self._i2c_read_reg(BHI385_REG_ROM_VER_H, 1)
            print("[BHI385] Chip ID:    0x{:02X}".format(self.getChipId()))
            if fuser2_id:
                print("[BHI385] Fuser2 ID:  0x{:02X}".format(fuser2_id[0]))
            if fuser2_rev:
                print("[BHI385] Fuser2 Rev: 0x{:02X}".format(fuser2_rev[0]))
            if rom_ver_h and rom_ver_l:
                print(
                    "[BHI385] ROM version: 0x{:02X}{:02X}".format(
                        rom_ver_h[0], rom_ver_l[0]
                    )
                )

        if self.getChipId() != BHI385_CHIP_ID_VAL:
            if self._dbg:
                print(
                    "[BHI385] begin: FAILED: chip ID mismatch (got 0x{:02X}, expected 0x{:02X})".format(
                        self.getChipId(), BHI385_CHIP_ID_VAL
                    )
                )
            return False

        self._initialized = True
        return True

    def loadFirmware(self, firmware):
        """
        Upload firmware to the BHI385 program RAM and boot it.
        Must be called after begin() and before enabling any sensors.
        The firmware binary must be obtained from Bosch Sensortec.

        :param firmware: Firmware binary as bytes or bytearray
        :return: True if firmware loaded and booted successfully
        """
        if not self._initialized:
            if self._dbg:
                print("[BHI385] loadFirmware: FAILED: begin() was not successful")
            return False

        if not firmware or len(firmware) == 0:
            if self._dbg:
                print("[BHI385] loadFirmware: FAILED: empty firmware")
            return False

        fw_len = len(firmware)

        if self._dbg:
            print("[BHI385] loadFirmware: firmware size = {} bytes".format(fw_len))
            print(
                "[BHI385] loadFirmware: boot status before upload = 0x{:02X}".format(
                    self.getBootStatus()
                )
            )

        # Step 1: send the 4-byte "Upload to Program RAM" command header.
        # Format: [CMD_ID_L][CMD_ID_H][WORD_COUNT_L][WORD_COUNT_H]
        # WORD_COUNT = ceil(fw_len / 4) — firmware size in 32-bit words, not bytes.
        fw_len_rounded = (fw_len + 3) & ~3
        word_count = fw_len_rounded // 4
        header = bytes(
            [
                BHI385_CMD_UPLOAD_FW & 0xFF,
                (BHI385_CMD_UPLOAD_FW >> 8) & 0xFF,
                word_count & 0xFF,
                (word_count >> 8) & 0xFF,
            ]
        )

        if self._dbg:
            fw_preview = " ".join("{:02X}".format(b) for b in firmware[:32])
            print(
                "[BHI385] loadFirmware: firmware first 32 bytes: {}".format(fw_preview)
            )
            print(
                "[BHI385] loadFirmware: word count = {} ({} bytes rounded)".format(
                    word_count, fw_len_rounded
                )
            )
            print(
                "[BHI385] loadFirmware: [1/5] writing upload command header... ", end=""
            )

        if not self._channel_write(BHI385_CH_CMD, header):
            if self._dbg:
                print("FAILED")
            return False

        if self._dbg:
            print("OK")

        # Step 2: upload firmware data in BHI385_I2C_CHUNK_SIZE-byte chunks.
        # Each chunk is a separate I2C transaction: [CH_CMD][data...].
        # A 500 µs pause between chunks lets the BHI385 internal DMA drain its
        # receive buffer before the next transaction arrives.
        if self._dbg:
            num_chunks = fw_len // BHI385_I2C_CHUNK_SIZE + 1
            print(
                "[BHI385] loadFirmware: [2/5] uploading {} chunks @ {} bytes each...".format(
                    num_chunks, BHI385_I2C_CHUNK_SIZE
                )
            )

        offset = 0
        report_step = max(fw_len // 10, 1)
        next_report = report_step

        while offset < fw_len:
            chunk = min(fw_len - offset, BHI385_I2C_CHUNK_SIZE)
            try:
                self._i2c.writeto_mem(
                    self._addr, BHI385_CH_CMD, firmware[offset : offset + chunk]
                )
            except OSError as e:
                if self._dbg:
                    print(
                        "[BHI385] loadFirmware: [2/5] FAILED at offset {}/{} ({})".format(
                            offset, fw_len, e
                        )
                    )
                return False

            time.sleep_us(500)
            offset += chunk

            if self._dbg and offset >= next_report:
                print(
                    "[BHI385] loadFirmware: [2/5]   {}% ({}/{} bytes)".format(
                        (offset * 100) // fw_len, offset, fw_len
                    )
                )
                next_report += report_step

        if self._dbg:
            print("[BHI385] loadFirmware: [2/5] upload complete")
            err_now = self._i2c_read_reg(BHI385_REG_ERROR_VAL, 1)
            print(
                "[BHI385] loadFirmware: [2/5] post-upload boot status = 0x{:02X}, "
                "error = 0x{:02X}".format(
                    self.getBootStatus(), err_now[0] if err_now else 0
                )
            )

        # Step 3: wait for CRC verify result.
        # Bit 5 (FW_VER_DONE) or bit 6 (FW_VER_ERR) will be set when the ROM
        # bootloader finishes checking the uploaded image.
        if self._dbg:
            print(
                "[BHI385] loadFirmware: [3/5] waiting for CRC verify "
                "(timeout {} ms)...".format(BHI385_T_FW_VER_MS)
            )

        if not self._poll_boot_status(
            BHI385_BOOT_FW_VER_DONE | BHI385_BOOT_FW_VER_ERR, BHI385_T_FW_VER_MS
        ):
            if self._dbg:
                print(
                    "[BHI385] loadFirmware: [3/5] TIMEOUT, "
                    "boot status = 0x{:02X}".format(self.getBootStatus())
                )
            return False

        boot_st = self.getBootStatus()
        if self._dbg:
            print(
                "[BHI385] loadFirmware: [3/5] boot status after verify = "
                "0x{:02X}".format(boot_st)
            )

        if boot_st & BHI385_BOOT_FW_VER_ERR:
            if self._dbg:
                err_val = self._i2c_read_reg(BHI385_REG_ERROR_VAL, 1)
                print(
                    "[BHI385] loadFirmware: [3/5] FAILED: CRC mismatch, "
                    "error = 0x{:02X}".format(err_val[0] if err_val else 0)
                )
            return False

        if self._dbg:
            print("[BHI385] loadFirmware: [3/5] CRC OK")

        # Step 4: send the "Boot Program RAM" command.
        boot_cmd = bytes(
            [
                BHI385_CMD_BOOT_FW & 0xFF,
                (BHI385_CMD_BOOT_FW >> 8) & 0xFF,
                0x00,
                0x00,
            ]
        )

        if self._dbg:
            print("[BHI385] loadFirmware: [4/5] sending boot command... ", end="")

        if not self._channel_write(BHI385_CH_CMD, boot_cmd):
            if self._dbg:
                print("FAILED")
            return False

        if self._dbg:
            print("OK")

        # Step 5: wait for firmware to boot and host interface to become ready.
        if self._dbg:
            print(
                "[BHI385] loadFirmware: [5/5] waiting for firmware boot "
                "(timeout {} ms)...".format(BHI385_T_BOOT_FW_MS)
            )

        time.sleep_ms(85)  # Typical firmware boot time is 81 ms

        if not self._poll_boot_status(BHI385_BOOT_HOST_IFACE_RDY, BHI385_T_BOOT_FW_MS):
            if self._dbg:
                print(
                    "[BHI385] loadFirmware: [5/5] TIMEOUT, "
                    "boot status = 0x{:02X}".format(self.getBootStatus())
                )
            return False

        if self._dbg:
            print(
                "[BHI385] loadFirmware: [5/5] firmware booted. "
                "Boot status = 0x{:02X}".format(self.getBootStatus())
            )

        # Clear HOST_INTERFACE_CTRL (0x06) to release AP_SUSPENDED. While
        # AP_SUSPENDED is set the firmware buffers all sensor events internally
        # and does not flush them to the FIFO channels.
        self._i2c_write_reg(BHI385_REG_HOST_INTF_CTRL, 0x00)

        # Flush FIFOs to discard the initial boot interrupt
        self._channel_read(BHI385_CH_FIFO_WU)
        self._channel_read(BHI385_CH_FIFO_NW)
        self._channel_read(BHI385_CH_STATUS)

        if self._dbg:
            print("[BHI385] loadFirmware: SUCCESS")
        return True

    def enableAccelerometer(self, rateHz=100.0, range=BHI385_ACCEL_8G):
        """
        Enable the accelerometer virtual sensor.

        :param rateHz: Output data rate in Hz (default 100.0)
        :param range: Dynamic range — BHI385_ACCEL_4G / 8G / 16G / 32G (default BHI385_ACCEL_8G)
        :return: True on success
        """
        self._accel_sensor_id = BHI385_SENSOR_ACCEL_CORRECTED
        self._accel_sens = self._accel_range_to_sensitivity(range)
        return self._configure_sensor(self._accel_sensor_id, rateHz)

    def enableGyroscope(self, rateHz=100.0, range=BHI385_GYRO_2000DPS):
        """
        Enable the gyroscope virtual sensor.

        :param rateHz: Output data rate in Hz (default 100.0)
        :param range: Full-scale range — BHI385_GYRO_125DPS through 2000DPS
                      (default BHI385_GYRO_2000DPS)
        :return: True on success
        """
        self._gyro_sensor_id = BHI385_SENSOR_GYRO_CORRECTED
        self._gyro_sens = self._gyro_range_to_sensitivity(range)
        return self._configure_sensor(self._gyro_sensor_id, rateHz)

    def enableGameRotationVector(self, rateHz=100.0):
        """
        Enable the Game Rotation Vector virtual sensor.
        Outputs a normalized quaternion fused from accel + gyro.
        Does not use a magnetometer so yaw is relative to power-on orientation.

        :param rateHz: Output data rate in Hz (default 100.0)
        :return: True on success
        """
        self._quat_sensor_id = BHI385_SENSOR_GAMERV
        return self._configure_sensor(self._quat_sensor_id, rateHz)

    def enableStepCounter(self, rateHz=100.0):
        """
        Enable the step counter virtual sensor.
        Reports the cumulative step count since the sensor was last reset.

        :param rateHz: Update rate in Hz (default 100.0; 1.0 Hz is typical for step counting)
        :return: True on success
        """
        self._stc_sensor_id = BHI385_SENSOR_STC_LP
        return self._configure_sensor(self._stc_sensor_id, rateHz)

    def enableWristGestureDetect(self, rateHz=100.0, hand=BHI385_WRIST_LEFT):
        """
        Enable the wrist gesture detect sensor (wake-up).
        Detects wrist shake/jiggle and arm flick in/out.
        Requires the bsxsam_lite_Klio_cyclic firmware variant.

        :param rateHz: Output rate in Hz (default 100.0)
        :param hand: Which wrist — BHI385_WRIST_LEFT (default) or BHI385_WRIST_RIGHT
        :return: True on success
        """
        self._wrist_gest_sensor_id = BHI385_SENSOR_WRIST_GEST

        if hand != BHI385_WRIST_LEFT:
            if not self._set_wrist_gesture_phys_param(hand):
                if self._dbg:
                    print("[BHI385] enableWristGestureDetect: hand config failed")
                return False

        return self._configure_sensor(self._wrist_gest_sensor_id, rateHz)

    def enableMultiTapDetect(self, tapMask=BHI385_TAP_ALL, rateHz=100.0):
        """
        Enable the multi-tap detect virtual sensor (wake-up).
        Reports single, double, and/or triple taps depending on tapMask.

        :param tapMask: Bitmask of tap types to detect — OR together BHI385_TAP_* values
                        (default BHI385_TAP_ALL)
        :param rateHz: Sensor update rate in Hz (default 100.0)
        :return: True on success
        """
        self._tap_sensor_id = BHI385_SENSOR_MULTI_TAP

        # Write tap-enable configuration to the multi-tap parameter page.
        # Payload is 4 bytes (padded from 1): [tapMask][0][0][0]
        cfg = bytes([tapMask, 0, 0, 0])
        if not self._send_command(BHI385_PARAM_MULTI_TAP_ENABLE, cfg):
            return False

        return self._configure_sensor(self._tap_sensor_id, rateHz)

    def disableAccelerometer(self):
        """
        Disable the accelerometer virtual sensor.

        :return: True on success
        """
        return self._configure_sensor(self._accel_sensor_id, 0.0)

    def disableGyroscope(self):
        """
        Disable the gyroscope virtual sensor.

        :return: True on success
        """
        return self._configure_sensor(self._gyro_sensor_id, 0.0)

    def disableGameRotationVector(self):
        """
        Disable the Game Rotation Vector sensor.

        :return: True on success
        """
        return self._configure_sensor(self._quat_sensor_id, 0.0)

    def disableStepCounter(self):
        """
        Disable the step counter sensor.

        :return: True on success
        """
        return self._configure_sensor(self._stc_sensor_id, 0.0)

    def disableWristGestureDetect(self):
        """
        Disable the wrist gesture detect sensor.

        :return: True on success
        """
        return self._configure_sensor(self._wrist_gest_sensor_id, 0.0)

    def disableMultiTapDetect(self):
        """
        Disable the multi-tap detect sensor.

        :return: True on success
        """
        return self._configure_sensor(self._tap_sensor_id, 0.0)

    def update(self):
        """
        Read and parse all pending FIFO data.
        Call this regularly in your main loop or from an interrupt handler.
        After calling, check accelUpdated() / gyroUpdated() etc. and read the data.

        :return: True (always; indicates the function ran)
        """
        self._accel_updated = False
        self._gyro_updated = False
        self._quat_updated = False
        self._step_updated = False
        self._wrist_gesture_updated = False
        self._tap_updated = False

        self._read_and_parse_fifo(BHI385_CH_FIFO_WU)
        self._read_and_parse_fifo(BHI385_CH_FIFO_NW)

        # Drain STATUS FIFO to prevent it from filling up
        self._channel_read(BHI385_CH_STATUS)

        return True

    # ---------------------------------------------------------------------------
    # Data accessors
    # ---------------------------------------------------------------------------

    def getAccelX(self):
        """Return last accelerometer X reading in g."""
        return self._accel[0]

    def getAccelY(self):
        """Return last accelerometer Y reading in g."""
        return self._accel[1]

    def getAccelZ(self):
        """Return last accelerometer Z reading in g."""
        return self._accel[2]

    def getAccelData(self):
        """Return last accelerometer reading as (x, y, z) tuple in g."""
        return (self._accel[0], self._accel[1], self._accel[2])

    def getGyroX(self):
        """Return last gyroscope X reading in deg/s."""
        return self._gyro[0]

    def getGyroY(self):
        """Return last gyroscope Y reading in deg/s."""
        return self._gyro[1]

    def getGyroZ(self):
        """Return last gyroscope Z reading in deg/s."""
        return self._gyro[2]

    def getGyroData(self):
        """Return last gyroscope reading as (x, y, z) tuple in deg/s."""
        return (self._gyro[0], self._gyro[1], self._gyro[2])

    def getQuatX(self):
        """Return last quaternion X component (range -1 to +1)."""
        return self._quat[0]

    def getQuatY(self):
        """Return last quaternion Y component (range -1 to +1)."""
        return self._quat[1]

    def getQuatZ(self):
        """Return last quaternion Z component (range -1 to +1)."""
        return self._quat[2]

    def getQuatW(self):
        """Return last quaternion W component (range -1 to +1)."""
        return self._quat[3]

    def getQuatAccuracyDeg(self):
        """Return estimated heading accuracy in degrees."""
        return self._quat[4]

    def getQuatData(self):
        """Return last quaternion reading as (x, y, z, w, accuracyDeg) tuple."""
        return (
            self._quat[0],
            self._quat[1],
            self._quat[2],
            self._quat[3],
            self._quat[4],
        )

    def getStepCount(self):
        """Return cumulative step count."""
        return self._step_count

    def getWristGesture(self):
        """Return last detected wrist gesture (see BHI385_WRIST_GEST_* constants)."""
        return self._wrist_gesture

    def getTapType(self):
        """Return last detected tap type (see BHI385_TAP_* constants)."""
        return self._tap_type

    # ---------------------------------------------------------------------------
    # Updated flags
    # ---------------------------------------------------------------------------

    def accelUpdated(self):
        """Returns True if accelerometer data was refreshed in the last update() call."""
        return self._accel_updated

    def gyroUpdated(self):
        """Returns True if gyroscope data was refreshed in the last update() call."""
        return self._gyro_updated

    def quatUpdated(self):
        """Returns True if quaternion data was refreshed in the last update() call."""
        return self._quat_updated

    def stepUpdated(self):
        """Returns True if step count was updated in the last update() call."""
        return self._step_updated

    def wristGestureUpdated(self):
        """Returns True if a new wrist gesture was detected in the last update() call."""
        return self._wrist_gesture_updated

    def tapUpdated(self):
        """Returns True if a tap was detected in the last update() call."""
        return self._tap_updated

    def clearUpdatedFlags(self):
        """Clear all updated flags. Call after processing data from update()."""
        self._accel_updated = False
        self._gyro_updated = False
        self._quat_updated = False
        self._step_updated = False
        self._wrist_gesture_updated = False
        self._tap_updated = False

    # ---------------------------------------------------------------------------
    # Status
    # ---------------------------------------------------------------------------

    def getBootStatus(self):
        """
        Read the boot status register (0x25).

        :return: Raw boot status byte
        """
        data = self._i2c_read_reg(BHI385_REG_BOOT_STATUS, 1)
        return data[0] if data else 0

    def getChipId(self):
        """
        Read the chip ID register (0x2B). Should return 0x7C.

        :return: Chip ID byte
        """
        data = self._i2c_read_reg(BHI385_REG_CHIP_ID, 1)
        return data[0] if data else 0

    def isReady(self):
        """Returns True if begin() succeeded and chip identity was verified."""
        return self._initialized

    def enableDebug(self):
        """Enable verbose debug output via print(). Call before loadFirmware() to see
        step-by-step progress."""
        self._dbg = True

    def disableDebug(self):
        """Disable verbose debug output."""
        self._dbg = False

    # ---------------------------------------------------------------------------
    # Private: Low-level I2C
    # ---------------------------------------------------------------------------

    def _i2c_write_reg(self, reg, val):
        """Write a single byte to a configuration register."""
        try:
            self._i2c.writeto_mem(self._addr, reg, bytes([val]))
            return True
        except OSError as e:
            if self._dbg:
                print("[BHI385] I2C write failed reg 0x{:02X}: {}".format(reg, e))
            return False

    def _i2c_read_reg(self, reg, length=1):
        """Read one or more bytes from a configuration register."""
        try:
            return self._i2c.readfrom_mem(self._addr, reg, length)
        except OSError as e:
            if self._dbg:
                print("[BHI385] I2C read failed reg 0x{:02X}: {}".format(reg, e))
            return None

    def _channel_write(self, channel, data):
        """
        Write data to a BHI385 channel register in BHI385_I2C_CHUNK_SIZE-byte chunks.
        Each I2C transaction: START + [channel][data_chunk] + STOP.
        The BHI385 channel maintains its write pointer across separate transactions.

        :param channel: Channel register (e.g. BHI385_CH_CMD)
        :param data: bytes or bytearray to write
        :return: True on success
        """
        offset = 0
        length = len(data)
        while offset < length:
            chunk = min(length - offset, BHI385_I2C_CHUNK_SIZE)
            try:
                self._i2c.writeto_mem(
                    self._addr, channel, data[offset : offset + chunk]
                )
            except OSError as e:
                if self._dbg:
                    print(
                        "[BHI385] channel write failed ch 0x{:02X}: {}".format(
                            channel, e
                        )
                    )
                return False
            offset += chunk
        return True

    def _channel_read(self, channel, max_len=BHI385_FIFO_BUF_SIZE):
        """
        Read data from a BHI385 channel register.

        Uses a repeated START (no STOP between the address write and the data read)
        as required by the BHI385. Sending a STOP first causes the device to reset
        its internal read pointer, making the 2-byte length header come back as 0x0000.

        Protocol:
          1. Write [channel] without STOP
          2. Read 2-byte length header (little-endian, includes STOP)
          3. For each 32-byte chunk: write [channel] without STOP, then read chunk

        :param channel: Channel register (e.g. BHI385_CH_FIFO_NW)
        :param max_len: Maximum bytes to return (capped at BHI385_FIFO_BUF_SIZE)
        :return: bytes of FIFO payload (length header stripped), or b'' on failure
        """
        try:
            # Write channel address without STOP → repeated START before the read
            self._i2c.writeto(self._addr, bytes([channel]), False)
            # Read 2-byte transfer-length header
            header = self._i2c.readfrom(self._addr, 2)
        except OSError:
            return b""

        data_len = header[0] | (header[1] << 8)
        if data_len == 0:
            return b""

        to_read = min(data_len, max_len)
        result = bytearray()
        offset = 0

        while offset < to_read:
            chunk = min(to_read - offset, 32)
            try:
                self._i2c.writeto(self._addr, bytes([channel]), False)
                chunk_data = self._i2c.readfrom(self._addr, chunk)
                result.extend(chunk_data)
            except OSError:
                break
            offset += chunk

        return bytes(result)

    # ---------------------------------------------------------------------------
    # Private: Command helpers
    # ---------------------------------------------------------------------------

    def _send_command(self, cmd_id, params=None):
        """
        Write a generic command packet to channel 0 (BHI385_CH_CMD).
        Format: [CMD_ID_L][CMD_ID_H][PADDED_LEN_L][PADDED_LEN_H][PARAMS...]
        padded to a 4-byte boundary with 0x00 bytes.

        :param cmd_id: Command identifier (uint16)
        :param params: Parameter bytes or bytearray (optional)
        :return: True on success
        """
        if params is None:
            params = b""

        param_len = len(params)
        padded_param_len = (param_len + 3) & ~3
        total_len = 4 + padded_param_len

        pkt = bytearray(total_len)
        pkt[0] = cmd_id & 0xFF
        pkt[1] = (cmd_id >> 8) & 0xFF
        pkt[2] = padded_param_len & 0xFF
        pkt[3] = (padded_param_len >> 8) & 0xFF
        pkt[4 : 4 + param_len] = params

        return self._channel_write(BHI385_CH_CMD, pkt)

    def _configure_sensor(self, sensor_id, rate_hz, latency_ms=0):
        """
        Send a Configure Sensor command (0x000D).
        8 parameter bytes: [sensor_id (1)] [rate_hz IEEE-754 LE (4)] [latency_ms 24-bit LE (3)]

        :param sensor_id: Virtual sensor ID
        :param rate_hz: Desired output rate in Hz (0.0 = disable)
        :param latency_ms: Maximum report latency in milliseconds (default 0)
        :return: True on success
        """
        rate_bytes = struct.pack("<f", rate_hz)
        params = (
            bytes([sensor_id])
            + rate_bytes
            + bytes(
                [
                    latency_ms & 0xFF,
                    (latency_ms >> 8) & 0xFF,
                    (latency_ms >> 16) & 0xFF,
                ]
            )
        )
        return self._send_command(BHI385_CMD_CONFIGURE_SENSOR, params)

    def _change_sensor_range(self, sensor_id, range_val):
        """
        Send a Change Sensor Dynamic Range command (0x000E).
        For accelerometers: range_val in g (4, 8, 16, 32).
        For gyroscopes: range_val in deg/s (125, 250, 500, 1000, 2000).

        :param sensor_id: Virtual sensor ID
        :param range_val: Full-scale range value
        :return: True on success
        """
        params = bytes([sensor_id, range_val & 0xFF, (range_val >> 8) & 0xFF])
        return self._send_command(BHI385_CMD_CHANGE_RANGE, params)

    # ---------------------------------------------------------------------------
    # Private: Physical sensor parameter access
    # ---------------------------------------------------------------------------

    def _set_wrist_gesture_phys_param(self, hand):
        """
        Read the wrist gesture physical sensor control parameters, update the
        device_pos (hand) field, and write them back.

        Protocol (per Bosch SensorAPI bhi385_phy_sensor_ctrl_param.c):
          1. Switch STATUS channel to sync mode (clear ASYNC_STATUS_CHANNEL bit).
          2. Send read-request command 0x0E38 with payload [0x87, 0, 0, 0].
          3. Send get-parameter command 0x1E38 (= 0x0E38 | 0x1000), no payload.
          4. Poll INT_STATUS bit 5 for STATUS FIFO ready.
          5. Read 25 bytes from STATUS channel:
             [code_L][code_H][remain_L][remain_H][ctrl=0x07][config[0..19]]
          6. Set config[18] (device_pos) to the requested hand value.
          7. Write back via command 0x0E38 with 21-byte payload.
          8. Restore HOST_INTF_CTRL.

        :param hand: 0 = left arm, 1 = right arm
        :return: True on success
        """
        # Save HOST_INTF_CTRL and clear ASYNC_STATUS_CHANNEL (bit 7) so the STATUS
        # channel operates in synchronous parameter-response mode
        hif_ctrl_data = self._i2c_read_reg(BHI385_REG_HOST_INTF_CTRL, 1)
        hif_ctrl_saved = hif_ctrl_data[0] if hif_ctrl_data else 0
        self._i2c_write_reg(
            BHI385_REG_HOST_INTF_CTRL, hif_ctrl_saved & ~BHI385_HIF_CTRL_ASYNC_STATUS
        )

        # Send read-request: cmd=0x0E38, 4-byte payload = [ctrl_read=0x87, 0, 0, 0]
        read_req = bytes([0x38, 0x0E, 0x04, 0x00, 0x87, 0x00, 0x00, 0x00])
        self._channel_write(BHI385_CH_CMD, read_req)

        # Send get-parameter: cmd = 0x0E38 | 0x1000 = 0x1E38, no payload
        get_param = bytes([0x38, 0x1E, 0x00, 0x00])
        self._channel_write(BHI385_CH_CMD, get_param)

        # Wait for STATUS FIFO ready (INT_STATUS bit 5)
        status_ready = False
        t_start = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), t_start) < 200:
            int_st = self._i2c_read_reg(BHI385_REG_INT_STATUS, 1)
            if int_st and (int_st[0] & BHI385_INT_STATUS_DBG):
                status_ready = True
                break
            time.sleep_ms(1)

        success = False
        if status_ready:
            # Read 25-byte sync response from STATUS channel with repeated START
            try:
                self._i2c.writeto(self._addr, bytes([BHI385_CH_STATUS]), False)
                resp = bytearray(self._i2c.readfrom(self._addr, 25))
            except OSError:
                resp = bytearray(25)

            code = resp[0] | (resp[1] << 8)
            remain = resp[2] | (resp[3] << 8)
            ctrl_code = resp[4]

            if (
                code == BHI385_PARAM_WRIST_GEST_PHY
                and remain == 21
                and ctrl_code == 0x07
            ):
                # resp[5..24] = config[0..19]; device_pos is at config[18] = resp[23]
                resp[23] = hand
                # Write back: cmd=0x0E38, payload=[ctrl_code=0x07][config[0..19]] = 21 bytes
                success = self._send_command(
                    BHI385_PARAM_WRIST_GEST_PHY, bytes(resp[4:25])
                )
            elif self._dbg:
                print(
                    "[BHI385] _set_wrist_gesture_phys_param: unexpected response "
                    "code=0x{:04X} remain={} ctrlCode=0x{:02X}".format(
                        code, remain, ctrl_code
                    )
                )
        elif self._dbg:
            print(
                "[BHI385] _set_wrist_gesture_phys_param: timeout waiting for STATUS FIFO"
            )

        # Restore HOST_INTF_CTRL
        self._i2c_write_reg(BHI385_REG_HOST_INTF_CTRL, hif_ctrl_saved)
        return success

    # ---------------------------------------------------------------------------
    # Private: FIFO parsing
    # ---------------------------------------------------------------------------

    def _read_and_parse_fifo(self, channel):
        """
        Read one FIFO channel and parse all events it contains.

        :param channel: Channel register to read from
        :return: True on a successful channel read (even if 0 bytes)
        """
        data = self._channel_read(channel)
        if data:
            self._parse_fifo_data(data)
        return True

    def _parse_fifo_data(self, buf):
        """
        Walk the FIFO byte stream and dispatch each event.

        :param buf: bytes containing raw FIFO data
        """
        i = 0
        length = len(buf)
        while i < length:
            consumed = self._parse_event(buf, length, i)
            if consumed == 0:
                break  # Prevent infinite loop on unexpected data
            i += consumed

    def _parse_event(self, buf, length, offset):
        """
        Parse a single FIFO event starting at offset and return how many bytes
        were consumed (including the ID byte).

        :param buf: FIFO data buffer (bytes)
        :param length: Total valid length of buf
        :param offset: Byte offset of the event ID within buf
        :return: Number of bytes consumed by this event
        """
        if offset >= length:
            return 1

        event_id = buf[offset]

        # --- Padding / filler bytes ---
        if event_id == BHI385_FIFO_PAD or event_id == BHI385_FIFO_FILLER:
            return 1

        # --- WU FIFO system events (0xF5-0xF8) ---
        if event_id == BHI385_FIFO_TS_SMALL_DLT_WU:
            return 2  # 1 ID + 1 delta byte
        if event_id == BHI385_FIFO_TS_LARGE_DLT_WU:
            return 3  # 1 ID + 2 delta bytes
        if event_id == BHI385_FIFO_TS_FULL_WU:
            return 6  # 1 ID + 5 timestamp bytes
        if event_id == BHI385_FIFO_META_WU:
            return 4  # 1 ID + 3 meta bytes
        if event_id == 0xF9:
            return 1  # Invalid — skip to avoid loop
        if event_id == BHI385_FIFO_DEBUG_MSG:
            return 18  # 1 ID + 17 debug bytes

        # --- NW FIFO system events (0xFB-0xFE) ---
        if event_id == BHI385_FIFO_TS_SMALL_DLT:
            return 2
        if event_id == BHI385_FIFO_TS_LARGE_DLT:
            return 3
        if event_id == BHI385_FIFO_TS_FULL:
            return 6
        if event_id == BHI385_FIFO_META:
            return 4

        # --- Accelerometer event (7 bytes: ID + X + Y + Z as int16 LE) ---
        if event_id == self._accel_sensor_id:
            if offset + 7 <= length:
                raw_x = buf[offset + 1] | (buf[offset + 2] << 8)
                raw_y = buf[offset + 3] | (buf[offset + 4] << 8)
                raw_z = buf[offset + 5] | (buf[offset + 6] << 8)
                if raw_x >= 0x8000:
                    raw_x -= 0x10000
                if raw_y >= 0x8000:
                    raw_y -= 0x10000
                if raw_z >= 0x8000:
                    raw_z -= 0x10000
                self._accel[0] = raw_x / self._accel_sens
                self._accel[1] = raw_y / self._accel_sens
                self._accel[2] = raw_z / self._accel_sens
                self._accel_updated = True
            return 7

        # --- Gyroscope event (7 bytes: ID + X + Y + Z as int16 LE) ---
        if event_id == self._gyro_sensor_id:
            if offset + 7 <= length:
                raw_x = buf[offset + 1] | (buf[offset + 2] << 8)
                raw_y = buf[offset + 3] | (buf[offset + 4] << 8)
                raw_z = buf[offset + 5] | (buf[offset + 6] << 8)
                if raw_x >= 0x8000:
                    raw_x -= 0x10000
                if raw_y >= 0x8000:
                    raw_y -= 0x10000
                if raw_z >= 0x8000:
                    raw_z -= 0x10000
                self._gyro[0] = raw_x / self._gyro_sens
                self._gyro[1] = raw_y / self._gyro_sens
                self._gyro[2] = raw_z / self._gyro_sens
                self._gyro_updated = True
            return 7

        # --- Game Rotation Vector event (11 bytes: ID + x,y,z,w,accuracy as int16 LE) ---
        # Scale: x/y/z/w = raw / 16384.0 (normalized quaternion, range -1 to +1)
        #        accuracy = raw / 16384.0 * (180 / PI)  (radians → degrees)
        if event_id == self._quat_sensor_id:
            if offset + 11 <= length:
                rx = buf[offset + 1] | (buf[offset + 2] << 8)
                ry = buf[offset + 3] | (buf[offset + 4] << 8)
                rz = buf[offset + 5] | (buf[offset + 6] << 8)
                rw = buf[offset + 7] | (buf[offset + 8] << 8)
                ra = buf[offset + 9] | (buf[offset + 10] << 8)
                if rx >= 0x8000:
                    rx -= 0x10000
                if ry >= 0x8000:
                    ry -= 0x10000
                if rz >= 0x8000:
                    rz -= 0x10000
                if rw >= 0x8000:
                    rw -= 0x10000
                if ra >= 0x8000:
                    ra -= 0x10000
                self._quat[0] = rx / 16384.0
                self._quat[1] = ry / 16384.0
                self._quat[2] = rz / 16384.0
                self._quat[3] = rw / 16384.0
                self._quat[4] = ra / 16384.0 * (180.0 / 3.14159265)
                self._quat_updated = True
            return 11

        # --- Step counter event (5 bytes: ID + uint32 LE step count) ---
        if event_id == self._stc_sensor_id:
            if offset + 5 <= length:
                self._step_count = (
                    buf[offset + 1]
                    | (buf[offset + 2] << 8)
                    | (buf[offset + 3] << 16)
                    | (buf[offset + 4] << 24)
                )
                self._step_updated = True
            return 5

        # --- Wrist gesture event (2 bytes: ID + 1-byte gesture enum) ---
        if event_id == self._wrist_gest_sensor_id:
            if offset + 2 <= length:
                self._wrist_gesture = buf[offset + 1]
                self._wrist_gesture_updated = True
            return 2

        # --- Multi-tap event (2 bytes: ID + 1-byte tap type bitmask) ---
        if event_id == self._tap_sensor_id:
            if offset + 2 <= length:
                self._tap_type = buf[offset + 1]
                self._tap_updated = True
            return 2

        # --- Unknown sensor event: assume 3-axis format (7 bytes) as fallback ---
        return 7

    # ---------------------------------------------------------------------------
    # Private: Utilities
    # ---------------------------------------------------------------------------

    def _poll_boot_status(self, mask, timeout_ms):
        """
        Poll boot status register until the given bits are set or timeout expires.

        :param mask: One or more BHI385_BOOT_* bits to wait for
        :param timeout_ms: Timeout in milliseconds
        :return: True if mask bits were set within the timeout
        """
        t_start = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), t_start) < timeout_ms:
            if self.getBootStatus() & mask:
                return True
            time.sleep_ms(1)
        return False

    def _accel_range_to_sensitivity(self, range):
        """Convert accelerometer range constant to LSB/g divisor."""
        if range == BHI385_ACCEL_4G:
            return BHI385_ACCEL_SENS_4G
        elif range == BHI385_ACCEL_16G:
            return BHI385_ACCEL_SENS_16G
        elif range == BHI385_ACCEL_32G:
            return BHI385_ACCEL_SENS_32G
        else:
            return BHI385_ACCEL_SENS_8G  # Default: ±8g

    def _gyro_range_to_sensitivity(self, range):
        """Convert gyroscope range constant to LSB/(deg/s) divisor."""
        if range == BHI385_GYRO_125DPS:
            return BHI385_GYRO_SENS_125DPS
        elif range == BHI385_GYRO_250DPS:
            return BHI385_GYRO_SENS_250DPS
        elif range == BHI385_GYRO_500DPS:
            return BHI385_GYRO_SENS_500DPS
        elif range == BHI385_GYRO_1000DPS:
            return BHI385_GYRO_SENS_1000DPS
        else:
            return BHI385_GYRO_SENS_2000DPS  # Default: ±2000 deg/s
