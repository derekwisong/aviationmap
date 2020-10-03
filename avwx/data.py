#!/usr/bin/env python

import threading
import logging
import datetime
import requests
import avwx.tds
import time

from . import db

class Data:
    def __init__(self, database_conn_str):
        self.airports = set()
        self.database_conn_str = database_conn_str
        self.database = db.Database(database_conn_str)
        self.metar_monitor = MetarMonitor(self.database)
        
    def add_airport(self, airport):
        self.airports.add(airport)
        self.metar_monitor.add_airport(airport)
    
    def start(self):
        self.metar_monitor.start()
    
    def stop(self):
        self.metar_monitor.stop()
        self.metar_monitor.join()

class MetarMonitor(threading.Thread):
    def __init__(self, database):
        threading.Thread.__init__(self)
        self.airports = {}
        self.database = database
        self.metar = {}
        self.last_update = None
        self.stopped = threading.Event()

    def add_airport(self, airport):
        self.airports[airport.icao_id] = airport

    def update(self):
        logger = logging.getLogger(__name__)
        if len(self.airports) == 0:
            return

        try:
            self.metar = avwx.tds.get_latest_metar(self.airports.keys())
            self.database.add_metars(self.metar)
            time.sleep(0.05)
            
            for code, metar in self.metar.items():
                airport = self.airports[code]
                airport.metar = metar
            
            self.last_update = datetime.datetime.utcnow()
        except requests.exceptions.Timeout:
            logger.error("Timeout while getting METAR data")
        except requests.exceptions.ConnectionError:
            logger.error("Unable to connect to METAR data source")
        except:
            logger.exception("Problem handling METAR data")

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

