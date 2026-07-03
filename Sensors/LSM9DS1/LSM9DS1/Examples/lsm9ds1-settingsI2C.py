# FILE: lsm9ds1-settingsI2C.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Configure LSM9DS1 with custom settings before init, print data rates and values
# LAST UPDATED: 2026-06-02

from lsm9ds1 import LSM9DS1
import time

PRINT_RATE_MS = 500

imu = LSM9DS1(auto_begin=False)

# Gyroscope settings
imu.settings.gyro.enabled        = True
imu.settings.gyro.scale          = 245    # 245, 500, or 2000 dps
imu.settings.gyro.sampleRate     = 3      # 1=14.9 2=59.5 3=119 4=238 5=476 6=952 Hz
imu.settings.gyro.bandwidth      = 0
imu.settings.gyro.lowPowerEnable = False
imu.settings.gyro.HPFEnable      = True
imu.settings.gyro.HPFCutoff      = 1      # cutoff depends on ODR, see datasheet
imu.settings.gyro.flipX          = False
imu.settings.gyro.flipY          = False
imu.settings.gyro.flipZ          = False

# Accelerometer settings
imu.settings.accel.enabled          = True
imu.settings.accel.enableX          = True
imu.settings.accel.enableY          = True
imu.settings.accel.enableZ          = True
imu.settings.accel.scale            = 8    # 2, 4, 8, or 16 g
imu.settings.accel.sampleRate       = 1    # 1=10 2=50 3=119 4=238 5=476 6=952 Hz
imu.settings.accel.bandwidth        = 0    # -1=ODR-dependent 0=408 1=211 2=105 3=50 Hz
imu.settings.accel.highResEnable    = False
imu.settings.accel.highResBandwidth = 0

# Magnetometer settings
imu.settings.mag.enabled                = True
imu.settings.mag.scale                  = 12   # 4, 8, 12, or 16 Gauss
imu.settings.mag.sampleRate             = 5    # 0=0.625 1=1.25 2=2.5 3=5 4=10 5=20 6=40 7=80 Hz
imu.settings.mag.tempCompensationEnable = False
imu.settings.mag.XYPerformance          = 3    # 0=low 1=med 2=high 3=ultra
imu.settings.mag.ZPerformance           = 3
imu.settings.mag.lowPowerEnable         = False
imu.settings.mag.operatingMode          = 0    # 0=continuous 1=single 2=power-down

imu.settings.temp.enabled = True

status = imu.begin()
print("LSM9DS1 WHO_AM_I: 0x{:04X} (should be 0x683D)".format(status))

startTime  = time.ticks_ms()
accelCount = gyroCount = magCount = tempCount = 0
lastPrint  = time.ticks_ms()

while True:
    if imu.accelAvailable():
        imu.readAccel()
        accelCount += 1
    if imu.gyroAvailable():
        imu.readGyro()
        gyroCount += 1
    if imu.magAvailable():
        imu.readMag()
        magCount += 1
    if imu.tempAvailable():
        imu.readTemp()
        tempCount += 1

    if time.ticks_diff(time.ticks_ms(), lastPrint) >= PRINT_RATE_MS:
        runTime = time.ticks_diff(time.ticks_ms(), startTime) / 1000.0
        print("A: {:.4f}, {:.4f}, {:.4f} g\t| {:.1f} Hz".format(
            imu.calcAccel(imu.ax), imu.calcAccel(imu.ay), imu.calcAccel(imu.az),
            accelCount / runTime))
        print("G: {:.4f}, {:.4f}, {:.4f} dps\t| {:.1f} Hz".format(
            imu.calcGyro(imu.gx), imu.calcGyro(imu.gy), imu.calcGyro(imu.gz),
            gyroCount / runTime))
        print("M: {:.4f}, {:.4f}, {:.4f} Gs\t| {:.1f} Hz".format(
            imu.calcMag(imu.mx), imu.calcMag(imu.my), imu.calcMag(imu.mz),
            magCount / runTime))
        print("T: {} C\t\t\t\t| {:.1f} Hz".format(imu.temperature, tempCount / runTime))
        print()
        lastPrint = time.ticks_ms()
