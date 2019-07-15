#!/usr/bin/env python

from bs4 import BeautifulSoup
import bs4

import requests
import re

dimensions_pattern = re.compile("([0-9]+) x ([0-9]+) ft.")

class Airport:
    def __init__(self, identifier):
        self.identifier = identifier
        self.url = "https://www.airnav.com/airport/{}".format(identifier)
        self.content = requests.get(self.url, timeout=30.0)
        self.soup = BeautifulSoup(self.content.text, 'html.parser')

    def runways(self):
        runway_info = self.soup.find('h3', string="Runway Information")
        #until getting to an H4 that doesn't start with "Runway", continue
        runways = []
        current_runway = {}
        
        for element in runway_info.next_siblings:
            if not isinstance(element, bs4.element.Tag):
                continue

            if element.name == 'h4':
                if element.text.startswith("Runway "):
                    current_runway = {'name':element.text}
                    runways.append(current_runway)
                else:
                    break
            elif element.name == 'table':
                for child in element.find_all('td'):
                    if not isinstance(child, bs4.element.Tag):
                        continue

                    if child.name == 'td' and child.text.startswith("Dimensions:"):
                        dimensions = child.find_next_sibling('td').text
                        match = dimensions_pattern.search(dimensions)
                        if match:
                            length = match.group(1)
                            width = match.group(2)
                            current_runway['length'] = length
                            current_runway['width'] = width
        return runways


if __name__ == '__main__':
    runways = Airport('KLGA').runways()
    print(runways)
