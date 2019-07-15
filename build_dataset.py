import pandas as pd
import avwx.tds as tds
import requests
import os
import logging
import airnav
import time

logging.basicConfig(level=logging.INFO)

states = {
        'AK': 'Alaska',
        'AL': 'Alabama',
        'AR': 'Arkansas',
        'AS': 'American Samoa',
        'AZ': 'Arizona',
        'CA': 'California',
        'CO': 'Colorado',
        'CT': 'Connecticut',
        'DC': 'District of Columbia',
        'DE': 'Delaware',
        'FL': 'Florida',
        'GA': 'Georgia',
        'GU': 'Guam',
        'HI': 'Hawaii',
        'IA': 'Iowa',
        'ID': 'Idaho',
        'IL': 'Illinois',
        'IN': 'Indiana',
        'KS': 'Kansas',
        'KY': 'Kentucky',
        'LA': 'Louisiana',
        'MA': 'Massachusetts',
        'MD': 'Maryland',
        'ME': 'Maine',
        'MI': 'Michigan',
        'MN': 'Minnesota',
        'MO': 'Missouri',
        'MP': 'Northern Mariana Islands',
        'MS': 'Mississippi',
        'MT': 'Montana',
        'NA': 'National',
        'NC': 'North Carolina',
        'ND': 'North Dakota',
        'NE': 'Nebraska',
        'NH': 'New Hampshire',
        'NJ': 'New Jersey',
        'NM': 'New Mexico',
        'NV': 'Nevada',
        'NY': 'New York',
        'OH': 'Ohio',
        'OK': 'Oklahoma',
        'OR': 'Oregon',
        'PA': 'Pennsylvania',
        'PR': 'Puerto Rico',
        'RI': 'Rhode Island',
        'SC': 'South Carolina',
        'SD': 'South Dakota',
        'TN': 'Tennessee',
        'TX': 'Texas',
        'UT': 'Utah',
        'VA': 'Virginia',
        'VI': 'Virgin Islands',
        'VT': 'Vermont',
        'WA': 'Washington',
        'WI': 'Wisconsin',
        'WV': 'West Virginia',
        'WY': 'Wyoming'
}

state_abbrevs = ["@{}".format(_) for _ in states.keys()]


def get_metars(cache=None):
    logger = logging.getLogger(__name__)
    if cache is not None and os.path.exists(cache):
        logger.info("Reading cache: {}".format(cache))
        metar_table = pd.read_pickle(cache)
    else:
        # get all the metars
        metars = {state:tds.get_latest_metar([state]) for state in state_abbrevs}
        metar_table = pd.concat([pd.DataFrame(_.values()) for _ in metars.values()])
        metar_table = metar_table.drop(columns=['raw_xml'])
        front_cols = ['station_id', 'observation_time']
        metar_table = metar_table.reindex(columns=front_cols + [c for c in metar_table.columns.tolist() if c not in front_cols])
        if cache is not None:
            logger.info("Writing cache: {}".format(cache))
            metar_table.to_pickle(cache)
    
    return metar_table

def build_map(metar_table):
    from mpl_toolkits.basemap import Basemap
    import matplotlib.pyplot as plt
    # projection=lcc
    # resolution=None
    # lon_0=-107.0
    m = Basemap(width=5000000,height=4000000,
        projection='lcc', resolution='l',lat_1=45.,lat_2=55,lat_0=40,lon_0=-97.)
    m.shadedrelief()
    m.drawcoastlines()
    m.drawstates()
    m.drawcountries()

    x, y = m(
        list(metar_table['longitude']),
        list(metar_table['latitude']))

    m.scatter(x,y, marker='o', color='red', s=3)
    plt.ion()
    plt.show()

def get_airport_info(identifier):
    logger = logging.getLogger(__name__)
    logger.info("Getting airport information for {}".format(identifier))
    info = {'station_id': identifier}
    try:
        airport = airnav.Airport(identifier)
    except:
        logger.error("Unable to query AirNav for {}".format(identifier))
        return None
    
    if airport.content.status_code != 200:
        logger.error("AirNav returned status {} for {}".format(airport.content.status_code, identifier))
        return None

    try:
        runways = airport.runways()
        info['num_runways'] = len(runways)
        lengths = [x['length'] for x in airport.runways()]
        try:
            info['avg_runway_len_ft'] = sum(lengths) / len(runways)
        except ZeroDivisionError:
            info['avg_runway_len_ft'] = None
        
        info['max_runway_len_ft'] = max(lengths)
        info['min_runway_len_ft'] = min(lengths)
        return info
    except:
        logger.exception("Unable to parse runway details for {}".format(identifier))
    
    return None

def get_airport_table(identifiers, cache=None):
    logger = logging.getLogger(__name__)
    if cache is not None and os.path.exists(cache):
        logger.info("Reading airport cache: {}".format(cache))
        airport_table = pd.read_pickle(cache)
    else:
        data = []
        for identifier in identifiers:
            info = get_airport_info(identifier)
            if info is not None:
                data.append(info)
            time.sleep(1)
        airport_table = pd.DataFrame(data)
        if cache is not None and len(airport_table) > 0:
            logger.info("Writing airport cache: {}".format(cache))
            airport_table.to_pickle(cache)
    return airport_table
        

metar_table = get_metars(cache='metars.pkl')
airport_table = get_airport_table(metar_table['station_id'], cache='airports.pkl')
