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
    map = LedMap(config)

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    logger.info("Stopping map...")
    map.stop()
