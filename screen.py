import board
import busio
from adafruit_ssd1306 import SSD1306_I2C
from PIL import Image, ImageDraw, ImageFont
import clarity_IPC


import pi_servo_hat
import time

# I2C setup via Qwiic
i2c = busio.I2C(board.SCL, board.SDA)

# SSD1306 setup (128x64 display with I2C address 0x3C)
oled = SSD1306_I2C(128, 64, i2c, addr=0x3C)


def show_text(text):
    oled.fill(0)
    oled.show()
    # Create a blank image for drawing
    width = oled.width
    height = oled.height
    image = Image.new("1", (width, height))
    draw = ImageDraw.Draw(image)

    # Draw text
    font = ImageFont.load_default()
    draw.text((0, 0), text, font=font, fill=255)

    # Display the image on the OLED
    oled.image(image)
    oled.show()


def show_image(path):
    image = Image.open("path_to_image.png")
    oled.image(image)
    oled.show()
