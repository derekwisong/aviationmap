#!/usr/bin/env python

"""
Tool for obtaining Aviation Weather from aviationweather.gov using
the Text Data Server (TDS)
"""

import requests
import logging
import xml.etree.ElementTree as ET

TDS = 'https://www.aviationweather.gov/adds/dataserver_current/httpparam'

def item_text(item):
    try:
        return item.text
    except AttributeError:
        return None

def item_float(item):
    try:
        return float(item.text)
    except AttributeError:
        return None
    except ValueError:
        return None
    except TypeError:
        return None

def parse_xml_metar(xml_data):
    root = ET.fromstring(xml_data)
    stations = {}
    for metar in root.iter('METAR'):
        id = metar.find('station_id').text
        stations[id] = {
            'id': id,
            'time': item_text(metar.find('observation_time')),
            'latitude': item_text(metar.find('latitude')),
            'longitude': item_text(metar.find('longitude')),
            'temp': item_float(metar.find('temp_c')),
            'dewpoint': item_float(metar.find('dewpoint_c')),
            'wind_dir': item_float(metar.find('wind_dir_degrees')),
            'wind_speed': item_float(metar.find('wind_speed_kt')),
            'visibility': item_float(metar.find('visibility_statute_mi')),
            'altimiter': item_float(metar.find('altim_in_hg')),
            'pressure': item_float(metar.find('sea_level_pressure_mb')),
            'sky': metar.find('sky_condition').attrib,
            'category': item_text(metar.find('flight_category')),
            'elevation': item_float(metar.find('elevation_m'))
        }

    return stations

def get_latest_metar(stations):
    logger = logging.getLogger(__name__)
    logger.info("Requesting latest METAR data")
    opts = {'datasource': 'metars',
            'requestType': 'retrieve',
            'format': 'xml',
            'stationString': ",".join(stations),
            'mostRecentForEachStation': 'constraint',
            'hoursBeforeNow': '1.75'}

    response = requests.get(TDS, params=opts, timeout=20.0)
    
    if response.status_code == 200:
        return parse_xml_metar(response.text)
    else:
        raise RuntimeError("Unable to retreive METAR")

def get_flight_categories(stations):
    """
    Get flight categories (VFR, MVFR, IFR, LIFR) for a list of stations.
    https://www.aviationweather.gov/metar/help?page=plot#fltcat
    """

    metars = get_latest_metar(stations)
    categories = {station: v.get('category') for station,v in metars.items()}
    return categories
