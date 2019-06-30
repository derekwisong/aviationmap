#!/usr/bin/env python

import threading
import logging
import time
import requests.exceptions
import avwx.tds

class StationLed:
    def __init__(self, name, number):
        self.name = name
        self.number = number
        self.category = None
        self.color = ()

    def set_rgb(self, r, g, b):
        logger = logging.getLogger(__name__)
        self.color = (r, g, b)
        logger.info("Set {} ({}) color to {}".format(self.name, self.number, self.color))

    def set_category(self, category):
        logger = logging.getLogger(__name__)
        logger.info("Station category {} is {}".format(self.name, category))
    
        if category == 'VFR':
           self.set_rgb(0, 255, 0)
        elif category == 'MVFR':
            self.set_rgb(0, 0, 255)
        elif category == 'IFR':
            self.set_rgb(255, 0, 0)
        elif category == 'LIFR':
            self.set_rgb(255, 0, 255)
        else:
            logger.warn("Unknown category: {}".format(category))


class StationMonitor(threading.Thread):
    def __init__(self, event):
        threading.Thread.__init__(self)
        self.stopped = event
        self.stations = {}
        self.station_names = set()
    
    def add_station(self, station):
        self.stations[station.name] = station
        self.station_names.add(station.name)
    
    def remove_station(self, station):
        del self.stations[station.name]
        self.station_names.remove(station.name)

    def update_flight_categories(self):
        logger = logging.getLogger(__name__)

        try:
            categories = avwx.tds.get_flight_categories(self.station_names)
        except requests.exceptions.ConnectTimeout:
            logger.exception("Timeout getting flight category data")
            return
        except requests.exceptions.ConnectionError:
            logger.exception("Error getting flight category data")
            return


        for station_name, category in categories.items():
            try:
                station = self.stations[station_name]
            except KeyError:
                # unexpected station
                continue

            station.set_category(category)
            

    def run(self):
        while not self.stopped.wait(1):
            self.update_flight_categories()

            for i in range(60):
                if self.stopped.wait(1):
                    break