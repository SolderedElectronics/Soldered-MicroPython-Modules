# FILE: drv8825.py
# AUTHOR: Josip Šimun Kuči @ Soldered (based on DRV8825 by Rob Tillaart)
# BRIEF: MicroPython library for DRV8825 stepper motor driver
# LAST UPDATED: 2025-05-23

from machine import Pin
from time import sleep_us, sleep_ms


class DRV8825:
    """
    Class for interfacing with the DRV8825 stepper motor driver via GPIO pins.
    """

    CLOCK_WISE = 1
    COUNTER_CLOCK_WISE = 0

    def __init__(self):
        """
        Constructor: Initializes internal state without configuring pins.
        """
        self._directionPin = None
        self._stepPin = None
        self._enablePin = None
        self._resetPin = None
        self._sleepPin = None

        self._direction = self.COUNTER_CLOCK_WISE
        self._steps = 0
        self._stepsPerRotation = 0
        self._position = 0
        self._stepPulseLength = 0  # in microseconds

    def begin(self, DIR, STEP, EN=None, RST=None, SLP=None):
        """
        Initialize motor control pins.

        Parameters:
            DIR  : GPIO pin number for direction
            STEP : GPIO pin number for step signal
            EN   : Optional GPIO pin number for enable
            RST  : Optional GPIO pin number for reset
            SLP  : Optional GPIO pin number for sleep

        Returns:
            True on successful setup.
        """
        self._directionPin = Pin(DIR, Pin.OUT, value=0)
        self._stepPin = Pin(STEP, Pin.OUT, value=0)

        if EN is not None:
            self._enablePin = Pin(EN, Pin.OUT, value=0)

        if RST is not None:
            self._resetPin = Pin(RST, Pin.OUT, value=1)

        if SLP is not None:
            self._sleepPin = Pin(SLP, Pin.OUT, value=1)

        return True

    def setStepsPerRotation(self, steps):
        """
        Define how many steps the motor takes per full rotation.
        """
        self._stepsPerRotation = steps

    def getStepsPerRotation(self):
        """
        Get configured steps per full rotation.
        """
        return self._stepsPerRotation

    def setDirection(self, direction):
        """
        Set motor direction.

        Parameters:
            direction : 0 for CCW, 1 for CW

        Returns:
            True if direction is valid, False otherwise.
        """
        if direction not in (0, 1):
            return False
        self._direction = direction
        sleep_us(1)
        self._directionPin.value(direction)
        sleep_us(1)
        return True

    def getDirection(self):
        """
        Get current direction signal value.
        """
        return self._directionPin.value()

    def step(self):
        """
        Perform one step and update internal counters and position.
        """
        self._stepPin.value(1)
        if self._stepPulseLength > 0:
            sleep_us(self._stepPulseLength)
        self._stepPin.value(0)
        if self._stepPulseLength > 0:
            sleep_us(self._stepPulseLength)

        self._steps += 1
        if self._stepsPerRotation > 0:
            if self._direction == self.CLOCK_WISE:
                self._position = (self._position + 1) % self._stepsPerRotation
            else:
                self._position = (
                    self._position - 1 + self._stepsPerRotation
                ) % self._stepsPerRotation

    def resetSteps(self, s=0):
        """
        Reset internal step counter.

        Parameters:
            s : new step count (default 0)

        Returns:
            Previous step count
        """
        old_steps = self._steps
        self._steps = s
        return old_steps

    def getSteps(self):
        """
        Get current step count.
        """
        return self._steps

    def setStepPulseLength(self, length):
        """
        Set pulse length in microseconds for the step signal.
        """
        self._stepPulseLength = length

    def getStepPulseLength(self):
        """
        Get current step pulse length in microseconds.
        """
        return self._stepPulseLength

    def setPosition(self, pos):
        """
        Manually set position within a rotation.

        Parameters:
            pos : position (must be less than stepsPerRotation)

        Returns:
            True if set successfully, False otherwise.
        """
        if pos >= self._stepsPerRotation:
            return False
        self._position = pos
        return True

    def getPosition(self):
        """
        Get current position within one full rotation.
        """
        return self._position

    def enable(self):
        """
        Enable the motor driver.
        """
        if self._enablePin is None:
            return False
        self._enablePin.value(0)
        return True

    def disable(self):
        """
        Disable the motor driver.
        """
        if self._enablePin is None:
            return False
        self._enablePin.value(1)
        return True

    def isEnabled(self):
        """
        Check if the motor is currently enabled.
        """
        if self._enablePin is not None:
            return self._enablePin.value() == 0
        return True

    def reset(self):
        """
        Perform a reset pulse on the driver.
        """
        if self._resetPin is None:
            return False
        self._resetPin.value(0)
        sleep_ms(1)
        self._resetPin.value(1)
        return True

    def sleep(self):
        """
        Put the motor driver to sleep mode.
        """
        if self._sleepPin is None:
            return False
        self._sleepPin.value(0)
        return True

    def wakeup(self):
        """
        Wake the motor driver from sleep mode.
        """
        if self._sleepPin is None:
            return False
        self._sleepPin.value(1)
        return True

    def isSleeping(self):
        """
        Check if the driver is currently in sleep mode.
        """
        if self._sleepPin is not None:
            return self._sleepPin.value() == 0
        return False
