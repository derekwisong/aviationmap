import RPi.GPIO as GPIO
import Adafruit_WS2801
import Adafruit_GPIO.SPI as SPI

class LEDController:
    def __init__(self, pixel_count, clock_pin, data_pin):
        self.pixels = Adafruit_WS2801.WS2801Pixels(pixel_count, clk=clock_pin,
                                                   do=data_pin)

    def all_off(self):
        self.pixels.clear()
        self.pixels.show()
    
    def set_rgb(self, pixel_number, r, g, b, show=True):
        self.pixels.set_pixel_rgb(pixel_number, r, g, b)

        if show:
            self.pixels.show()
    
    def get_rgb(self, pixel_number):
        return self.pixels.get_pixel_rgb(pixel_number)
