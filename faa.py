import requests
from bs4 import BeautifulSoup
import re
import pandas as pd

dimensions_re = re.compile("([0-9]+) +ft\.[ \n]+x ([0-9]+) ft.")

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