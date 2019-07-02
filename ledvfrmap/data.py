#!/usr/bin/env python

import threading
import logging
import datetime
import avwx.tds

class FlightCategoryMonitor(threading.Thread):
    def __init__(self, stations=None):
        threading.Thread.__init__(self)

        if stations is not None:
            self.stations = set(stations)
        else:
            self.stations = set()

        self.categories = {}
        self.last_update = None
        self.stopped = threading.Event()

    def add_station(self, station):
        self.stations.add(station)

    def update(self):
        logger = logging.getLogger(__name__)

        try:
            self.categories = avwx.tds.get_flight_categories(self.stations)
            self.last_update = datetime.datetime.utcnow()
        except:
            logger.exception("Unable to update flight category data")

    def run(self):
        self.update()

        while not self.stopped.wait(60):
            self.update()

    def category(self, station):
        return self.categories.get(station)
    
    def stop(self):
        self.stopped.set()
