#!/usr/bin/env python

import ledvfrmap.led as led
import logging
import threading
import time
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
stop = threading.Event()
monitor = led.StationMonitor(stop)

logger.info("Reading configuration")
with open('config.json') as config_file:
    data = json.load(config_file)
    for station in data["stations"]:
        s = led.StationLed(station["name"], station["led"])
        monitor.add_station(s)

monitor.start()

try:
    monitor.join()
except KeyboardInterrupt:
    logger.info("Stopping monitor...")
    stop.set()