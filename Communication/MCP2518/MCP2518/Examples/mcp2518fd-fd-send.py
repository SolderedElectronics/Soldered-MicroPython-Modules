# FILE: mcp2518fd-fd-send.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: CAN FD message send example using MCP2518FD.
# WORKS WITH: CAN Bus Breakout: solde.red/333020
# LAST UPDATED: 2026-05-21

# Connecting diagram:
#
# CAN Bus Breakout    Dasduino
# NCS--------------->5
# SDI--------------->23 (MOSI)
# SDO--------------->19 (MISO)
# SCK--------------->18
# GND--------------->GND
# VCC--------------->5V
# INT--------------->not connected (optional)

from machine import SPI, Pin
import time
from mcp2518fd import MCP2518FD, CAN_OK, CAN_NORMAL_MODE, CAN_125K_500K, MCP2518FD_20MHz

MAX_DATA_SIZE = 64

# Change these to match your wiring
PIN_CS = 5
PIN_MOSI = 23
PIN_MISO = 19
PIN_SCK = 18

spi = SPI(
    1,
    baudrate=4000000,
    polarity=0,
    phase=0,
    firstbit=SPI.MSB,
    sck=Pin(PIN_SCK),
    mosi=Pin(PIN_MOSI),
    miso=Pin(PIN_MISO),
)

CAN = MCP2518FD(cs_pin=PIN_CS, spi=spi)

# -------------------------------------------------------------------------
# Setup
# -------------------------------------------------------------------------
print("MCP2518FD CAN FD Bus - Send Example")

CAN.setMode(CAN_NORMAL_MODE)

while CAN.begin(CAN_125K_500K, MCP2518FD_20MHz) != CAN_OK:
    print("CAN init fail, retry...")
    time.sleep_ms(100)

print("CAN init ok!")

stmp = bytes(range(MAX_DATA_SIZE))

# -------------------------------------------------------------------------
# Main loop
# -------------------------------------------------------------------------
while True:
    CAN.sendMsgBuf(0x01, 0, MAX_DATA_SIZE, stmp)
    time.sleep_ms(10)
    CAN.sendMsgBuf(0x04, 0, MAX_DATA_SIZE, stmp)
    time.sleep_ms(500)
    print("CAN BUS sendMsgBuf ok!")
