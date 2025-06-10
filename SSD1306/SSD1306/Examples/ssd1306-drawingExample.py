# FILE: SSD1306-example.py 
# AUTHOR: Soldered
# BRIEF:  An example showing various functionalities of the SSD1306 OLED display
# WORKS WITH: Display OLED I2C 0.96" SSD1306 (Blue screen color): www.solde.red/333100
#             Display OLED I2C 0.96" SSD1306 (White screen color): www.solde.red/333099
# LAST UPDATED: 2025-06-10 

# Import required libraries
from ssd1306 import SSD1306  # OLED display driver
import time                  # For delays and timing
import random                # For random number generation
import framebuf              # For frame buffer operations
from machine import I2C,Pin

# Initialize the OLED display
display = SSD1306()  # Creates an instance of the SSD1306 OLED display

# If you aren't using the Qwiic connector, manually enter your I2C pins
# i2c = I2C(0, scl=Pin(22), sda=Pin(21))
# display = SSD1306(i2c)


# Bitmap data for a 16x16 pixel logo
# Stored as a bytearray where each byte represents 8 vertical pixels
LOGO_WIDTH = 16    # Width of the logo in pixels
LOGO_HEIGHT = 16   # Height of the logo in pixels
logo_bmp = bytearray([
    0b00000000, 0b11000000, 0b00000001, 0b11000000, 0b00000001, 0b11000000, 0b00000011, 0b11100000,
    0b11110011, 0b11100000, 0b11111110, 0b11111000, 0b01111110, 0b11111111, 0b00110011, 0b10011111,
    0b00011111, 0b11111100, 0b00001101, 0b01110000, 0b00011011, 0b10100000, 0b00111111, 0b11100000,
    0b00111111, 0b11110000, 0b01111100, 0b11110000, 0b01110000, 0b01110000, 0b00000000, 0b00110000])

def test_draw_line():
    """Demonstrates drawing lines in various directions on the display"""
    display.fill(0)  # Clear display (0 = black, 1 = white)
    
    # Draw lines from top-left corner to right edge, moving down
    for i in range(0, display.width, 4):
        display.line(0, 0, i, display.height-1, 1)  # Draw line (x0,y0 to x1,y1, color)
        display.show()  # Update the display
        time.sleep_ms(1)  # Short delay for animation effect
    
    # Draw lines from top-left corner to bottom edge, moving right
    for i in range(0, display.height, 4):
        display.line(0, 0, display.width-1, i, 1)
        display.show()
        time.sleep_ms(1)
    
    time.sleep_ms(250)  # Pause before next pattern
    display.fill(0)  # Clear display
    
    # Draw lines from bottom-left corner to right edge, moving up
    for i in range(0, display.width, 4):
        display.line(0, display.height-1, i, 0, 1)
        display.show()
        time.sleep_ms(1)
    
    # Draw lines from bottom-left corner to top edge, moving right
    for i in range(display.height-1, -1, -4):  # Count down from bottom
        display.line(0, display.height-1, display.width-1, i, 1)
        display.show()
        time.sleep_ms(1)
    
    time.sleep_ms(250)
    display.fill(0)
    
    # Draw lines from bottom-right corner to left edge, moving up
    for i in range(display.width-1, -1, -4):
        display.line(display.width-1, display.height-1, i, 0, 1)
        display.show()
        time.sleep_ms(1)
    
    # Draw lines from bottom-right corner to top edge, moving left
    for i in range(display.height-1, -1, -4):
        display.line(display.width-1, display.height-1, 0, i, 1)
        display.show()
        time.sleep_ms(1)
    
    time.sleep_ms(250)
    display.fill(0)
    
    # Draw lines from top-right corner to left edge, moving down
    for i in range(0, display.height, 4):
        display.line(display.width-1, 0, 0, i, 1)
        display.show()
        time.sleep_ms(1)
    
    # Draw lines from top-right corner to bottom edge, moving left
    for i in range(0, display.width, 4):
        display.line(display.width-1, 0, i, display.height-1, 1)
        display.show()
        time.sleep_ms(1)
    
    time.sleep(2)  # Final pause before ending function

def test_draw_rect():
    """Demonstrates drawing rectangles of decreasing size"""
    display.fill(0)
    
    # Draw concentric rectangles starting from the outside
    for i in range(0, display.height//2, 2):
        display.rect(i, i, display.width-2*i, display.height-2*i, 1)
        display.show()
        time.sleep_ms(1)
    
    time.sleep(2)

def test_fill_rect():
    """Demonstrates drawing filled rectangles with alternating colors"""
    display.fill(0)
    
    for i in range(0, display.height//2, 3):
        # Draw filled rectangle (inverse alternates between white and black)
        display.fill_rect(i, i, display.width-2*i, display.height-2*i, 1)
        display.show()
        time.sleep_ms(1)
        display.fill_rect(i, i, display.width-2*i, display.height-2*i, 0)  # Inverse
        display.show()
        time.sleep_ms(1)
    
    time.sleep(2)

def test_draw_round_rect():
    """Demonstrates drawing rectangles (simulating rounded corners)"""
    # Note: MicroPython's framebuf doesn't have native rounded rectangles
    # So we use regular rectangles as an approximation
    display.fill(0)
    
    for i in range(0, display.height//2-2, 2):
        display.rect(i, i, display.width-2*i, display.height-2*i, 1)
        display.show()
        time.sleep_ms(1)
    
    time.sleep(2)

def test_fill_round_rect():
    """Demonstrates filled rectangles (simulating rounded corners)"""
    display.fill(0)
    
    for i in range(0, display.height//2-2, 2):
        display.fill_rect(i, i, display.width-2*i, display.height-2*i, 1)
        display.show()
        time.sleep_ms(1)
        display.fill_rect(i, i, display.width-2*i, display.height-2*i, 0)  # Inverse
        display.show()
        time.sleep_ms(1)
    
    time.sleep(2)

def test_draw_triangle():
    """Demonstrates drawing triangles of increasing size"""
    display.fill(0)
    
    for i in range(0, max(display.width, display.height)//2, 5):
        # Draw triangle by connecting three lines
        display.line(display.width//2, display.height//2-i, 
                     display.width//2-i, display.height//2+i, 1)
        display.line(display.width//2-i, display.height//2+i, 
                     display.width//2+i, display.height//2+i, 1)
        display.line(display.width//2+i, display.height//2+i, 
                     display.width//2, display.height//2-i, 1)
        display.show()
        time.sleep_ms(1)
    
    time.sleep(2)

def test_fill_triangle():
    """Demonstrates filled triangles using horizontal lines as an approximation"""
    display.fill(0)
    
    for i in range(max(display.width, display.height)//2, 0, -5):
        # Since MicroPython doesn't have fill_triangle, we approximate with lines
        for y in range(display.height//2-i, display.height//2+i):
            # Calculate left and right x-coordinates for each horizontal line
            x_start = display.width//2 - i + (y - (display.height//2-i))
            x_end = display.width//2 + i - (y - (display.height//2-i))
            display.line(x_start, y, x_end, y, 1)
        display.show()
        time.sleep_ms(1)
        display.fill(0)
        display.show()
        time.sleep_ms(1)
    
    time.sleep(2)

def test_draw_char():
    """Demonstrates drawing text characters on the display"""
    display.fill(0)
    display.text("Hello World!", 0, 0, 1)  # Text, x, y, color
    display.show()
    time.sleep(2)

def test_draw_styles():
    """Demonstrates different text styles and formatting"""
    display.fill(0)
    display.text("Hello, world!", 0, 0, 1)  # Simple text
    display.text(str(3.141592), 0, 10, 1)   # Number conversion
    display.text("0xDEADBEEF", 0, 20, 1)   # Hexadecimal value
    display.show()
    time.sleep(2)

def test_scroll_text():
    """Demonstrates scrolling text horizontally"""
    display.fill(0)
    display.text("scrolling...", 10, 0, 1)
    display.show()
    time.sleep(0.1)
    
    # Scroll text left
    for i in range(0, display.width):
        display.scroll(-1, 0)  # Scroll x by -1, y by 0
        display.show()
        time.sleep_ms(50)
    
    time.sleep(1)
    
def test_draw_bitmap():
    """Demonstrates drawing a bitmap image (the predefined logo)"""
    display.fill(0)
    # Create a frame buffer from our bitmap data
    buf = framebuf.FrameBuffer(logo_bmp, LOGO_WIDTH, LOGO_HEIGHT, framebuf.MONO_HLSB)
    # Blit (copy) the buffer to the display, centered
    display.blit(buf, (display.width - LOGO_WIDTH) // 2, (display.height - LOGO_HEIGHT) // 2)
    display.show()
    time.sleep(1)

# Main program execution starts here
display.fill(0)  # Clear display
display.text("Starting...", 0, 0, 1)  # Show startup message
display.show()
time.sleep(2)  # Pause so user can see the message
    
# Run all demonstration functions
test_draw_line()          # Line drawing demo
test_draw_rect()          # Rectangle outline demo
test_fill_rect()          # Filled rectangle demo
test_draw_round_rect()    # Rounded rectangle demo (approximation)
test_fill_round_rect()    # Filled rounded rectangle demo
test_draw_triangle()      # Triangle outline demo
test_fill_triangle()      # Filled triangle demo
test_draw_char()          # Text drawing demo
test_draw_styles()        # Text formatting demo
test_scroll_text()        # Text scrolling demo
test_draw_bitmap()        # Bitmap drawing demo
    
# Demonstrate display inversion
display.invert(1)  # Invert display colors
time.sleep(1)
display.invert(0)  # Restore normal colors
time.sleep(1)
