import ledvfrmap.map as map

import logging
import os
import time

if __name__ == '__main__':
    import argparse

    logger = logging.getLogger(__name__)

    parser = argparse.ArgumentParser(description="LED VFR Map")
    parser.add_argument('-c', '--config', type=str, dest='config',
                        default='config.yml',
                        help="Configuration file")
    parser.add_argument('-v', '--verbose', action='store_const', const=True,
                        dest='verbose', default=False,
                        help="Show more verbose logging output")
    args = parser.parse_args()

    logfmt = "[%(levelname)s %(asctime)s %(module)s %(threadName)s] %(message)s"
    level = logging.INFO

    if args.verbose:
        level = logging.DEBUG

    logging.basicConfig(format=logfmt, level=level)

    if not os.path.exists(args.config):
        logger.error("Config file {} does not exist".format(args.config))
        exit(1)

    map = map.LedMap(args.config)

    while True:
        try:
            time.sleep(0.5)
        except KeyboardInterrupt:
            break
    
    map.stop()
