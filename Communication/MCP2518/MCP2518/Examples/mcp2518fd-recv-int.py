# FILE: mcp2518fd-recv-int.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: CAN 2.0 message receive example using hardware interrupt on MCP2518FD.
# WORKS WITH: CAN Bus Breakout: solde.red/333020
# LAST UPDATED: 2026-05-22

# Connecting diagram:
#
# CAN Bus Breakout    Dasduino
# NCS--------------->5
# SDI--------------->23 (MOSI)
# SDO--------------->19 (MISO)
# SCK--------------->18
# INT--------------->4
# GND--------------->GND
# VCC--------------->5V

from machine import SPI, Pin
import time
from mcp2518fd import MCP2518FD, CAN_OK, CAN_MSGAVAIL, CAN_125KBPS, MCP2518FD_20MHz

# Change these to match your wiring
PIN_CS   = 5
PIN_MOSI = 23
PIN_MISO = 19
PIN_SCK  = 18
PIN_INT  = 4

spi = SPI(1, baudrate=4000000, polarity=0, phase=0, firstbit=SPI.MSB,
          sck=Pin(PIN_SCK), mosi=Pin(PIN_MOSI), miso=Pin(PIN_MISO))

CAN = MCP2518FD(cs_pin=PIN_CS, spi=spi)

flag_recv = False

def can_isr(pin):
    global flag_recv
    flag_recv = True

# -------------------------------------------------------------------------
# Setup
# -------------------------------------------------------------------------
print("MCP2518FD CAN Bus - Receive with Interrupt Example")

while CAN.begin(CAN_125KBPS, MCP2518FD_20MHz) != CAN_OK:
    print("CAN init fail, retry...")
    time.sleep_ms(100)

print("CAN init ok!")

int_pin = Pin(PIN_INT, Pin.IN)
int_pin.irq(trigger=Pin.IRQ_FALLING, handler=can_isr)

# -------------------------------------------------------------------------
# Main loop
# -------------------------------------------------------------------------
while True:
    if flag_recv:
        flag_recv = False
        # Drain FIFO — INT stays low while messages remain
        while CAN.checkReceive() == CAN_MSGAVAIL:
            length, buf = CAN.readMsgBuf()
            can_id = CAN.getCanId()
            print("Get Data From id:", can_id)
            print("Len =", length)
            print("\t".join(str(buf[i]) for i in range(length)))
