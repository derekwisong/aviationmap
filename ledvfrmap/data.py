#!/usr/bin/env python

import threading
import logging
import datetime
import requests
import avwx.tds

from . import db

class Data:
    def __init__(self, database_conn_str):
        self.stations = set()
        self.database_conn_str = database_conn_str
        self.database = db.Database(database_conn_str)
        self.metar_monitor = MetarMonitor(self.database)
        
    def add_station(self, station):
        self.stations.add(station)
        self.metar_monitor.add_station(station)
    
    def get_metar(self, station):
        return self.metar_monitor.get_metar(station)
    
    def get_metar_value(self, station, item):
        return self.metar_monitor.get_metar_value(station, item)

    def start(self):
        self.metar_monitor.start()
    
    def stop(self):
        self.metar_monitor.stop()

class MetarMonitor(threading.Thread):
    def __init__(self, database, stations=None):
        threading.Thread.__init__(self)

        if stations is not None:
            self.stations = set(stations)
        else:
            self.stations = set()
        
        self.database = database
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
        if len(self.stations) == 0:
            return

        try:
            self.metar = avwx.tds.get_latest_metar(self.stations)
            self.database.add_metars(self.metar)
            self.last_update = datetime.datetime.utcnow()
        except requests.exceptions.Timeout:
            logger.error("Timeout while getting METAR data")
        except requests.exceptions.ConnectionError:
            logger.error("Unable to connect to METAR data source")
        except:
            logger.excepion("Problem handling METAR data")

    def run(self):
        self.update()

        while not self.stopped.wait(60):
            self.update()

    def stop(self):
        self.stopped.set()

# https://app.swaggerhub.com/apis/FAA/ASWS/1.1.0

# This returns JSON with status information for KATL
# https://soa.smext.faa.gov/asws/api/airport/status/KATL

# This returns delay information
# https://soa.smext.faa.gov/asws/api/airport/delays
# url = "https://soa.smext.faa.gov/asws/api/airport/delays"                                                                                                                              
# requests.get(url, headers={'accept':'application/json'}).text                                                                                                                          
# '{"status":{"code":200,"info":"OK","count":0},"GroundDelays":{"groundDelay":[],"count":0},"GroundStops":{"groundStop":[],"count":0},"ArriveDepartDelays":{"arriveDepart":[],"count":0},"Closures":{"closure":[],"count":0}}'

