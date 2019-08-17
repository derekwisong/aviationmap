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
        self._led = led
        self._metar = {}
    
    @property
    def led(self):
        return self._led

    @property
    def icao_id(self):
        return self._icao_id

    @property
    def metar(self):
        return self._metar
    
    @metar.setter
    def metar(self, new_metar):
        self._metar = new_metar

    def metar_value(self, item):
        try:
            return self.metar[item]
        except KeyError:
            return None

    def __str__(self):
        return self.icao_id


class LedController:
    def __init__(self, leds):
        self.leds = leds
        self._state = {}

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

        return is_new

    def show(self):
        pass
    
    def clear(self):
        pass


class ConsoleLedController(LedController):
    def __init__(self, leds):
        LedController.__init__(self, leds)

    def update_led(self, led):
        changed = super().update_led(led)
        if changed:
            logger = logging.getLogger(__name__)
            logger.info("Led changed: {}".format(led))
        return changed
    
    def show(self):
        logger = logging.getLogger(__name__)
        logger.info("Showing LEDs")


class RaspberryPiLedController(LedController):
    def __init__(self, leds, clock_pin, data_pin, clear=True):
        LedController.__init__(self, leds)
        import Adafruit_WS2801
        self.pixels = Adafruit_WS2801.WS2801Pixels(len(leds),
                                                   clk=clock_pin,
                                                   do=data_pin)
        if clear:
            self.clear()
    
    def clear(self):
        logger = logging.getLogger(__name__)
        logger.info("Clearing LEDs")
        self.pixels.clear()
        self.show()

    def update_led(self, led):
        changed = super().update_led(led)
 
        if changed:
            if self._state[led]['state']:
                self.pixels.set_pixel_rgb(led.number, *self._state[led]['color'])
            else:
                self.pixels.set_pixel_rgb(led.number, 0, 0, 0)

            logger = logging.getLogger(__name__)
            logger.debug("Updated LED {}".format(led))

        return changed

    def show(self):
        self.pixels.show()

class LedDisplay(threading.Thread):
    def __init__(self, airports, data, name="LedDisplay"):
        threading.Thread.__init__(self, name=name)
        self._airports = airports
        self._data = data
        self._stopped = threading.Event()
        self._led_controller = None
    
    def stop(self):
        self._stopped.set()
    
    @property
    def stopped(self):
        logger = logging.getLogger(__name__)
        logger.debug("Stopping LedDisplay")
        return self._stopped.is_set()
    
    @property
    def led_controller(self):
        return self._led_controller
    
    @led_controller.setter
    def led_controller(self, controller):
        self._led_controller = controller

class FlightCategoryDisplay(LedDisplay):
    cat_colors = {'VFR': Color(0, 255, 0),
                  'MVFR': Color(0, 0, 255),
                  'IFR': Color(255, 0, 0),
                  'LIFR': Color(255, 0, 255)}

    def __init__(self, airports, data, gust_alert=None):
        LedDisplay.__init__(self, airports, data, name="FlightCategoryDisplay")
        self.gust_alert = gust_alert
    
    @staticmethod
    def get_category_color(category):
        if category in FlightCategoryDisplay.cat_colors:
            return FlightCategoryDisplay.cat_colors[category]
        else:
            return Color(0, 0, 0)
    
    def update(self):
        changed = False
        for airport in self._airports:
            flight_category = airport.metar_value('flight_category')
            airport.led.color = FlightCategoryDisplay.get_category_color(flight_category)
            changed |= self.led_controller.update_led(airport.led)

        if changed:
            self.led_controller.show()

    def run(self):
        self.update()

        while not self._stopped.wait(0.1):
            self.update()

class LedMap:
    def __init__(self, config_file):
        self._display = None
        self._airports = {}
        self._led_controller = None

        with open(config_file, 'rb') as config:
            self.config = yaml.load(config, Loader=yaml.Loader)
    
        self._data = data.Data(self.config['database'])
        self._setup_airports()
        self._setup_led_controller()

        self._data.start()
        self.set_display(self.config['display'])

    def _setup_led_controller(self):
        leds = [airport.led for airport in self.airports.values()]
        controller = self.config['controller']

        if controller == 'console':
            self._led_controller = ConsoleLedController(leds)
        elif controller == 'rpi':
            clock_pin = self.config['rpi']['clock_pin']
            data_pin = self.config['rpi']['data_pin']
            self._led_controller = RaspberryPiLedController(leds, clock_pin, data_pin)
        else:
            raise Exception("Unknown LED controller: {}".format(controller))

    def _setup_airports(self):
        airports = {}

        for airport_info in self.config['stations']:
            code = airport_info['code']
            led = Led(airport_info['led'])
            airport = Airport(code, led)
            airports[code] = airport
            self._data.add_airport(airport)

        self._airports = airports

    def stop(self):
        self._data.stop()
        self._display.stop()
        self._display.join()
        self._led_controller.clear()

    def set_display(self, display):
        if self._display is not None:
            self._display.stop()
            self._display.join()
        
        if type(display) == str:
            if display == 'flight_category':
                gust_level = int(self.config['modes']['flight_category']['gust_pulse'])
                self._display = FlightCategoryDisplay(self.airports.values(), self._data, gust_alert=gust_level)
            else:
                raise Exception("Unknown display: {}".format(self.config['display']))
        else:
            self._display = display

        self._display.led_controller = self.led_controller
        self._display.start()


    @property
    def airports(self):
        return self._airports
    
    def get_airport(self, code):
        return self.airports[code]

    @property
    def led_controller(self):
        return self._led_controller
