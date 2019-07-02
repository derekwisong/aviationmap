#!/usr/bin/env python

import threading
import avwx.tds

class FlightCategoryMonitor(threading.Thread):
    def __init__(self, stations=None):
        threading.Thread.__init__(self)

        if stations is not None:
            self.stations = set(stations)
        else:
            self.stations = set()

        self.categories = {}
        self.stopped = threading.Event()

    def add_station(self, station):
        self.stations.add(station)

    def update(self):
        self.categories = avwx.tds.get_flight_categories(self.stations)
        
    def run(self):
        self.update()

        while not self.stopped.wait(60):
            self.update()

    def category(self, station):
        return self.categories.get(station)
    
    def stop(self):
        self.stopped.set()
