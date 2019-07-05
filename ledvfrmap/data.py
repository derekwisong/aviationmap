#!/usr/bin/env python

import threading
import logging
import datetime
import avwx.tds

class MetarMonitor(threading.Thread):
    def __init__(self, stations=None):
        threading.Thread.__init__(self)

        if stations is not None:
            self.stations = set(stations)
        else:
            self.stations = set()

        self.metar = {}
        self.last_update = None
        self.stopped = threading.Event()

    def add_station(self, station):
        self.stations.add(station)
    
    def get_metar(self, station):
        return self.metar.get(station)
    
    def get_metar_value(self, station, item):
        metar = self.get_metar(station)
        if metar:
            return metar.get(item)
        else:
            return None

    def update(self):
        logger = logging.getLogger(__name__)

        try:
            self.metar = avwx.tds.get_latest_metar(self.stations)
            self.last_update = datetime.datetime.utcnow()
        except:
            logger.exception("Unable to update metar data")

    def run(self):
        self.update()

        while not self.stopped.wait(60):
            self.update()

    def category(self, station):
        return self.get_metar_value(station, 'category')
    
    def stop(self):
        self.stopped.set()
