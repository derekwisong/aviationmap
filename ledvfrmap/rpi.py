import RPi.GPIO as GPIO
import Adafruit_WS2801
import Adafruit_GPIO.SPI as SPI
import threading
import logging

class LEDController(threading.Thread):
    def __init__(self, pixel_count, clock_pin, data_pin):
        threading.Thread.__init__(self)
        self.pixels = Adafruit_WS2801.WS2801Pixels(pixel_count, clk=clock_pin,
                                                   do=data_pin)
        self.all_off()
        self.changed = False
        self.stopped = threading.Event()

    def stop(self):
        self.stopped.set()

    def all_off(self):
        self.pixels.clear()
        self.pixels.show()
    
    def set_rgb(self, pixel_number, r, g, b):
        self.pixels.set_pixel_rgb(pixel_number, r, g, b)
        self.changed = True
    
    def get_rgb(self, pixel_number):
        return self.pixels.get_pixel_rgb(pixel_number)

    def run(self):
        logger = logging.getLogger(__name__)
        while not self.stopped.wait(0.5):
            if self.changed:
                logger.info("LED color(s) changed, showing the new color(s)")
                self.pixels.show()
                self.changed = False
