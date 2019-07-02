#!/usr/bin/env python

import threading
import logging

from . import data
from .led import StationLed

category_colors = {'VFR': (0, 255, 0),
                   'MVFR': (0, 0, 255),
                   'IFR': (255, 0, 0),
                   'LIFR': (255, 0, 255)}

class Station(threading.Thread):
    def __init__(self, code, name, led_number, category_data):
        threading.Thread.__init__(self)
        self.category_data = category_data

        self.led = StationLed(led_number)

        self.code = code
        self.name = name
        self.number = led_number

        self.category = None
        self.category_timestamp = None

        self._stopped = threading.Event()

    def set_color(self, r, g, b):
        self.led.set_rgb(r, g, b)
    
    def run(self):
        logger = logging.getLogger(__name__)
        while not self._stopped.wait(1):
            color = self.led.color
            category = self.category_data.category(self.code)

            # TODO: check category timestamp for dead data

            if category != self.category:
                # category has changed
                self.category = category
                self.category_timestamp = self.category_data.last_update
                logger.info("{} flight category is now {}".format(self.code, category))
                
                try:
                    color = category_colors[category]
                except KeyError:
                    color = (0, 0, 0)

            if color != self.led.color:
                self.set_color(*color)
    
    def stop(self):
        self._stopped.set()

class LedMap:
    def __init__(self, stations):
        self.stations = {}
        self.category_data = data.FlightCategoryMonitor()

        for station in stations:
            code = station['code']
            name = station['name']
            num = station['led']

            if code is None or num is None:
                continue

            self.category_data.add_station(code)
            station = Station(code, name, num, self.category_data)
            station.start()
            self.stations[code] = station
        
        self.category_data.start()


    def set_all_stations_color(self, r, g, b):
        for station in self.stations.values():
            station.set_color(r, g, b)
    
    def stop(self):
        self.category_data.stop()

        for station in self.stations.values():
            station.stop()
