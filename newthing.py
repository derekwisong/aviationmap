import logging
import time
import yaml

from avwx.tds import get_latest_metar

logger = logging.getLogger(__name__)

def load_config(config_file):
    with open(config_file, 'rb') as config:
        return yaml.load(config, Loader=yaml.Loader)

def set_led(led, red, green, blue):
    pass

def update(stations):
    metars = get_latest_metar([_['code'] for _ in stations])

    for station in stations:
        code = station['code']
        led = station['led']
        name = station['name']

        logger.info(f"Updating {name} ({code})")
        set_led(led, 0, 0, 0)

def main():
    config = load_config('config.yml')
    stations = config['stations']

    while True:
        update(stations)
        time.sleep(10)

    [(['code']) for _ in config['stations']]


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()