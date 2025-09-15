# FILE: DS3234-writeSRAM.py 
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: Example showing how to write and retrieve 
#        data from RTC SRAM
# WORKS WITH: DS3234 RTC Breakout: www.solde.red/333358
# LAST UPDATED: 2025-09-15 

import machine
import time
import struct
from DS3234 import DS3234

# Configurable Pin Definitions
DS3234_CS_PIN = 5  # DS3234 RTC Chip-select pin

# Initialize SPI and CS pin
# Using VSPI (SPI ID 2) with default ESP32 pins
spi = machine.SPI(2, baudrate=1000000, polarity=1, phase=1,
                  sck=machine.Pin(18), mosi=machine.Pin(23), miso=machine.Pin(19))
cs_pin = machine.Pin(DS3234_CS_PIN, machine.Pin.OUT)

# Create an instance of the RTC object
rtc = DS3234(spi, cs_pin)

print("\n### Starting DS3234_RTC_SRAM_Demo! ###\n")

# We don't set time or do other clock-related stuff here.
# This is a demo about SRAM functionality

""" Write and read single bytes to/from SRAM """

# The DS3234 has 256 bytes of SRAM
# The address is a uint8_t ranging from 0 to 255
sram_address = 161  # == 0xA1

# Choose some data to store in SRAM
data_byte = 42

print("Writing a byte with value", data_byte, "to memory address 0x{:02X}.".format(sram_address))

# Do the writing here...
# Note: If you have battery support on your RTC module, this value
# will survive reboots and even extended periods without external power.
rtc.writeToSRAM(sram_address, data_byte)

# Now we read the value back from SRAM
read_back_byte = rtc.readFromSRAM(sram_address)

print("We have read back a byte with value", read_back_byte, "from memory address 0x{:02X}.".format(sram_address))

""" Write and read several bytes to/from an array """

# Put some data into an array of bytes
write_buffer = bytearray([101, 102, 103, 104, 199, 255])

# Get the length of the array to write
length = len(write_buffer)

print("Writing", length, "byte(s) to SRAM, starting at address 0x{:02X}.".format(sram_address))
print("Values to write:", " ".join(str(b) for b in write_buffer))

# Now we do the writing
rtc.writeToSRAMBuffer(sram_address, write_buffer)

# Create an array to hold the data we read back from SRAM
read_buffer = bytearray(length)

# Now read back the stored data into read_buffer
read_data = rtc.readFromSRAMBuffer(sram_address, length)

print("Data we have read back starting from SRAM address 0x{:02X}:".format(sram_address), 
      " ".join(str(b) for b in read_data))

""" Write and read other data types directly to/from SRAM """

# Note:
# You are responsible for non-overlapping memory ranges. If you write some data type with
# a width of, say, four byte to SRAM address x, the next value to store can start at SRAM
# address x+4 (because locations x, x+1, x+2 and x+3 are already in use).

# Warning:
# writeToSRAMValue() and readFromSRAMValue() do not take byte-ordering (i.e. "endian-ness") into
# account. If you want to write data to SRAM of the DS3234 on one type of microcontroller,
# unplug it, re-plug it to another type of microcontroller, you have to make sure that both
# types of MC work with the same byte ordering, otherwise you might get garbage.

# Example 1: Store and read a uint16_t
uint16_data = 32769

# write uint16_t to SRAM
print("Writing a uint16_t with value", uint16_data, "to memory address 0x{:02X}.".format(sram_address))

rtc.writeToSRAMValue(sram_address, uint16_data, 'uint16')

# And now read the value back:
read_back_uint16 = rtc.readFromSRAMValue(sram_address, 'uint16')

print("We have read back a uint16_t with value", read_back_uint16, "from memory address 0x{:02X}.".format(sram_address))

print("Written and read uint16_t values are equal:", uint16_data == read_back_uint16)

# Example 2: Using a signed integer this time
int32_data = -128653
rtc.writeToSRAMValue(sram_address, int32_data, 'int32')

read_back_int32 = rtc.readFromSRAMValue(sram_address, 'int32')

print("Written and read int32_t values are equal:", int32_data == read_back_int32)

# Example 3: Using a floating point
float_data = 3.14159265358979  # the number pi
rtc.writeToSRAMValue(sram_address, float_data, 'float')

read_back_float = rtc.readFromSRAMValue(sram_address, 'float')

print("Written and read float values are equal:", abs(float_data - read_back_float) < 0.0001)

# Example 4: Using a string (custom implementation)
string_data = "Hello RTC!"
string_address = sram_address + 20  # Different address to avoid overlap

# Convert string to bytes and write
string_bytes = string_data.encode('utf-8')
rtc.writeToSRAMBuffer(string_address, string_bytes)

# Read back and convert to string
read_string_bytes = rtc.readFromSRAMBuffer(string_address, len(string_bytes))
read_string = read_string_bytes.decode('utf-8')

print("Original string:", string_data)
print("Read back string:", read_string)
print("Strings are equal:", string_data == read_string)

# Example 5: Demonstrate persistence across resets
print("\nTesting SRAM persistence across reset...")
persistent_address = 200

# Write a value that should persist
persistent_value = 123
rtc.readFromSRAM(persistent_address)

print("Wrote value", persistent_value, "to address 0x{:02X}".format(persistent_address))
print("Reset the board and run this script again to check if the value persists")

print("\n### DS3234_RTC_SRAM_Demo finished! ###\n")
