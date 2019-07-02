#!/usr/bin/env python

import threading

from . import data
from .led import StationLed

category_colors = {'VFR': (0, 255, 0),
                   'MVFR': (0, 0, 255),
                   'IFR': (255, 0, 0),
                   'LIFR': (255, 0, 255)}

class Station(threading.Thread):
    def __init__(self, name, led_number, category_data):
        threading.Thread.__init__(self)
        self.led = StationLed(name, led_number)
        self.name = name
        self.number = led_number
        self.category = None
        self.category_data = category_data
        self._stopped = threading.Event()

    def set_color(self, r, g, b):
        self.led.set_rgb(r, g, b)
    
    def run(self):
        while not self._stopped.wait(1):
            self.category = self.category_data.category(self.name)

            try:
                color = category_colors[self.category]
            except KeyError:
                color = (0, 0, 0)
            
            self.set_color(*color)
    
    def stop(self):
        self._stopped.set()

class LedMap:
    def __init__(self, stations):
        self.stations = {}
        self.category_data = data.FlightCategoryMonitor()

        for station in stations:
            name = station['name']
            num = station['led']

            self.category_data.add_station(name)
            station = Station(name, num, self.category_data)
            station.start()
            self.stations[name] = station
        
        self.category_data.start()


    def set_all_stations_color(self, r, g, b):
        for station in self.stations.values():
            station.set_color(r, g, b)
    
    def stop(self):
        self.category_data.stop()

        for station in self.stations.values():
            station.stop()
