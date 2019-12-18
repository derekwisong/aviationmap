import pandas as pd
import avwx.tds as tds
import requests
import os
import logging
import airnav
import time
import faa
import threading
from queue import Queue

logging.basicConfig(level=logging.INFO)

class AirportDownloader(threading.Thread):
    def __init__(self, task_queue, result_queue):
        threading.Thread.__init__(self)
        self.task_queue = task_queue
        self.result_queue = result_queue
        self.stopped = threading.Event()
        self.session = requests.Session()

    def stop(self):
        self.stopped.set()

    def run(self):
        logger = logging.getLogger(__name__)
        while not self.stopped.wait(1.1):
            identifier = self.task_queue.get()
            
            try:
                if identifier is None:
                    break
                airport = faa.Airport(str(identifier))
                airport.query(session=self.session)
                runways = airport.runways()

                if runways is not None and len(runways) > 0:
                    logger.info("Found {} runways for {}".format(len(runways), identifier))
                    for runway in runways:
                        if runway is not None:
                            self.result_queue.put(runway)
                else:
                    logger.warning("No runways found for {}".format(identifier))
            except:
                logger.exception("Unable to process {}".format(identifier))
            finally:
                self.task_queue.task_done()


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
        airport = faa.Airport(identifier)
        airport.query()
    except:
        logger.error("Unable to query AirNav for {}".format(identifier))
        return None
    
    if airport.res.status_code != 200:
        logger.error("FAA returned status {} for {}".format(airport.res.status_code, identifier))
        return None

    try:
        info = airport.runways()
        return info
    except:
        logger.exception("Unable to parse runway details for {}".format(identifier))
    
    return None

def get_airport_table(identifiers, cache=None, num_threads=10):
    logger = logging.getLogger(__name__)
    if cache is not None and os.path.exists(cache):
        logger.info("Reading airport cache: {}".format(cache))
        airport_table = pd.read_pickle(cache)
    else:
        task_queue = Queue()
        result_queue = Queue()
        threads = []
        
        for identifier in identifiers:
            task_queue.put(identifier)
        
        for _ in range(num_threads):
            thread = AirportDownloader(task_queue, result_queue)
            thread.start()
            threads.append(thread)
            task_queue.put(None)

        logger.info("Waiting for threads to finish")
        task_queue.join()
        for thread in threads:
            thread.join()
        
        result_queue.put(None)
        runways = []
        while True:
            runway = result_queue.get()
            try:
                if runway is None: break
                else: runways.append(runway)
            finally:
                result_queue.task_done()
    
        airport_table = pd.DataFrame(runways)

        if cache is not None and len(airport_table) > 0:
            logger.info("Writing airport cache: {}".format(cache))
            airport_table.to_pickle(cache)
    return airport_table
        

metar_table = get_metars(cache='data/metars.pkl')
airport_table = get_airport_table(metar_table['station_id'][:20], cache='data/airports.pkl', num_threads=1)
