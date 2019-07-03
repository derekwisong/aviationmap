#!/usr/bin/env python

import threading
import logging

from . import data
from .led import StationLed


def linear_gradient(start_rgb, finish_rgb=(255, 255, 255), n=10):
  gradient = [start_rgb]

  for t in range(1, n):
    curr_vector = [
      int(start_rgb[j] + (float(t)/(n - 1)) * (finish_rgb[j] - start_rgb[j]))
      for j in range(3)
    ]
    gradient.append(curr_vector)

  return gradient

class CategoryColorPicker:
    category_colors = {'VFR': (0, 255, 0),
                       'MVFR': (0, 0, 255),
                       'IFR': (255, 0, 0),
                       'LIFR': (255, 0, 255)}

    def pick_color(self, station):
        category = station.get_metar_value('category')
        
        try:
            return self.category_colors[category]
        except KeyError:
            return (0, 0, 0)

class TemperatureColorPicker:
    def __init__(self, min_temp, max_temp, steps=10):
        self.min_temp = min_temp
        self.max_temp = max_temp
        self.gradient = linear_gradient((0, 0, 255), (255, 0, 0), n=steps)
        self.steps = steps

    def temp_to_color(self, temperature):
        temperature = min(temperature, self.max_temp)
        temperature = max(temperature, self.min_temp)
        width = (self.max_temp - self.min_temp) / (self.steps - 1)
        n = (temperature - self.min_temp) / width
        n = int(round(n))
        return self.gradient[n]

    def pick_color(self, station):
        temperature = station.get_metar_value('temp')
        return self.temp_to_color(temperature)

pickers = {'category': CategoryColorPicker(),
           'temp': TemperatureColorPicker(-10, 48, steps=30)}

class Station(threading.Thread):
    def __init__(self, code, name, led_number, metar_monitor, led_controller):
        threading.Thread.__init__(self)
        self.metar_monitor = metar_monitor

        self.led = StationLed(led_number, led_controller)
        self.code = code
        self.name = name
        self.number = led_number

        self.set_color_picker('category')

        self._stopped = threading.Event()

    def set_color_picker(self, picker_name):
        self.color_picker = pickers[picker_name]

    def set_color(self, r, g, b):
        if (r, g, b) != self.led.color:
            self.led.set_rgb(r, g, b)
    
    def get_metar_value(self, item):
        return self.metar_monitor.get_metar_value(self.code, item)

    def run(self):
        while not self._stopped.wait(1):
            color = self.color_picker.pick_color(self)
            self.set_color(*color)
    
    def stop(self):
        self._stopped.set()

class LedMap:
    def __init__(self, config):
        self.num_leds = config['leds']
        self.metar_monitor = data.MetarMonitor()
        self.stations = {}

        if config['controller'] == 'test':
            from .led import TestLEDController
            controller = TestLEDController(self.num_leds)   
        else:
            from .rpi import LEDController
            controller = LEDController(self.num_leds,
                                       config['rpi']['clock_pin'],
                                       config['rpi']['data_pin'])

        self.led_controller = controller

        for station in config['stations']:
            code = station['code']
            name = station['name']
            num = station['led']

            if code is None or num is None:
                continue

            self.metar_monitor.add_station(code)
            station = Station(code, name, num, self.metar_monitor, controller)
            station.start()
            self.stations[code] = station
        
        self.metar_monitor.start()


    def set_all_stations_color(self, r, g, b):
        for station in self.stations.values():
            station.set_color(r, g, b)
    
    def stop(self):
        self.metar_monitor.stop()

        for station in self.stations.values():
            station.stop()
