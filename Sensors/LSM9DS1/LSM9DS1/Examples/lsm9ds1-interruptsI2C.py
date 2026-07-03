# FILE: lsm9ds1-interruptsI2C.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Use LSM9DS1 hardware interrupts for threshold and data-ready events
# LAST UPDATED: 2026-06-02
#
# Interrupt pins (change to match your wiring, must support interrupts):
#   INT1_PIN  → INT1-A on breakout (gyro/accel threshold, active low)
#   INT2_PIN  → INT2-A on breakout (accel/gyro data ready, active low)
#   INTM_PIN  → INT-M  on breakout (mag threshold, active low)
#   RDYM_PIN  → RDY-M  on breakout (mag data ready, active high)
# NOTE: These pins are 3.3V only on the breakout!

from lsm9ds1 import (
    LSM9DS1,
    XG_INT1,
    XG_INT2,
    ZHIE_G,
    XHIE_XL,
    XIEN,
    INT1_IG_G,
    INT_IG_XL,
    INT_DRDY_XL,
    INT_DRDY_G,
    INT_ACTIVE_LOW,
    INT_PUSH_PULL,
    X_AXIS,
    Z_AXIS,
)
from machine import Pin
import time

# Change these to the GPIO pins connected to the interrupt outputs
INT1_PIN = Pin(2, Pin.IN, Pin.PULL_UP)
INT2_PIN = Pin(4, Pin.IN, Pin.PULL_UP)
INTM_PIN = Pin(5, Pin.IN, Pin.PULL_UP)
RDYM_PIN = Pin(14, Pin.IN)

imu = LSM9DS1(auto_begin=False)
imu.settings.gyro.latchInterrupt = False
imu.settings.gyro.scale = 245
imu.settings.gyro.sampleRate = 1  # 14.9 Hz
imu.settings.accel.scale = 2
imu.settings.mag.scale = 4
imu.settings.mag.sampleRate = 0  # 0.625 Hz
imu.begin()

# INT1 fires when gyro Z or accel X exceed threshold (active low, not latched)
imu.configGyroInt(ZHIE_G, False, False)
imu.configGyroThs(500, Z_AXIS, 10, True)
imu.configAccelInt(XHIE_XL, False)
imu.configAccelThs(20, X_AXIS, 1, False)
imu.configInt(XG_INT1, INT1_IG_G | INT_IG_XL, INT_ACTIVE_LOW, INT_PUSH_PULL)

# INT2 fires when new accel or gyro data is available (active low)
imu.configInt(XG_INT2, INT_DRDY_XL | INT_DRDY_G, INT_ACTIVE_LOW, INT_PUSH_PULL)

# INT-M fires when magnetometer X exceeds threshold (active low, latched)
imu.configMagInt(XIEN, INT_ACTIVE_LOW, True)
imu.configMagThs(10000)

lastPrint = time.ticks_ms()

while True:
    # Print all sensor values every second
    if time.ticks_diff(time.ticks_ms(), lastPrint) >= 1000:
        imu.readAccel()
        imu.readGyro()
        imu.readMag()
        print(
            "A: {:.2f}, {:.2f}, {:.2f}".format(
                imu.calcAccel(imu.ax), imu.calcAccel(imu.ay), imu.calcAccel(imu.az)
            )
        )
        print(
            "G: {:.2f}, {:.2f}, {:.2f}".format(
                imu.calcGyro(imu.gx), imu.calcGyro(imu.gy), imu.calcGyro(imu.gz)
            )
        )
        print(
            "M: {:.2f}, {:.2f}, {:.2f}".format(
                imu.calcMag(imu.mx), imu.calcMag(imu.my), imu.calcMag(imu.mz)
            )
        )
        lastPrint = time.ticks_ms()

    # INT2: new accel/gyro data available (active low)
    if not INT2_PIN.value():
        if imu.accelAvailable():
            imu.readAccel()
        if imu.gyroAvailable():
            imu.readGyro()

    # INT1: gyro/accel threshold exceeded (active low, stays low while exceeded)
    if not INT1_PIN.value():
        start = time.ticks_ms()
        print("\tINT1 Active!")
        print("\t\tGyro int:  0x{:02X}".format(imu.getGyroIntSrc()))
        print("\t\tAccel int: 0x{:02X}".format(imu.getAccelIntSrc()))
        while not INT1_PIN.value():
            imu.getGyroIntSrc()
            imu.getAccelIntSrc()
        print("\tINT1 Duration: {} ms".format(time.ticks_diff(time.ticks_ms(), start)))

    # INT-M: magnetometer threshold exceeded (active low, latched)
    if not INTM_PIN.value():
        start = time.ticks_ms()
        print("\t\tMag int: 0x{:02X}".format(imu.getMagIntSrc()))
        while not INTM_PIN.value():
            pass
        print(
            "\t\tINTM Duration: {} ms".format(time.ticks_diff(time.ticks_ms(), start))
        )

    # RDY-M: new magnetometer data available (active high)
    if RDYM_PIN.value():
        if imu.magAvailable():
            imu.readMag()
