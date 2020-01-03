#!/usr/bin/env python

import pkg_resources
from misc.faa import Airport
import yaml
import time

input_config_file = pkg_resources.resource_filename('ledvfrmap', 'config.yml')
output_config_file = pkg_resources.resource_filename('ledvfrmap', 'config.yml')

with open(input_config_file, 'r') as cfg:
    config = yaml.load(cfg, Loader=yaml.Loader)

data = []
fails = []

for station in config['stations']:
    code = station['code']

    if 'latitude' in station and 'longitude' in station:
        print(f"Skipping {code}, already have latitude and longitude")
        continue

    airport = Airport(code)
    tries = 5

    while tries > 0:
        try:
            print(f"Querying for station {code}")
            airport.query()
            summary = airport.summary()
            station['latitude'] = summary['coords'][0]
            station['longitude'] = summary['coords'][1]
            with open(output_config_file, 'w') as cfg:
                cfg.write(yaml.dump(config))
            break
        except Exception as e:
            tries -= 1
            if tries == 0:
                print(f"Unable to get data for {code}: " + str(e))
                fails.append(station)
                break
        finally:
            time.sleep(2)

if fails:
    print("The following items failed")
    print(fails)