import requests
from bs4 import BeautifulSoup
import re
import pandas as pd

dimensions_re = re.compile(r"([0-9]+) +ft\.[ \n]+x ([0-9]+) ft.")

def condense_string(string):
    """Condense multiple spaces into one"""
    return ' '.join(string.split())

def coords_to_dec(degrees, minutes, seconds):
    """Convert gps coords to degrees"""
    return degrees + (minutes/60) + (seconds/3600)

class Airport:
    def __init__(self, identifier, session=None):
        self.identifier = identifier
        self.session = session
        self.res = None
        self.soup = None
    
    def url(self):
        return 'https://nfdc.faa.gov/nfdcApps/services/ajv5/airportDisplay.jsp?airportId={}'.format(self.identifier)

    def query(self, session=None):
        if self.session is None:
            res = requests.get(self.url())
        else:
            res = session.get(self.url())

        self.res = res
        self.soup = BeautifulSoup(res.text, 'html.parser')

    def normalize_coords(self, coordinates):
        # coordinates = '32-39-23.666 N / 114-36-21.554 W'
        regex = re.compile('([0-9]+)-([0-9]+)-([0-9\.]+) +([NS]) +/ +([0-9]+)-([0-9]+)-([0-9\.]+) +([EW])')
        m = regex.match(coordinates)
        lat = coords_to_dec(float(m.group(1)), float(m.group(2)), float(m.group(3)))
        lat_sign = m.group(4)
        lon = coords_to_dec(float(m.group(5)), float(m.group(6)), float(m.group(7)))
        lon_sign = m.group(8)
        if lat_sign == 'S': lat *= -1
        if lon_sign == 'W': lon *= -1

        return (lat, lon)

    def summary(self):
        summary = self.soup.find('div', {'id': 'summary'})
        details = {}

        for row in summary.find_all('tr'):
            if not row: continue
            cells = row.find_all('td')
            if not cells: continue
            field = condense_string(cells[0].text)
            val = condense_string(cells[1].text)
            details[field] = val

        details['coords'] = self.normalize_coords(details['Latitude/Longitude'])
        return details


    def runways(self, to_df=False):
        id_filter = lambda x:x and x.startswith("runway_")
        data = []
        for runway_element in self.soup.find_all('div', id=id_filter):
            name = runway_element.find('div', {'class':'well'}).text.split()[-1]
            details = {'station_id': self.identifier, 'runway': name}
            summary_element = runway_element.find('table')
            for row in summary_element.find_all('tr'):
                cells = row.find_all('td')
                label = cells[0].text.strip()
                val = cells[1].text.strip()
                if label == 'Dimensions':
                    match = dimensions_re.search(val)
                    if match:
                        length = int(match.group(1))
                        width = int(match.group(2))
                        details['length'] = length
                        details['width'] = width
                else:
                    details[label] = val
            data.append(details)
        
        if to_df:
            data = pd.DataFrame(data)
        return data

if __name__ == '__main__':
    a = Airport("KHPN")
    a.query()
    print(a.runways(to_df=True))