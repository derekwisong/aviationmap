#!/usr/bin/env python

"""
Tool for obtaining Aviation Weather from aviationweather.gov using
the Text Data Server (TDS)
"""

import requests
import logging
import xml.etree.ElementTree as ET
import datetime

TDS = 'https://www.aviationweather.gov/adds/dataserver_current/httpparam'

def item_timestamp(item, fmt="%Y-%m-%dT%H:%M:%SZ"):
    try:
        text = item.text
        timestamp = datetime.datetime.strptime(text, fmt)
        return timestamp
    except ValueError:
        return None

def item_text(item):
    try:
        return item.text.strip()
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

def item_int(item):
    try:
        return int(item.text)
    except AttributeError:
        return None
    except ValueError:
        return None
    except TypeError:
        return None

def item_attrib(item):
    try:
        return item.attrib
    except AttributeError:
        return None

def parse_xml_metar(xml_data):
    root = ET.fromstring(xml_data)
    stations = {}
    for metar in root.iter('METAR'):
        id = metar.find('station_id').text
        sky = item_attrib(metar.find('sky_condition'))
        data = {
            'station_id': id,
            'raw_text': item_text(metar.find('raw_text')),
            'observation_time': item_timestamp(metar.find('observation_time')),
            'latitude': item_float(metar.find('latitude')),
            'longitude': item_float(metar.find('longitude')),
            'temp_c': item_float(metar.find('temp_c')),
            'dewpoint_c': item_float(metar.find('dewpoint_c')),
            'wind_dir_degrees': item_int(metar.find('wind_dir_degrees')),
            'wind_speed_kt': item_int(metar.find('wind_speed_kt')),
            'wind_gust_kt': item_int(metar.find('wind_gust_kt')),
            'visibility_statute_mi': item_float(metar.find('visibility_statute_mi')),
            'altim_in_hg': item_float(metar.find('altim_in_hg')),
            'sea_level_pressure_mb': item_float(metar.find('sea_level_pressure_mb')),
            'quality_control_flags': item_text(metar.find('quality_control_flags')),
            'wx_string': item_text(metar.find('wx_string')),
            'flight_category': item_text(metar.find('flight_category')),
            'elevation_m': item_float(metar.find('elevation_m')),
            'maxT_c': item_float(metar.find('maxT_c')),
            'minT_c': item_float(metar.find('minT_c')),
            'maxT24hr_c': item_float(metar.find('maxT24hr_c')),
            'minT24hr_c': item_float(metar.find('minT24hr_c')),
            'precip_in': item_float(metar.find('precip_in')),
            'pcp3hr_in': item_float(metar.find('pcp3hr_in')),
            'pcp6hr_in': item_float(metar.find('pcp6hr_in')),
            'snow_in': item_float(metar.find('snow_in')),
            'vert_vis_ft': item_int(metar.find('vert_vis_ft')),
            'metar_type': item_text(metar.find('metar_type')),
            'raw_xml': xml_data
        }
        try:
            data['cloud_base_ft_agl'] = float(sky['cloud_base_ft_agl'])
        except KeyError:
            data['cloud_base_ft_agl'] = None
        try:
            data['sky_cover'] = sky['sky_cover']
        except KeyError:
            data['sky_cover'] = None

        stations[id] = data

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
