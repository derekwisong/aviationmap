#!/usr/bin/env python

"""
LedController should run a timer that checks each LED
and updates the displayed color.
"""

import threading
import logging
import yaml


class Color:
    def __init__(self, r, g, b):
        self.r = r
        self.g = g
        self.b = b
    
    def rgb(self):
        return (self.r, self.g, self.b)


class Led:
    def __init__(self, number):
        self.number = number
        self._color = Color(0, 0, 0)
        self._on = True
    
    def on(self):
        self._on = True
    
    def off(self):
        self._on = False
    
    def toggle(self):
        if self._on:
            self.off()
        else:
            self.on()
    
    @property
    def color(self):
        return self._color
    
    @color.setter
    def color(self, color):
        self._color = color


class Airport:
    def __init__(self, icao_id, led):
        self.icao_id = icao_id
        self.led = led


class LedController(threading.Thread):
    def __init__(self, leds):
        threading.Thread.__init__(self)
        self.leds = leds
        self._stopped = threading.Event()
        self.colors = {}
        self.changed = []
    
    def stop(self):
        self._stopped.set()
    
    def run(self):
        while not self._stopped.wait(0.1):
            for led in self.leds:
                self.update_led(led)

            self.show()

    def update_led(self, led):
        new_color = led.color.rgb()
        is_new = False
        logger = logging.getLogger(__name__)
        if led.number not in self.colors:
            is_new = True
        else:
            if new_color != self.colors[led.number]:
                is_new = True
        
        if is_new:
            self.colors[led.number] = new_color
            self.changed.append(led.number)
            logger.info("LED {} changed to {}".format(led.number, new_color))


    def show(self):
        pass


class ConsoleLedController(LedController):
    def __init__(self, leds):
        LedController.__init__(self, leds)

    def show(self):
        logger = logging.getLogger(__name__)
        for led_number in self.changed:
            logger.info("LED {} is now {}".format(led_number, self.colors[led_number]))

        self.changed = []    


class RaspberryPiLedController(LedController):
    def __init__(self, leds, clock_pin, data_pin, clear=True):
        LedController.__init__(self, leds)
        import RPi.GPIO as GPIO
        import Adafruit_WS2801
        import Adafruit_GPIO.SPI as SPI
        self.pixels = Adafruit_WS2801.WS2801Pixels(len(leds),
                                                   clk=clock_pin,
                                                   do=data_pin)
        if clear:
            self.pixels.clear()
            self.show()
        
    def show(self):
        logger = logging.getLogger(__name__)
        for led_number in self.changed:
            logger.info("LED {} is now {}".format(led_number, self.colors[led_number]))
            self.pixels.set_pixel_rgb(led_number, *self.colors[led_number])
       
        if len(self.changed) > 0:
            self.pixels.show()

        self.changed = []


class LedMap:
    def __init__(self, config_file):
        self._airports = {}
        self._led_controller = None

        with open(config_file, 'rb') as config:
            self.config = yaml.load(config, Loader=yaml.Loader)
    
        self._setup_airports()
        self._setup_led_controller()

    def _setup_led_controller(self):
        leds = [airport.led for airport in self.airports.values()]
        self._led_controller = ConsoleLedController(leds)
        self._led_controller.start()

    def _setup_airports(self):
        airports = {}

        for airport_info in self.config['stations']:
            code = airport_info['code']
            led = Led(airport_info['led'])
            airport = Airport(code, led)
            airports[code] = airport

        self._airports = airports

    @property
    def airports(self):
        return self._airports
    
    def get_airport(self, code):
        return self.airports[code]

    @property
    def led_controller(self):
        return self._led_controller
