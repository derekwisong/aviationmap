#!/usr/bin/env python

import yaml
import json
import pkg_resources
import misc.faa as faa
import time

def get_airport_codes():
    with open(pkg_resources.resource_filename('ledvfrmap', 'config.yml'), 'rb') as cfg:
        config = yaml.load(cfg, Loader=yaml.Loader)

    return [station['code'] for station in config['stations']]

def get_airport_data(code):
    airport = faa.Airport(code)
    airport.query()
    summary = airport.summary()

    data = {
        'latitude': summary['coords'][0],
        'longitude': summary['coords'][1]}

    return data

def build_data():
    dat = {}
    for code in get_airport_codes():
        print(f"Getting data for {code}")
        tries = 3
        while tries > 0:
            try:
                dat[code] = get_airport_data(code)
                break
            except Exception as e:
                tries -= 1
                time.sleep(3)
            finally:
                time.sleep(1)
    return dat

def write_data(data, output):
    with open(output, 'w') as datfile:
        print(f"Writing to {output}")
        json.dump(data, datfile)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('outfile', type=str, help="output file path")
    args = parser.parse_args()
    data = build_data()
    write_data(data, args.outfile)