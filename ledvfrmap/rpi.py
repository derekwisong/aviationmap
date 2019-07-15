import RPi.GPIO as GPIO
import Adafruit_WS2801
import Adafruit_GPIO.SPI as SPI
import threading
import logging
import time

is_setup = False

BUTTON_SHORT_PRESS = 0
BUTTON_LONG_PRESS = 1

class RaspberryPiException(Exception):
    pass

def setup(mode="BCM"):
    global is_setup
    if is_setup:
        raise RaspberryPiException("Raspberry Pi is already setup")

    if mode == "BCM":
        GPIO.setmode(GPIO.BCM)
    else:
        raise ValueError("Unknown mode: {}".format(mode))

    is_setup = True

class Button:
    def __init__(self, led_map, pin, pull="DOWN", long_press_time=5.0, bouncetime=300):
        if not is_setup:
            raise RaspberryPiException("{name} is not setup, call {name}.setup()".format(name=__name__))
        logger = logging.getLogger(__name__)
        logger.info("Setting up button on pin {}".format(pin))
        self.led_map = led_map
        self.long_press_time = long_press_time
        self.pin = pin
        self.bouncetime = bouncetime

        if pull == "DOWN":
            self.pull = GPIO.PUD_DOWN
            self.pressed_input = GPIO.HIGH
        elif pull == "UP":
            self.pull = GPIO.PUD_UP
            self.pressed_input = GPIO.LOW
        else:
            raise RaspberryPiException("Unknown pull mode: {}".format(pull))

        self.setup()

    def setup(self):
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=self.pull)
        if self.pull == GPIO.PUD_DOWN:
            direction = GPIO.RISING
        else:
            direction = GPIO.FALLING
        GPIO.add_event_detect(self.pin, direction,
                              callback=self.switch_event,
                              bouncetime=self.bouncetime)

    def switch_event(self, channel):
        logger = logging.getLogger(__name__)
        start_time = time.time()

        while GPIO.input(channel) == self.pressed_input:
            pass

        button_time = time.time() - start_time

        if button_time >= self.long_press_time:
            logger.info("Button pressed for a long time: {}".format(button_time))
            self.led_map.toggle_on_off()
        else:
            logger.info("Button pressed quickly: {}".format(button_time))

class LEDController(threading.Thread):
    def __init__(self, pixel_count, clock_pin, data_pin, clear=True):
        threading.Thread.__init__(self)
        self.pixels = Adafruit_WS2801.WS2801Pixels(pixel_count,
                                                   clk=clock_pin,
                                                   do=data_pin)
        if clear:
            self.pixels.clear()
            self.pixels.show()

        self.pixel_count = pixel_count
        self.pixel_color = {i:(0, 0, 0) for i in range(pixel_count)}
        self.pixel_state = {i:True for i in range(pixel_count)}
        self.changed = False
        self.stopped = threading.Event()
        self.lock = threading.Lock()

    def stop(self):
        self.stopped.set()
        self.lock.acquire()
        try:
            self.pixels.clear()
            self.pixels.show()
        finally:
            self.lock.release()

    def all_off(self):
        self.lock.acquire()
        try:
            for i in range(self.pixel_count):
                self.pixel_state[i] = False

            self.pixels.clear()
            self.changed = True
        finally:
            self.lock.release()

    def all_on(self):
        self.lock.acquire()
        try:
            for i in range(self.pixel_count):
                self.pixel_state[i] = True
                color = self.pixel_color[i]
                self.pixels.set_pixel_rgb(i, *color)
            self.changed = True
        finally:
            self.lock.release()

    def is_on(self, pixel_number):
        return self.pixel_state[pixel_number]

    def set_rgb(self, pixel_number, r, g, b):
        self.lock.acquire()
        try:
            current = self.get_rgb(pixel_number)

            if current != (r, g, b):
                self.pixel_color[pixel_number] = (r, g, b)
                if self.is_on(pixel_number):
                    self.pixels.set_pixel_rgb(pixel_number, r, g, b)
                    self.changed = True
        finally:
            self.lock.release()
    
    def get_rgb(self, pixel_number):
        return self.pixels.get_pixel_rgb(pixel_number)
        
    def run(self):
        logger = logging.getLogger(__name__)

        while not self.stopped.wait(0.1):
            self.lock.acquire()
            try:
                if self.changed:
                    self.pixels.show()
                    self.changed = False
            finally:
                self.lock.release()
