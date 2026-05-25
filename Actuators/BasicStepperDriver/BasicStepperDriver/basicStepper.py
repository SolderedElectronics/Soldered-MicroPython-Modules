# FILE: basicstepper.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: MicroPython stepper motor library with acceleration/deceleration and multi-axis support
# LAST UPDATED: 2026-05-25

import math
import time
from machine import Pin

MULTISTEPPER_MAX_STEPPERS = 10


class BasicStepper:
    """
    Stepper motor controller with acceleration/deceleration support.

    Supports stepper drivers (step/dir), 2/3/4-wire full and half-step motors,
    and functional (callback) interfaces. Multiple simultaneous steppers are
    supported by calling run() on each in your main loop.

    Algorithm based on "Generate stepper-motor speed profiles in real time"
    by David Austin.
    """

    # Motor interface types
    FUNCTION  = 0  # Callback functions (forward/backward)
    DRIVER    = 1  # Step/Direction driver (A4988, DRV8825, TMC2208, ...)
    FULL2WIRE = 2  # 2-wire bipolar
    FULL3WIRE = 3  # 3-wire (e.g. HDD spindle)
    FULL4WIRE = 4  # 4-wire full step
    HALF3WIRE = 6  # 3-wire half step
    HALF4WIRE = 8  # 4-wire half step

    _DIRECTION_CCW = 0
    _DIRECTION_CW  = 1

    # Step sequencing tables — class-level tuples, allocated once
    _STEP2_SEQ = (0b10, 0b11, 0b01, 0b00)
    _STEP3_SEQ = (0b100, 0b001, 0b010)
    _STEP4_SEQ = (0b0101, 0b0110, 0b1010, 0b1001)
    _STEP6_SEQ = (0b100, 0b101, 0b001, 0b011, 0b010, 0b110)
    _STEP8_SEQ = (0b0001, 0b0101, 0b0100, 0b0110,
                  0b0010, 0b1010, 0b1000, 0b1001)

    def __init__(self, interface=4, pin1=2, pin2=3, pin3=4, pin4=5, enable=True):
        """
        Standard constructor.
            interface : motor interface type (BasicStepper.DRIVER, BasicStepper.FULL4WIRE, ...)
            pin1-pin4 : GPIO pin numbers
            enable    : call enableOutputs() at construction time (default True)

        Functional constructor — pass callables instead of interface type:
            interface : forward() callback
            pin1      : backward() callback
        """
        if callable(interface):
            self._interface   = self.FUNCTION
            self._forward_cb  = interface
            self._backward_cb = pin1
            self._pin_nums    = [0, 0, 0, 0]
        else:
            self._interface   = interface
            self._forward_cb  = None
            self._backward_cb = None
            self._pin_nums    = [pin1, pin2, pin3, pin4]

        # Cache pin count — interface never changes after construction
        if self._interface in (self.FULL4WIRE, self.HALF4WIRE):
            self._numpins = 4
        elif self._interface in (self.FULL3WIRE, self.HALF3WIRE):
            self._numpins = 3
        else:
            self._numpins = 2

        self._pin         = [None, None, None, None]
        self._pinInverted = [0, 0, 0, 0]

        self._currentPos     = 0
        self._targetPos      = 0
        self._speed          = 0.0
        self._maxSpeed       = 0.0
        self._acceleration   = 0.0
        self._sqrt_twoa      = 1.0
        self._stepInterval   = 0
        self._minPulseWidth  = 1
        self._enablePin      = None
        self._enableInverted = False
        self._lastStepTime   = 0
        self._direction      = self._DIRECTION_CCW
        self._n              = 0
        self._c0             = 0.0
        self._cn             = 0.0
        self._cmin           = 1.0

        if enable:
            self.enableOutputs()

        self.setAcceleration(1)
        self.setMaxSpeed(1)

    # ------------------------------------------------------------------
    # Position / target
    # ------------------------------------------------------------------

    def moveTo(self, absolute):
        """Set absolute target position (steps). Triggers speed recompute."""
        if self._targetPos != absolute:
            self._targetPos = absolute
            self.computeNewSpeed()

    def move(self, relative):
        """Set target position relative to current position."""
        self.moveTo(self._currentPos + relative)

    def distanceToGo(self):
        """Steps remaining to target. Positive = CW."""
        return self._targetPos - self._currentPos

    def targetPosition(self):
        """Most recently set target position in steps."""
        return self._targetPos

    def currentPosition(self):
        """Current motor position in steps."""
        return self._currentPos

    def setCurrentPosition(self, position):
        """Reset current position to given value without moving. Also zeroes speed."""
        self._targetPos    = position
        self._currentPos   = position
        self._n            = 0
        self._stepInterval = 0
        self._speed        = 0.0

    # ------------------------------------------------------------------
    # Speed / acceleration
    # ------------------------------------------------------------------

    def setMaxSpeed(self, speed):
        """Set maximum speed in steps/second. Must be > 0."""
        if speed < 0.0:
            speed = -speed
        if self._maxSpeed != speed:
            self._maxSpeed = speed
            self._cmin = 1000000.0 / speed
            if self._n > 0 and self._acceleration > 0:
                self._n = int((self._speed * self._speed) / (2.0 * self._acceleration))
                self.computeNewSpeed()

    def maxSpeed(self):
        """Return currently configured maximum speed."""
        return self._maxSpeed

    def setAcceleration(self, acceleration):
        """
        Set acceleration/deceleration in steps/second^2. Must be > 0.
        Expensive call (computes sqrt). Don't call more often than needed.
        """
        if acceleration == 0.0:
            return
        if acceleration < 0.0:
            acceleration = -acceleration
        if self._acceleration != acceleration:
            if self._acceleration > 0:
                self._n = int(self._n * (self._acceleration / acceleration))
            self._c0 = 0.676 * math.sqrt(2.0 / acceleration) * 1000000.0  # Eq. 15
            self._acceleration = acceleration
            self.computeNewSpeed()

    def acceleration(self):
        """Return currently configured acceleration."""
        return self._acceleration

    def setSpeed(self, speed):
        """Set constant speed for use with runSpeed(). Positive = CW. Clamped to ±maxSpeed."""
        if speed == self._speed:
            return
        speed = max(-self._maxSpeed, min(self._maxSpeed, speed))
        if speed == 0.0:
            self._stepInterval = 0
        else:
            self._stepInterval = abs(1000000.0 / speed)
            self._direction = self._DIRECTION_CW if speed > 0.0 else self._DIRECTION_CCW
        self._speed = speed

    def speed(self):
        """Return most recently set speed."""
        return self._speed

    def computeNewSpeed(self):
        """
        Recompute instantaneous step interval based on position and acceleration.
        Called internally after each step and after parameter changes.
        """
        distanceTo  = self.distanceToGo()
        stepsToStop = int((self._speed * self._speed) / (2.0 * self._acceleration)) \
                      if self._acceleration > 0 else 0  # Eq. 16

        if distanceTo == 0 and stepsToStop <= 1:
            self._stepInterval = 0
            self._speed        = 0.0
            self._n            = 0
            return self._stepInterval

        if distanceTo > 0:
            if self._n > 0:
                if stepsToStop >= distanceTo or self._direction == self._DIRECTION_CCW:
                    self._n = -stepsToStop
            elif self._n < 0:
                if stepsToStop < distanceTo and self._direction == self._DIRECTION_CW:
                    self._n = -self._n
        elif distanceTo < 0:
            if self._n > 0:
                if stepsToStop >= -distanceTo or self._direction == self._DIRECTION_CW:
                    self._n = -stepsToStop
            elif self._n < 0:
                if stepsToStop < -distanceTo and self._direction == self._DIRECTION_CCW:
                    self._n = -self._n

        if self._n == 0:
            self._cn        = self._c0
            self._direction = self._DIRECTION_CW if distanceTo > 0 else self._DIRECTION_CCW
        else:
            self._cn = self._cn - ((2.0 * self._cn) / ((4.0 * self._n) + 1))  # Eq. 13
            self._cn = max(self._cn, self._cmin)

        self._n           += 1
        self._stepInterval = self._cn
        self._speed        = 1000000.0 / self._cn
        if self._direction == self._DIRECTION_CCW:
            self._speed = -self._speed

        return self._stepInterval

    # ------------------------------------------------------------------
    # Run functions (call frequently in main loop)
    # ------------------------------------------------------------------

    def run(self):
        """
        Step motor once if due, with acceleration/deceleration toward target.
        Call as frequently as possible in main loop.
        Returns True if motor is still running toward target.
        """
        if self.runSpeed():
            self.computeNewSpeed()
        return self._speed != 0.0 or self.distanceToGo() != 0

    def runSpeed(self):
        """
        Step motor once if due, at constant speed set by setSpeed().
        Returns True if a step occurred.
        """
        if not self._stepInterval:
            return False
        now = time.ticks_us()
        if time.ticks_diff(now, self._lastStepTime) >= self._stepInterval:
            if self._direction == self._DIRECTION_CW:
                self._currentPos += 1
            else:
                self._currentPos -= 1
            self._do_step(self._currentPos)
            self._lastStepTime = now
            return True
        return False

    def runToPosition(self):
        """Blocking: move to target position with acceleration/deceleration."""
        while self.run():
            time.sleep_us(0)  # yield for ESP8266 watchdog

    def runToNewPosition(self, position):
        """Blocking: set new target and move there with acceleration/deceleration."""
        self.moveTo(position)
        self.runToPosition()

    def runSpeedToPosition(self):
        """Non-blocking constant-speed run toward target. Returns True if stepped."""
        if self._targetPos == self._currentPos:
            return False
        self._direction = self._DIRECTION_CW if self._targetPos > self._currentPos else self._DIRECTION_CCW
        return self.runSpeed()

    def stop(self):
        """Decelerate to stop as quickly as possible given current acceleration."""
        if self._speed != 0.0 and self._acceleration > 0:
            stepsToStop = int((self._speed * self._speed) / (2.0 * self._acceleration)) + 1
            self.move(stepsToStop if self._speed > 0 else -stepsToStop)

    def isRunning(self):
        """Return True if motor is moving or has not reached target."""
        return not (self._speed == 0.0 and self._targetPos == self._currentPos)

    # ------------------------------------------------------------------
    # Step output
    # ------------------------------------------------------------------

    def setOutputPins(self, mask):
        """
        Set motor output pins according to bitmask.
        Bit 0 → pin[0], bit 1 → pin[1], etc. Respects pin inversion.
        Can be overridden for serial or other output implementations.
        """
        for i in range(self._numpins):
            if self._pin[i] is not None:
                self._pin[i].value((1 if (mask & (1 << i)) else 0) ^ self._pinInverted[i])

    def stepForward(self):
        """Manual single step CW. Returns updated position."""
        self._currentPos += 1
        self._do_step(self._currentPos)
        self._lastStepTime = time.ticks_us()
        return self._currentPos

    def stepBackward(self):
        """Manual single step CCW. Returns updated position."""
        self._currentPos -= 1
        self._do_step(self._currentPos)
        self._lastStepTime = time.ticks_us()
        return self._currentPos

    def _do_step(self, step):
        iface = self._interface
        if   iface == self.FUNCTION:  self._step0(step)
        elif iface == self.DRIVER:    self._step1(step)
        elif iface == self.FULL2WIRE: self._step2(step)
        elif iface == self.FULL3WIRE: self._step3(step)
        elif iface == self.FULL4WIRE: self._step4(step)
        elif iface == self.HALF3WIRE: self._step6(step)
        elif iface == self.HALF4WIRE: self._step8(step)

    def _step0(self, step):
        if self._speed > 0:
            self._forward_cb()
        else:
            self._backward_cb()

    def _step1(self, step):
        # pin[0] = STEP, pin[1] = DIR
        self.setOutputPins(0b10 if self._direction else 0b00)  # DIR first
        self.setOutputPins(0b11 if self._direction else 0b01)  # STEP HIGH
        time.sleep_us(self._minPulseWidth)
        self.setOutputPins(0b10 if self._direction else 0b00)  # STEP LOW

    def _step2(self, step):
        self.setOutputPins(self._STEP2_SEQ[step & 0x3])

    def _step3(self, step):
        self.setOutputPins(self._STEP3_SEQ[step % 3])

    def _step4(self, step):
        self.setOutputPins(self._STEP4_SEQ[step & 0x3])

    def _step6(self, step):
        self.setOutputPins(self._STEP6_SEQ[step % 6])

    def _step8(self, step):
        self.setOutputPins(self._STEP8_SEQ[step & 0x7])

    # ------------------------------------------------------------------
    # Enable / disable
    # ------------------------------------------------------------------

    def enableOutputs(self):
        """Set motor pins to OUTPUT and assert enable pin (if set)."""
        if not self._interface:
            return
        for i in range(self._numpins):
            self._pin[i] = Pin(self._pin_nums[i], Pin.OUT)
        if self._enablePin is not None:
            self._enablePin.value(1 ^ int(self._enableInverted))

    def disableOutputs(self):
        """Set all motor pins LOW and de-assert enable pin to save power."""
        if not self._interface:
            return
        self.setOutputPins(0)
        if self._enablePin is not None:
            self._enablePin.value(0 ^ int(self._enableInverted))

    def setMinPulseWidth(self, minWidth):
        """Set minimum STEP pulse width in microseconds (DRIVER mode)."""
        self._minPulseWidth = minWidth

    def setEnablePin(self, enablePin=None):
        """Set enable pin number. Pass None to disable. Pin is asserted immediately."""
        if enablePin is not None:
            self._enablePin = Pin(enablePin, Pin.OUT)
            self._enablePin.value(1 ^ int(self._enableInverted))
        else:
            self._enablePin = None

    def setPinsInverted(self, *args):
        """
        Invert step/dir/enable signals.
        3-arg form (directionInvert, stepInvert, enableInvert)   — DRIVER mode
        5-arg form (pin1, pin2, pin3, pin4, enableInvert)        — multi-wire modes
        """
        if len(args) == 3:
            self._pinInverted[0] = int(args[1])   # STEP pin
            self._pinInverted[1] = int(args[0])   # DIR  pin
            self._enableInverted = bool(args[2])
        elif len(args) == 5:
            for i in range(4):
                self._pinInverted[i] = int(args[i])
            self._enableInverted = bool(args[4])


# ----------------------------------------------------------------------

class MultiStepper:
    """
    Coordinate up to MULTISTEPPER_MAX_STEPPERS BasicStepper instances.

    Computes individual constant speeds so all steppers reach their target
    positions at the same time — useful for XY plotters, 3D printers, etc.

    Note: only constant speed is used (no acceleration during coordinated moves).
    """

    def __init__(self):
        self._steppers     = []
        self._num_steppers = 0

    def addStepper(self, stepper):
        """Add a BasicStepper to the managed set. Returns False if limit exceeded."""
        if self._num_steppers >= MULTISTEPPER_MAX_STEPPERS:
            return False
        self._steppers.append(stepper)
        self._num_steppers += 1
        return True

    def moveTo(self, absolute):
        """
        Set target positions for all managed steppers.
        Speeds adjusted so all arrive simultaneously.
        absolute: list/tuple of positions, one per stepper in order added.
        """
        longestTime = 0.0
        for i in range(self._num_steppers):
            dist = absolute[i] - self._steppers[i].currentPosition()
            spd  = self._steppers[i].maxSpeed()
            if spd > 0:
                t = abs(dist) / spd
                if t > longestTime:
                    longestTime = t

        if longestTime > 0.0:
            for i in range(self._num_steppers):
                dist = absolute[i] - self._steppers[i].currentPosition()
                self._steppers[i].moveTo(absolute[i])
                self._steppers[i].setSpeed(dist / longestTime)

    def run(self):
        """Call runSpeed() on each stepper not yet at target. Returns True if any still running."""
        ret = False
        for i in range(self._num_steppers):
            if self._steppers[i].distanceToGo() != 0:
                self._steppers[i].runSpeed()
                ret = True
        return ret

    def runSpeedToPosition(self):
        """Blocking: run all steppers until every target position is reached."""
        while self.run():
            pass
