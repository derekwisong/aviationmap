#!/usr/bin/env python

from ledvfrmap.map import LedMap

import logging
import threading
import time
import json
import yaml

import argparse
parser = argparse.ArgumentParser(description="LED VFR Map")
parser.add_argument('--config', type=str, dest='config', default='config.yml',
                    help="Configuration file path")
parser.add_argument('--verbose', action='store_const', const=True,
                    dest='verbose', help="Turn on verbose output")
args = parser.parse_args()

log_level = logging.DEBUG if args.verbose else logging.INFO
log_format = '[%(asctime)s %(name)s %(levelname)s] %(message)s'
logging.basicConfig(level=log_level,
                    format=log_format)
logger = logging.getLogger(__name__)

logger.info("Reading configuration")
with open(args.config) as config_file:
    config = yaml.load(config_file, Loader=yaml.Loader)
    try:
        map = LedMap(config)
    except:
        logger.exception("Problem loading map")
        exit(1)
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    logger.info("Stopping map...")
    map.stop()
