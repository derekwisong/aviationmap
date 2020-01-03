#!/usr/bin/env python

"""
LedController should run a timer that checks each LED
and updates the displayed color.
"""

import threading
import logging
import yaml

from collections import defaultdict

from . import data
from . import geo
from . import led


class Color:
    def __init__(self, r, g, b):
        self.r = r
        self.g = g
        self.b = b

    def rgb(self):
        return self.r, self.g, self.b

    def __str__(self):
        return "Color {}".format((self.r, self.g, self.b))


class Led:
    def __init__(self, number, name=None):
        self.number = number
        self._color = Color(0, 0, 0)
        self._on = True
        self._name = name

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
        return "Led ({n}:{name}, {onoff}): {color}".format(n=self.number,
                                                           onoff="On" if self._on else "Off",
                                                           color=self._color,
                                                           name=self._name)


class Airport:
    def __init__(self, icao_id, airport_led):
        self._icao_id = icao_id
        self._led = airport_led
        self._metar = {}
        self._lock = threading.RLock()
        self.neighbors = []
        self.latitude = None
        self.longitude = None

    @property
    def led(self):
        return self._led

    @property
    def icao_id(self):
        return self._icao_id

    @property
    def metar(self):
        with self._lock:
            return self._metar

    @metar.setter
    def metar(self, new_metar):
        with self._lock:
            self._metar = new_metar

    def metar_value(self, item):
        with self._lock:
            try:
                return self.metar[item]
            except KeyError:
                return None

    def distance(self, latitude, longitude):
        return geo.haversine(self.longitude, self.latitude, longitude, latitude, miles=True)

    def flight_category(self):
        return self.metar_value('flight_category')

    def estimate_flight_category(self):
        # estimate the flight category if possible
        ceiling = self.metar_value('cloud_base_ft_agl')
        visibility = self.metar_value('visibility_statute_mi')

        n_neighbors = len(self.neighbors)
        if ceiling is None and n_neighbors > 0:
            neighbor_ceiling = 0
            for neighbor in self.neighbors:
                if neighbor.metar_value('sky_cover') == 'CLR':
                    neighbor_ceiling += 5000
                else:
                    neighbor_ceiling += neighbor.metar_value('cloud_base_ft_agl')

            ceiling = neighbor_ceiling / n_neighbors

        if visibility is None and n_neighbors > 0:
            neighbor_visibility = 0
            neighbor_count = 0
            for neighbor in self.neighbors:
                vis = neighbor.metar_value('visibility_statute_mi')
                if vis is not None:
                    neighbor_visibility += vis
                    neighbor_count += 1

            visibility = neighbor_visibility / neighbor_count

        if ceiling is None or visibility is None:
            flight_category = None
        elif ceiling > 3000 and visibility > 5:
            flight_category = 'VFR'
        elif (1000 <= ceiling <= 3000) and (3 <= visibility <= 5):
            flight_category = 'MVFR'
        elif (500 <= ceiling < 1000) or (1 <= visibility < 3):
            flight_category = 'IFR'
        elif (ceiling < 500) or (visibility < 1):
            flight_category = 'LIFR'
        else:
            flight_category = None

        return flight_category

    def __str__(self):
        return self.icao_id


class LedController:
    def __init__(self, leds):
        self.leds = leds
        self._state = {}

    def off(self):
        for led_instance in self.leds:
            led_instance.off()

    def on(self):
        for led_instance in self.leds:
            led_instance.on()

    def update_led(self, led_instance):
        new_color = led_instance.color.rgb()
        new_state = led_instance.is_on()

        is_new = False

        if led_instance not in self._state:
            is_new = True
        else:
            if new_color != self._state[led_instance]['color']:
                is_new = True
            elif new_state != self._state[led_instance]['state']:
                is_new = True

        if is_new:
            self._state[led_instance] = {'color': new_color, 'state': new_state}

        return is_new

    def show(self):
        pass

    def clear(self):
        pass


class ConsoleLedController(LedController):
    def __init__(self, leds):
        LedController.__init__(self, leds)

    def update_led(self, led_instance):
        changed = super().update_led(led_instance)
        if changed:
            logger = logging.getLogger(__name__)
            logger.info("Led changed: {}".format(led_instance))
        return changed

    def show(self):
        logger = logging.getLogger(__name__)
        logger.info("Showing LEDs")


class RaspberryPiLedController(LedController):
    def __init__(self, leds, clock_pin, data_pin, clear=True):
        LedController.__init__(self, leds)

        try:
            import Adafruit_WS2801
        except ModuleNotFoundError:
            raise

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

    def update_led(self, led_instance):
        changed = super().update_led(led_instance)

        if changed:
            if self._state[led_instance]['state']:
                self.pixels.set_pixel_rgb(led_instance.number, *self._state[led_instance]['color'])
            else:
                self.pixels.set_pixel_rgb(led_instance.number, 0, 0, 0)

            logger = logging.getLogger(__name__)
            logger.info("Updated LED {}".format(led_instance))

        return changed

    def show(self):
        self.pixels.show()


class LedDisplay(threading.Thread):
    def __init__(self, airports, data_instance, name="LedDisplay"):
        threading.Thread.__init__(self, name=name)
        self._airports = airports
        self._data = data_instance
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


class OpenSkyTrafficDisplay(LedDisplay):
    def __init__(self, airports):
        LedDisplay.__init__(self, airports, data, name="OpenSkyTrafficDisplay")
        self.opensky = data.OpenSkyData()
        self.states = None
        self.aircraft_overhead = defaultdict(int)

    def get_color(self, code):
        logger = logging.getLogger(__name__)
        num_aircraft = self.aircraft_overhead[code]
        logger.info(f"There are {num_aircraft} aircraft over {code}")

        if num_aircraft > 100:
            return led.RED
        elif num_aircraft > 70:
            return led.ORANGE
        elif num_aircraft > 20:
            return led.YELLOW
        elif num_aircraft > 10:
            return led.GREEN
        elif num_aircraft > 0:
            return led.BLUE
        else:
            return led.OFF

    def update_traffic_data(self):
        self.states = self.opensky.get_states()
        self.calculate_traffic_stats()

    def closest_airport(self, longitude, latitude):
        min_distance = None
        closest = None

        for airport in self._airports:
            dist = airport.distance(latitude, longitude)

            if min_distance is None or dist < min_distance:
                closest = airport
                min_distance = dist

        return closest, min_distance

    def calculate_traffic_stats(self):
        aircraft_overhead = defaultdict(int)

        for state in self.states:
            closest_airport, distance = self.closest_airport(state['longitude'],
                                                             state['latitude'])
            if distance <= 100:
                aircraft_overhead[closest_airport.icao_id] += 1

        self.aircraft_overhead = aircraft_overhead

    def update(self):
        self.update_traffic_data()
        changed = False

        for airport in self._airports:
            airport.led.color = self.get_color(airport.icao_id)
            changed |= self.led_controller.update_led(airport.led)

        self.led_controller.show()

    def run(self):
        self.update()

        while not self._stopped.wait(60):
            self.update()


class FlightCategoryDisplay(LedDisplay):
    cat_colors = {'VFR': Color(0, 1, 0),
                  'MVFR': Color(0, 0, 1),
                  'IFR': Color(1, 0, 0),
                  'LIFR': Color(1, 0, 1)}

    def __init__(self, airports, data_instance, gust_alert=None):
        LedDisplay.__init__(self, airports, data_instance, name="FlightCategoryDisplay")
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
            if airport.metar_value('observation_time') is None:
                continue

            flight_category = airport.flight_category()

            if flight_category is None:
                flight_category = airport.estimate_flight_category(airport)

            airport.led.color = FlightCategoryDisplay.get_category_color(flight_category)
            changed |= self.led_controller.update_led(airport.led)

        if changed:
            self.led_controller.show()

    def run(self):
        self.update()

        while not self._stopped.wait(5):
            self.update()


def get_airports(config):
    airports = {}

    for airport_info in config['stations']:
        code = airport_info['code']
        airport_led = Led(airport_info['led'], name=code)
        airport = Airport(code, airport_led)
        airport.latitude = airport_info['latitude']
        airport.longitude = airport_info['longitude']
        airports[code] = airport

    for airport_info in config['stations']:
        code = airport_info['code']
        airport = airports[code]
        if 'neighbors' in airport_info:
            airport.neighbors = [airports[neighbor] for neighbor in airport_info['neighbors']]

    return airports


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
        self._airports = get_airports(self.config)
        for airport in self._airports.values():
            self._data.add_airport(airport)

    def on(self):
        self._led_controller.on()

    def off(self):
        self._led_controller.off()

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
            elif display == 'traffic':
                self._display = OpenSkyTrafficDisplay(self.airports.values())
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
