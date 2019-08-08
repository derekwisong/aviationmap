#!/usr/bin/env python

"""
LedController should run a timer that checks each LED
and updates the displayed color.
"""

import threading
import logging
import yaml
import time
import os

from . import data

class Color:
    def __init__(self, r, g, b):
        self.r = r
        self.g = g
        self.b = b
    
    def rgb(self):
        return (self.r, self.g, self.b)
    
    def __str__(self):
        return "Color {}".format((self.r, self.g, self.b))


class Led:
    def __init__(self, number):
        self.number = number
        self._color = Color(0, 0, 0)
        self._on = True
    
    def is_on(self):
        return self._on

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

    def __str__(self):
        return "Led ({n}, {onoff}): {color}".format(n=self.number,
            onoff="On" if self._on else "Off",
            color=self._color)

class Airport:
    def __init__(self, icao_id, led):
        self._icao_id = icao_id
        self.led = led
    
    @property
    def icao_id(self):
        return self._icao_id

    def __str__(self):
        return self.icao_id


class LedController(threading.Thread):
    def __init__(self, leds, rate=10):
        threading.Thread.__init__(self)
        self.leds = leds
        self._stopped = threading.Event()
        self._state = {}
        self._changed = []
        self.rate = rate
    
    @property
    def changed(self):
        return self._changed

    def stop(self):
        self._stopped.set()
    
    def run(self):
        sleeptime = 0
        
        while not self._stopped.wait(sleeptime):
            start = time.time()
            for led in self.leds:
                self.update_led(led)

            self.show()
            self._changed.clear()
            end = time.time()
            sleeptime = max(0.05, (1 - (end-start) * self.rate) / self.rate)


    def update_led(self, led):
        new_color = led.color.rgb()
        new_state = led.is_on()

        is_new = False

        if led not in self._state:
            is_new = True
        else:
            if new_color != self._state[led]['color']:
                is_new = True
            elif new_state != self._state[led]['state']:
                is_new = True
        
        if is_new:
            self._state[led] = {'color': new_color, 'state': new_state}
            self.changed.append(led)

    def show(self):
        pass


class ConsoleLedController(LedController):
    def __init__(self, leds):
        LedController.__init__(self, leds)

    def show(self):
        logger = logging.getLogger(__name__)
        for led in self.changed:
            logger.info("Showing LED {}".format(led))


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
        for led in self.changed:
            color = self._state[led]['color']
            logger.info("Showing LED {}".format(led))

            if self._state['led']['state']:
                self.pixels.set_pixel_rgb(led.number, *color)
            else:
                self.pixels.set_pixel_rgb(led.number, 0, 0, 0)

        if len(self.changed) > 0:
            self.pixels.show()


class LedMap:
    def __init__(self, config_file):
        self._airports = {}
        self._led_controller = None

        with open(config_file, 'rb') as config:
            self.config = yaml.load(config, Loader=yaml.Loader)
    
        self._data = data.Data(self.config['database'])
        self._setup_airports()
        self._setup_led_controller()

        self._data.start()

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
            self._data.add_station(code)

        self._airports = airports

    def stop(self):
        self._led_controller.stop()
        self._data.stop()
        self._led_controller.join()

    @property
    def airports(self):
        return self._airports
    
    def get_airport(self, code):
        return self.airports[code]

    @property
    def led_controller(self):
        return self._led_controller
