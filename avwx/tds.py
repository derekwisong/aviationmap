#!/usr/bin/env python

"""
Tool for obtaining Aviation Weather from aviationweather.gov using
the Text Data Server (TDS)
"""

import requests
import xml.etree.ElementTree as ET

TDS = 'https://www.aviationweather.gov/adds/dataserver_current/httpparam'

def parse_xml_metar(xml_data):
    root = ET.fromstring(xml_data)
    stations = {}
    for metar in root.iter('METAR'):
        id = metar.find('station_id').text
        stations[id] = {
            'id': id,
            'time': metar.find('observation_time').text,
            'latitude': metar.find('latitude').text,
            'longitude': metar.find('longitude').text,
            'temp': metar.find('temp_c'),
            'dewpoint': metar.find('dewpoint_c').text,
            'wind_dir': metar.find('wind_dir_degrees').text,
            'wind_speed': metar.find('wind_speed_kt').text,
            'visibility': metar.find('visibility_statute_mi').text,
            'altimiter': metar.find('altim_in_hg').text,
            'pressure': metar.find('sea_level_pressure_mb').text,
            'sky': metar.find('sky_condition').attrib,
            'category': metar.find('flight_category').text,
            'elevation': metar.find('elevation_m').text
        }

    return stations

def get_latest_metar(stations):
    opts = {'datasource': 'metars',
            'requestType': 'retrieve',
            'format': 'xml',
            'stationString': ",".join(stations),
            'mostRecentForEachStation': 'constraint',
            'hoursBeforeNow': '1.75'}

    response = requests.get(TDS, params=opts)

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
