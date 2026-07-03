# FILE: mcp47a1-waveformGenerator.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: This example shows how to generate simple wavefroms like sinewave, triangle wave and sawtooth wave. 
#        You will need 330 Ohm resistor and LED. Connect LED and resistor at the output of a DAC. 
#        You can alternatively use oscilloscope or small speaker.
# WORKS WITH: DAC 6-Bit 1-Channel MCP47A1 Breakout: www.solde.red/333052
# LAST UPDATED: 2026-04-29

import time
import math
from mcp47a1 import MCP47A1

# If you aren't using the Qwiic connector, manually enter your I2C pins:
# i2c = I2C(0, scl=Pin(22), sda=Pin(21))
# mcp47a1 = MCP47A1(i2c)

# Initialize DAC over Qwiic
mcp47a1 = MCP47A1()

selectedWaveform = 0     # 0=sine, 1=triangle, 2=sawtooth
waveformLUT = [0] * 65   # 65 samples (0–64)

def make_lut(waveform):
    global waveformLUT

    if waveform == 0:  # Sine
        for i in range(65):
            waveformLUT[i] = int(32 * math.sin(2 * math.pi * i / 65) + 32)

    elif waveform == 1:  # Triangle
        n = 0
        direction = 2
        for i in range(65):
            if i == 32:
                direction = -2
            n += direction
            waveformLUT[i] = n

    elif waveform == 2:  # Sawtooth
        for i in range(65):
            waveformLUT[i] = i

make_lut(selectedWaveform)

k = 0

while True:
    mcp47a1.writeByte(waveformLUT[k])

    k += 1
    if k > 64:
        k = 0

    time.sleep_ms(100)