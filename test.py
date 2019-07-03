#!/usr/bin/env python

from ledvfrmap.map import LedMap

import logging
import threading
import time
import json
import yaml

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Reading configuration")
with open('config.yml') as config_file:
    config = yaml.load(config_file, Loader=yaml.Loader)
    stations = config['stations']
    num_leds = config['leds']

    if config['controller'] == 'test':
        from ledvfrmap.led import TestLEDController
        controller = TestLEDController(num_leds)   
    else:
        from ledvfrmap.rpi import LEDController
        controller = LEDController(num_leds, config['rpi']['clock_pin'],
                                   config['rpi']['data_pin'])

    map = LedMap(stations, controller)

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    logger.info("Stopping map...")
    map.stop()
