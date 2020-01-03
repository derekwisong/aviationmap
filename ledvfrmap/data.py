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
        except requests.exceptions.RequestException:
            logger.exception("Problem requesting METAR data")

    def run(self):
        self.update()

        while not self.stopped.wait(60):
            self.update()

    def stop(self):
        self.stopped.set()


class OpenSkyData:
    def __init__(self):
        from opensky_api import OpenSkyApi
        self.api = OpenSkyApi()
        # bounding box around the USA
        self.bbox = (23.346528, 50.579747, -128.466799, -64.262697)
        self.states = []

    def get_states(self):
        states = []
        before_query = datetime.datetime.utcnow()
        api_states = self.api.get_states(bbox=self.bbox)
        after_query = datetime.datetime.utcnow()

        if api_states.states:
            for state in api_states.states:
                datum = {'utctime_before_query': before_query,
                         'utctime_after_query': after_query,
                         'icao24': state.icao24,
                         'callsign': state.callsign,
                         'origin_country': state.origin_country,
                         'time_position': state.time_position,
                         'last_contact': state.last_contact,
                         'longitude': state.longitude,
                         'latitude': state.latitude,
                         'geo_altitude': state.geo_altitude,
                         'on_ground': state.on_ground,
                         'velocity': state.velocity,
                         'heading': state.heading,
                         'vertical_rate': state.vertical_rate,
                         'sensors': state.sensors,
                         'baro_altitude': state.baro_altitude,
                         'squawk': state.squawk,
                         'spi': state.spi,
                         'position_source': state.position_source
                         }
                states.append(datum)

        return states
